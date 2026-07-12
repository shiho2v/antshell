#!/usr/bin/env python3
"""Evidence Pack 생성 — 모듈이 읽는 **유일한** 근거 단위.

모듈 분석 단계에서 Claude 는 원시 API 응답이나 전체 재무제표를 읽지 않는다.
필요한 모듈의 evidence item 만 읽는다 (Phase 2: progressive disclosure).

모든 evidence 는 evidence-item.schema.json 을 만족해야 하며,
출처·기준일·단위·수집경로를 반드시 갖는다. DART 수치에는 rcept_no 가 붙는다.

모듈당 evidence 는 기본 20개 이내로 제한한다 (Phase 12).

사용법:
    python build_evidence_packs.py 009150

출력:
    data/evidence/{ticker}_evidence.json
"""
from __future__ import annotations

import argparse
from collections import defaultdict

from _common import (
    DART_VIEWER,
    SkillError,
    die,
    evidence_path,
    load_registry,
    log,
    metrics_path,
    normalized_path,
    now_iso,
    raw_path,
    read_json,
    validate_schema,
    validate_ticker,
    write_json,
)

MAX_EVIDENCE_PER_MODULE = 20

# 시세 계열(가격·거래량·지수·수급)에서 유래한 지표.
# 이들의 원천은 pykrx → KRX/Naver 이며 **비공식 경로**다. 반드시 그렇게 표기한다.
# 그 외 지표는 DART 공시 계보이며, 접수번호 또는 입력 evidence 체인으로 추적된다.
MARKET_ORIGIN_METRICS = {
    "close_price",
    "high_52w",
    "pct_from_52w_high",
    "volume_ratio_vs_60d",
    "rs_vs_index_6m_pp",
    "index_vs_ma200_pct",
    "inst_foreign_net_60d_to_mktcap",
}

# metric → 이 지표를 쓰는 모듈. registry 에서 자동 유도하되,
# hint_metrics(정성 모듈의 참고 지표)도 포함한다.
PREFIX = {
    "business": "B", "quality": "Q", "growth": "G", "moat": "MO",
    "valuation": "V", "trend": "T", "risk": "R", "catalyst": "C",
    "shared": "S",
}


def metric_module_map(registry: dict) -> dict[str, list[str]]:
    """metric 키 → 그 지표가 필요한 모듈 목록."""
    mapping: dict[str, list[str]] = defaultdict(list)
    for mod, spec in registry["modules"].items():
        for c in spec["criteria"]:
            if c.get("metric"):
                mapping[c["metric"]].append(mod)
            for h in c.get("hint_metrics", []) or []:
                mapping[h].append(mod)
    return {k: sorted(set(v)) for k, v in mapping.items()}


def slug(metric: str) -> str:
    return metric.upper().replace("_", "")[:10]


def build_metric_evidence(
    ticker: str, metrics: dict, mmap: dict[str, list[str]], fs_div: str
) -> list[dict]:
    """지표 → evidence item. 파생값이므로 source_type=derived_calculation."""
    items: list[dict] = []
    counters: dict[str, int] = defaultdict(int)

    for name, m in metrics["metrics"].items():
        mods = mmap.get(name, ["shared"])
        primary = mods[0]
        counters[primary] += 1
        eid = f"{PREFIX.get(primary, 'S')}-{slug(name)}-{counters[primary]:03d}"

        # 출처 판정 — 지표의 실제 계보를 정직하게 표기한다.
        # 시세 계열에서 유래한 지표는 **pykrx(비공식 래퍼)** 로 표기해야 한다.
        # 이를 'internal' 로 뭉뚱그리면 비공식 출처가 숨겨진다.
        # 나머지는 DART 계보이며, 접수번호가 직접 없더라도 입력 evidence 체인을 통해
        # 상위 공시로 추적된다 (예: growth_acceleration_pp → rev_yoy_q → 분기보고서).
        rcepts = m.get("rcept_nos") or []
        url = DART_VIEWER.format(rcept_no=rcepts[0]) if rcepts else None
        has_formula = bool(m.get("formula"))
        is_market = name in MARKET_ORIGIN_METRICS

        if is_market:
            provider = "pykrx"
            underlying = "KRX / Naver Finance (pykrx 경유, 비공식)"
            endpoint = "calculate_metrics.py" if has_formula else "get_market_ohlcv"
            stype = "derived_calculation" if has_formula else "unofficial_wrapper"
        else:
            provider = "dart"
            underlying = None
            endpoint = "calculate_metrics.py" if has_formula else "fnlttSinglAcntAll.json"
            stype = "derived_calculation" if has_formula else "official_api"

        limits = list(m.get("limitations") or [])
        if m.get("na_reason"):
            limits.append(f"N/A 사유: {m['na_reason']}")
        if m.get("period_type") in ("ttm", "quarter_standalone", "annual"):
            limits.append(f"재무 기준: {fs_div}")

        items.append({
            "evidence_id": eid,
            "module": primary if primary in PREFIX else "shared",
            "evidence_type": "metric",
            "metric": name,
            "label": name,
            "value": m["value"],
            "unit": m["unit"],
            "period_start": None,
            "period_end": None,
            "period_type": m.get("period_type"),
            "fs_div": fs_div if m.get("period_type") in
                      ("ttm", "quarter_standalone", "quarter_cumulative", "annual") else None,
            "source": {
                "provider": provider,
                "source_type": stype,
                "underlying_source": underlying,
                "rcept_no": rcepts[0] if rcepts else None,
                "url_or_identifier": url,
                "endpoint_or_function": endpoint,
                "retrieved_at": metrics["calculated_at"],
            },
            "calculation": {
                "formula": m["formula"],
                "inputs": m.get("inputs") or {},
                "input_evidence_ids": [],   # link_calculation_inputs 가 채운다
            } if has_formula else None,
            "text": None,
            "verification": "pending",
            "confidence": None if m["value"] is None else 0.9,
            "limitations": limits,
            # 스키마 외 필드 — 검증 전에 제거한다
            "_shared_with": mods,
            "_period_label": m.get("period"),
        })

    return items


def link_calculation_inputs(items: list[dict]) -> None:
    """파생값의 input_evidence_ids 를 실제 evidence 로 연결한다 (근거 체인).

    예: operating_margin_ttm 의 입력은 operating_income_ttm 과 revenue_ttm 이며,
    이 둘도 evidence item 으로 존재한다 → 두 ID 를 연결한다.

    입력이 원시 공시 행인 기초 지표(revenue_ttm 등)는 연결할 evidence 가 없다.
    이 경우 input_evidence_ids 는 비고, **출처는 rcept_no 로 추적**한다
    (validate_evidence.py 가 둘 중 하나는 반드시 있도록 강제한다).
    """
    by_metric = {
        it["metric"]: it["evidence_id"]
        for it in items
        if it.get("evidence_type") == "metric" and it.get("metric")
    }
    for it in items:
        calc = it.get("calculation")
        if not calc:
            continue
        calc["input_evidence_ids"] = [
            by_metric[k] for k in (calc.get("inputs") or {})
            if k in by_metric and by_metric[k] != it["evidence_id"]
        ]


def build_event_evidence(ticker: str, events: dict) -> list[dict]:
    """공시 → catalyst/risk 근거. **공시 근거 없는 촉매는 만들 수 없다.**"""
    items: list[dict] = []
    for i, e in enumerate(events.get("catalyst_candidates", [])[:MAX_EVIDENCE_PER_MODULE], 1):
        rd = e.get("rcept_dt") or ""
        iso = f"{rd[:4]}-{rd[4:6]}-{rd[6:8]}" if len(rd) == 8 else None
        items.append({
            "evidence_id": f"C-EVENT-{i:03d}",
            "module": "catalyst",
            "evidence_type": "event",
            "metric": None,
            "label": e["report_nm"],
            "value": None,
            "unit": None,
            "period_start": iso,
            "period_end": iso,
            "period_type": "point_in_time",
            "fs_div": None,
            "source": {
                "provider": "dart",
                "source_type": "official_api",
                "underlying_source": None,
                "rcept_no": e["rcept_no"],
                "url_or_identifier": e["url"],
                "endpoint_or_function": "list.json",
                "retrieved_at": events["source"]["retrieved_at"],
            },
            "calculation": None,
            "text": f"[{'/'.join(e['tags'])}] {e['report_nm']} (접수 {rd}, 제출인 {e.get('flr_nm')})",
            "verification": "pending",
            "confidence": 1.0,
            "limitations": ["제목 키워드 기반 후보 분류다. 촉매 확정이 아니며 원문 확인이 필요하다."],
            "_shared_with": ["catalyst", "risk"],
            "_period_label": iso,
        })
    return items


def build_profile_evidence(ticker: str, profile: dict) -> list[dict]:
    """기업개황 + 사업보고서 원문 → business/moat 정성 근거."""
    items: list[dict] = []
    comp = profile["company"]
    src = profile["source"]

    items.append({
        "evidence_id": "B-PROFILE-001",
        "module": "business",
        "evidence_type": "statement",
        "metric": None,
        "label": "기업개황",
        "value": None,
        "unit": None,
        "period_start": None, "period_end": None,
        "period_type": "point_in_time",
        "fs_div": None,
        "source": {
            "provider": "dart", "source_type": "official_api",
            "underlying_source": None, "rcept_no": None,
            "url_or_identifier": comp.get("hm_url"),
            "endpoint_or_function": "company.json",
            "retrieved_at": src["retrieved_at"],
        },
        "calculation": None,
        "text": (
            f"법인명: {comp.get('corp_name')} / 업종코드: {comp.get('induty_code')} / "
            f"설립일: {comp.get('est_dt')} / 결산월: {comp.get('acc_mt')}월 / "
            f"대표자: {comp.get('ceo_nm')}"
        ),
        "verification": "pending",
        "confidence": 1.0,
        "limitations": ["업종코드는 표준산업분류이며 사업부문 구성을 설명하지 않는다."],
        "_shared_with": ["business"],
        "_period_label": None,
    })

    sec = profile.get("business_section")
    if sec:
        items.append({
            "evidence_id": "B-FILING-001",
            "module": "business",
            "evidence_type": "filing_text",
            "metric": None,
            "label": "사업보고서 「II. 사업의 내용」 원문",
            "value": None,
            "unit": None,
            "period_start": None, "period_end": None,
            "period_type": "point_in_time",
            "fs_div": None,
            "source": {
                "provider": "dart",
                "source_type": "official_filing",
                "underlying_source": None,
                "rcept_no": sec["rcept_no"],
                "url_or_identifier": DART_VIEWER.format(rcept_no=sec["rcept_no"]),
                "endpoint_or_function": "document.xml",
                "retrieved_at": src["retrieved_at"],
            },
            "calculation": None,
            "text": (
                f"원문 텍스트 파일: {sec['text_path']} ({sec['chars']:,}자"
                f"{', 절단됨' if sec.get('truncated') else ''}). "
                f"사업부문·생산능력·가동률·원재료·수주잔고는 구조화 API 가 없어 "
                f"이 원문에서만 확인 가능하다. **수치를 자동 추출하지 않았다** — "
                f"인용 시 원문 문구에 근거해야 한다."
            ),
            "verification": "pending",
            "confidence": 0.8,
            "limitations": [
                "원문을 태그 제거 후 텍스트로 변환했다. 표 구조가 손실될 수 있다.",
                "자동 수치 추출을 하지 않았다. Claude 가 읽고 인용해야 한다.",
            ],
            "_shared_with": ["business", "moat", "risk"],
            "_period_label": sec.get("rcept_dt"),
        })

    shares = profile["shares"]
    items.append({
        "evidence_id": "S-SHARES-001",
        "module": "shared",
        "evidence_type": "metric",
        "metric": "issued_shares",
        "label": "발행주식총수",
        "value": shares["issued_shares"],
        "unit": "주",
        "period_start": None, "period_end": None,
        "period_type": "point_in_time",
        "fs_div": None,
        "source": {
            "provider": "dart", "source_type": "official_api",
            "underlying_source": None,
            "rcept_no": shares.get("rcept_no"),
            "url_or_identifier": (
                DART_VIEWER.format(rcept_no=shares["rcept_no"])
                if shares.get("rcept_no") else None
            ),
            "endpoint_or_function": "stockTotqySttus.json",
            "retrieved_at": src["retrieved_at"],
        },
        "calculation": None,
        "text": None,
        "verification": "pending",
        "confidence": 1.0,
        "limitations": [f"{shares['bsns_year']} 사업보고서 기준 — 기중 변동은 반영되지 않는다."],
        "_shared_with": ["valuation", "quality"],
        "_period_label": f"{shares['bsns_year']} 사업보고서",
    })
    return items


def main() -> None:
    ap = argparse.ArgumentParser(description="Evidence Pack 생성")
    ap.add_argument("ticker")
    args = ap.parse_args()

    try:
        ticker = validate_ticker(args.ticker)
        registry = load_registry()
        metrics = read_json(metrics_path(ticker))
        nz = read_json(normalized_path(ticker))
        profile = read_json(raw_path(ticker, "dart_profile"))
        events = read_json(raw_path(ticker, "dart_events"))

        mmap = metric_module_map(registry)
        items = (
            build_metric_evidence(ticker, metrics, mmap, nz["fs_div"])
            + build_profile_evidence(ticker, profile)
            + build_event_evidence(ticker, events)
        )
        link_calculation_inputs(items)

        # 모듈별 evidence pack (Phase 12: 모듈당 20개 이내)
        packs: dict[str, list[str]] = defaultdict(list)
        for it in items:
            for mod in it["_shared_with"]:
                if len(packs[mod]) < MAX_EVIDENCE_PER_MODULE:
                    packs[mod].append(it["evidence_id"])

        # 스키마 검증 전에 내부 필드 제거
        clean = []
        for it in items:
            c = {k: v for k, v in it.items() if not k.startswith("_")}
            errs = validate_schema(c, "evidence-item.schema.json")
            if errs:
                raise SkillError(
                    f"evidence {it['evidence_id']} 가 스키마를 위반했습니다:\n  - "
                    + "\n  - ".join(errs)
                )
            clean.append(c)

        result = {
            "ticker": ticker,
            "generated_at": now_iso(),
            "evidence": clean,
            "packs": {k: v for k, v in sorted(packs.items())},
            "counts": {
                "total": len(clean),
                "with_value": sum(1 for c in clean if c["value"] is not None),
                "na": sum(1 for c in clean if c["value"] is None
                          and c["evidence_type"] == "metric"),
            },
        }

        out = write_json(evidence_path(ticker), result)
        print(f"저장: {out}")
        print(f"  evidence {len(clean)}개 (수치 보유 {result['counts']['with_value']}개)")
        for mod, ids in result["packs"].items():
            print(f"  {mod}: {len(ids)}개")

    except SkillError as e:
        die(str(e))


if __name__ == "__main__":
    main()
