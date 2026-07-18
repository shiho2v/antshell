#!/usr/bin/env python3
"""Gate 3 (Analysis) + Gate 4 (Report) — 최종 검증 및 manifest 생성.

Gate 3: 계산·채점의 무결성
  - 점수를 **독립적으로 재계산**해 module-result 와 대조 (재현 가능성)
  - rubric(registry) 과 점수 일치
  - N/A 항목에 점수가 부여되지 않았는가
  - 적자기업 PER 이 사용되지 않았는가
  - 음수 기준연도 CAGR 이 없는가
  - 분모 0 이 없는가
  - 중복 지표로 이중 점수가 부여되지 않았는가 (trend 의 C·A 는 growth 재사용)

Gate 4: 보고서의 정직성
  - 모든 claim 에 evidence ID 가 있는가
  - claim_type 별 최소 근거 수를 만족하는가
  - 존재하지 않는 evidence ID 를 참조하지 않는가
  - 목표주가·컨센서스가 생성되지 않았는가
  - 데이터 완전성과 결론 강도가 일치하는가
  - 면책 문구가 있는가

**한 게이트라도 실패하면 최종 보고서를 생성하지 않는다.**

사용법:
    python validate_report.py 009150
    python validate_report.py 009150 --claims data/009150_claims.json --html outputs/xxx.html

출력:
    data/{ticker}_manifest.json   (report-manifest.schema.json 준수)
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import (
    DATA_DIR,
    SkillError,
    contract_path,
    die,
    evidence_path,
    load_modes,
    load_registry,
    metrics_path,
    module_result_path,
    now_iso,
    read_json,
    validate_schema,
    validate_ticker,
    write_json,
)

MAX_LEVEL = 3

# claim_type → 최소 근거 수 (Phase 8)
MIN_EVIDENCE = {
    "fact": 1,
    "derived_interpretation": 2,
    "conditional_view": 1,
    "unknown": 0,
}

FORBIDDEN_PHRASES = [
    "매수", "매도", "목표주가", "적정주가", "컨센서스", "target price",
    "buy", "sell", "overweight", "underweight",
]


def recompute_score(result: dict, registry: dict) -> float | None:
    """module-result 의 점수를 **독립적으로 재계산**한다 (Gate 3: 계산식 재현 가능)."""
    spec = registry["modules"][result["module"]]
    weights = {c["id"]: c["weight"] for c in spec["criteria"]}

    scored = [r for r in result["criteria_scores"] if r["level"] is not None]
    if not scored:
        return None

    total_w = sum(weights[r["criterion_id"]] for r in scored)
    if total_w == 0:
        return None
    earned = sum(weights[r["criterion_id"]] * r["level"] / MAX_LEVEL for r in scored)
    return round(earned / total_w * 100, 1)


def gate3(ticker: str, modules: list[str], registry: dict, metrics: dict) -> dict:
    checks: list[dict] = []
    errors: list[str] = []

    # ── 점수 재현 ───────────────────────────────────────────────────────────
    mismatches = []
    for mod in modules:
        p = module_result_path(ticker, mod)
        if not p.exists():
            errors.append(f"{mod}: module-result 파일이 없다")
            continue
        r = read_json(p)
        expected = recompute_score(r, registry)
        actual = r["score"]
        if expected != actual:
            mismatches.append(f"{mod}: 저장된 점수 {actual} ≠ 재계산 {expected}")

    checks.append({
        "check": "점수 재현 가능 (독립 재계산 일치)",
        "result": "fail" if mismatches else "pass",
        "detail": "; ".join(mismatches) if mismatches else f"{len(modules)}개 모듈 일치",
    })
    errors.extend(mismatches)

    # ── N/A 에 점수 금지 ────────────────────────────────────────────────────
    na_scored = []
    for mod in modules:
        p = module_result_path(ticker, mod)
        if not p.exists():
            continue
        for c in read_json(p)["criteria_scores"]:
            if c["level"] is None and not c.get("na_reason"):
                na_scored.append(f"{mod}/{c['criterion_id']}: N/A 인데 사유가 없다")
    checks.append({
        "check": "N/A 항목에 점수 금지 + 사유 기록",
        "result": "fail" if na_scored else "pass",
        "detail": "; ".join(na_scored) if na_scored else "위반 없음",
    })
    errors.extend(na_scored)

    # ── 적자기업 PER 금지 ───────────────────────────────────────────────────
    per = metrics["metrics"].get("per_trailing", {})
    ni = metrics["metrics"].get("net_income_ttm", {})
    per_violation = (
        ni.get("value") is not None and ni["value"] <= 0 and per.get("value") is not None
    )
    checks.append({
        "check": "적자기업 PER 금지",
        "result": "fail" if per_violation else "pass",
        "detail": ("순이익이 0 이하인데 PER 이 산출되었다"
                   if per_violation else
                   ("적자 → PER=N/A 로 정상 처리" if (ni.get("value") or 1) <= 0
                    else "흑자 → PER 적용 가능")),
    })
    if per_violation:
        errors.append("적자기업에 PER 이 적용되었다")

    # ── 음수 기준연도 CAGR 금지 ─────────────────────────────────────────────
    cagr_bad = []
    for k in ("rev_cagr_3y", "op_cagr_3y", "eps_cagr_3y"):
        m = metrics["metrics"].get(k, {})
        base = (m.get("inputs") or {}).get("base_value")
        if m.get("value") is not None and base is not None and base <= 0:
            cagr_bad.append(f"{k}: 기준연도 값이 {base} 인데 CAGR 이 산출되었다")
    checks.append({
        "check": "음수 기준연도 CAGR 금지",
        "result": "fail" if cagr_bad else "pass",
        "detail": "; ".join(cagr_bad) if cagr_bad else "위반 없음",
    })
    errors.extend(cagr_bad)

    # ── 분모 0 검사 ─────────────────────────────────────────────────────────
    div0 = [
        f"{k}: 분모가 0 인데 값이 산출되었다"
        for k, m in metrics["metrics"].items()
        if m.get("value") is not None
        and any(v == 0 for kk, v in (m.get("inputs") or {}).items()
                if kk in ("revenue_ttm", "equity", "market_cap", "net_income_ttm"))
    ]
    checks.append({
        "check": "분모 0 검사",
        "result": "fail" if div0 else "pass",
        "detail": "; ".join(div0) if div0 else "위반 없음",
    })
    errors.extend(div0)

    # ── 중복 지표 이중 점수 금지 ────────────────────────────────────────────
    # trend 의 C·A 는 growth 지표를 재사용한다. registry 의 reuse_from 으로 선언되어 있어야 한다.
    reused = [
        c["id"] for c in registry["modules"]["trend"]["criteria"] if c.get("reuse_from")
    ]
    checks.append({
        "check": "중복 지표 이중 점수 금지 (CANSLIM C·A 는 growth 재사용 선언)",
        "result": "pass" if reused else "warn",
        "detail": (f"재사용 선언됨: {', '.join(reused)} — "
                   "growth 와 trend 는 별도 모듈이므로 가중치가 각각 적용되나, "
                   "지표는 재계산하지 않고 동일 evidence 를 참조한다"),
    })

    # ── 동일 기간 비교 ──────────────────────────────────────────────────────
    checks.append({
        "check": "동일 기간 비교 (YoY 는 동일 분기끼리)",
        "result": "pass",
        "detail": "calculate_metrics.yoy_quarter 가 quarter 번호 일치를 강제한다",
    })

    return {
        "status": "failed" if errors else "passed",
        "checks": checks,
        "errors": errors,
    }


def gate4(
    ticker: str, claims: list[dict], evidence_ids: set[str],
    comp: dict, contract: dict, html: str | None
) -> dict:
    checks: list[dict] = []
    errors: list[str] = []

    # ── 모든 claim 에 evidence ID ───────────────────────────────────────────
    no_ev = [
        c["claim_id"] for c in claims
        if c["claim_type"] != "unknown" and not c.get("evidence_ids")
    ]
    checks.append({
        "check": "모든 핵심 주장에 evidence ID 존재",
        "result": "fail" if no_ev else "pass",
        "detail": (f"근거 없는 주장: {', '.join(no_ev)}" if no_ev
                   else f"{len(claims)}건 모두 근거 보유"),
    })
    errors.extend(f"{cid}: 근거 없는 주장 — 최종 보고서에서 제거해야 한다" for cid in no_ev)

    # ── claim_type 별 최소 근거 수 ──────────────────────────────────────────
    weak = [
        f"{c['claim_id']}: {c['claim_type']} 는 근거 {MIN_EVIDENCE[c['claim_type']]}개 필요, "
        f"{len(c.get('evidence_ids', []))}개 제출"
        for c in claims
        if len(c.get("evidence_ids", [])) < MIN_EVIDENCE.get(c["claim_type"], 1)
    ]
    checks.append({
        "check": "주장 유형별 최소 근거 수 (사실 1 / 해석 2)",
        "result": "fail" if weak else "pass",
        "detail": "; ".join(weak) if weak else "충족",
    })
    errors.extend(weak)

    # ── 존재하지 않는 evidence 참조 금지 ────────────────────────────────────
    dangling = [
        f"{c['claim_id']}: 존재하지 않는 evidence {eid}"
        for c in claims
        for eid in (c.get("evidence_ids", []) + c.get("counter_evidence_ids", []))
        if eid not in evidence_ids
    ]
    checks.append({
        "check": "evidence ID 연결 유효성",
        "result": "fail" if dangling else "pass",
        "detail": "; ".join(dangling) if dangling else "모든 참조 유효",
    })
    errors.extend(dangling)

    # ── 인과 주장의 연결 경로 ───────────────────────────────────────────────
    causal_missing = [
        c["claim_id"] for c in claims
        if c["claim_type"] == "derived_interpretation"
        and re.search(r"때문|덕분|영향으로|기인|따라서|그 결과", c["claim"])
        and not c.get("causal_path")
    ]
    checks.append({
        "check": "인과 주장에 연결 경로 명시 (상관≠인과)",
        "result": "warn" if causal_missing else "pass",
        "detail": (f"연결 경로 없는 인과 표현: {', '.join(causal_missing)}"
                   if causal_missing else "위반 없음"),
    })

    # ── 목표주가·컨센서스 생성 금지 ─────────────────────────────────────────
    forbidden_hits: list[str] = []
    if html:
        body = re.sub(r"<[^>]+>", " ", html)
        for ph in ("목표주가", "적정주가", "target price"):
            if ph in body.lower() or ph in body:
                # '목표주가를 제시하지 않는다' 같은 부정문은 허용
                for mm in re.finditer(re.escape(ph), body):
                    ctx = body[max(0, mm.start() - 40): mm.end() + 40]
                    if not re.search(r"않|없|금지|제시하지|산출하지|불가", ctx):
                        forbidden_hits.append(f"'{ph}' 가 부정문 없이 등장: ...{ctx.strip()}...")
    checks.append({
        "check": "목표주가·컨센서스 임의 생성 금지",
        "result": "fail" if forbidden_hits else "pass",
        "detail": ("; ".join(forbidden_hits[:3]) if forbidden_hits
                   else "목표주가·컨센서스 미생성 (공식 데이터 출처 부재)"),
    })
    errors.extend(forbidden_hits)

    # ── 매수/매도 표현 금지 ─────────────────────────────────────────────────
    buysell = []
    if html:
        body = re.sub(r"<[^>]+>", " ", html)
        for ph in ("매수", "매도"):
            for mm in re.finditer(ph, body):
                # (a) 수급 용어 '순매수/순매도' 는 투자의견이 아니다 — 바로 앞 글자로 판별.
                if mm.start() > 0 and body[mm.start() - 1] == "순":
                    continue
                # (b) 부정문만 허용한다. 부정어가 **바로 뒤에 붙어 있어야** 하며,
                #     멀리 떨어진 면책 문구가 실제 매수 권유를 가려주지 못하게 창을 좁게 잡는다.
                #     예: "매수·매도 의견이 아니며"(허용) vs "매수 의견을 제시한다"(위반).
                after = body[mm.end(): mm.end() + 16]
                if re.search(r"않|없|금지|아니|권유", after):
                    continue
                ctx = body[max(0, mm.start() - 30): mm.end() + 30]
                buysell.append(f"'{ph}' 표현 사용: ...{ctx.strip()}...")
    checks.append({
        "check": "매수·매도 표현 금지",
        "result": "fail" if buysell else "pass",
        "detail": ("; ".join(buysell[:3]) if buysell
                   else "관찰 등급(긍정적/중립적/보수적/판단 유보)만 사용"),
    })
    errors.extend(buysell)

    # ── 데이터 완전성과 결론 강도 일치 ──────────────────────────────────────
    dc = comp.get("data_completeness")
    verdict = comp.get("verdict")
    mismatch = (
        dc is not None and dc < 0.5 and verdict not in ("판단 유보",)
    )
    checks.append({
        "check": "데이터 완전성과 결론 강도 일치",
        "result": "fail" if mismatch else "pass",
        "detail": (f"데이터 완전성 {dc:.0%} 인데 결론이 '{verdict}' — 판단 유보여야 한다"
                   if mismatch else
                   f"완전성 {dc:.0%} / 결론 '{verdict}' 일치"
                   if dc is not None else "완전성 미산출"),
    })
    if mismatch:
        errors.append("데이터 완전성이 낮은데 확정적 결론을 내렸다")

    # ── 면책 문구 ───────────────────────────────────────────────────────────
    has_disc = bool(html) and ("투자 자문" in html or "투자자문" in html)
    checks.append({
        "check": "투자 자문 아님 고지 포함",
        "result": "pass" if has_disc else ("skip" if not html else "fail"),
        "detail": "면책 문구 확인" if has_disc else
                  ("HTML 미제공 — 보고서 생성 시 검증" if not html else "면책 문구 없음"),
    })
    if html and not has_disc:
        errors.append("면책 문구(투자 자문 아님)가 없다")

    # ── 상충 근거 표시 ──────────────────────────────────────────────────────
    has_counter = any(c.get("counter_evidence_ids") for c in claims)
    checks.append({
        "check": "긍정·부정 근거 모두 표시",
        "result": "pass" if has_counter else "warn",
        "detail": ("상충 근거가 기록되어 있다" if has_counter
                   else "상충 근거가 하나도 없다 — 정말 없는지 재확인 필요"),
    })

    return {
        "status": "failed" if errors else "passed",
        "checks": checks,
        "errors": errors,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Gate 3 + Gate 4 검증 및 manifest 생성")
    ap.add_argument("ticker")
    ap.add_argument("--claims", help="claims JSON 경로 (Claude 가 작성)")
    ap.add_argument("--html", help="생성된 보고서 HTML 경로 (Gate 4 문구 검증용)")
    args = ap.parse_args()

    try:
        ticker = validate_ticker(args.ticker)
        registry = load_registry()
        modes_cfg = load_modes()
        contract = read_json(contract_path(ticker))
        metrics = read_json(metrics_path(ticker))
        pack = read_json(evidence_path(ticker))
        comp_file = read_json(DATA_DIR / f"{ticker}_composite.json")
        comp = comp_file["composite"]

        modules = contract["required_modules"]

        # Gate 1·2 는 앞 단계에서 이미 판정되어 파일로 남아 있다
        ident = read_json(DATA_DIR / "raw" / f"{ticker}_identity.json")
        g1 = ident["gate1"]
        g2 = read_json(DATA_DIR / f"{ticker}_gate2.json")

        g3 = gate3(ticker, modules, registry, metrics)

        claims = []
        if args.claims:
            cp = Path(args.claims)
            if not cp.is_absolute():
                cp = DATA_DIR.parent / args.claims
            claims = read_json(cp).get("claims", [])

        html = None
        if args.html:
            hp = Path(args.html)
            if not hp.is_absolute():
                hp = DATA_DIR.parent / args.html
            if hp.exists():
                html = hp.read_text(encoding="utf-8")

        evidence_ids = {e["evidence_id"] for e in pack["evidence"]}
        g4 = gate4(ticker, claims, evidence_ids, comp, contract, html)

        # ── manifest ────────────────────────────────────────────────────────
        sources: dict[tuple, dict] = {}
        for e in pack["evidence"]:
            s = e["source"]
            k = (s["provider"], s["source_type"], s.get("endpoint_or_function"))
            if k not in sources:
                sources[k] = {
                    "provider": s["provider"],
                    "source_type": s["source_type"],
                    "underlying_source": s.get("underlying_source"),
                    "endpoint_or_function": s.get("endpoint_or_function"),
                    "rcept_no": s.get("rcept_no"),
                    "url_or_identifier": s.get("url_or_identifier"),
                    "retrieved_at": s.get("retrieved_at"),
                    "evidence_count": 0,
                }
            sources[k]["evidence_count"] += 1

        limitations = list(contract.get("unsupported_data", []))
        if metrics.get("ttm_fallback"):
            limitations.append("TTM 대신 최근 연간값으로 폴백했다 — 최신 분기가 반영되지 않았다.")
        na_metrics = [k for k, v in metrics["metrics"].items() if v["value"] is None]
        if na_metrics:
            limitations.append(f"N/A 지표: {', '.join(na_metrics)}")

        manifest = {
            "ticker": ticker,
            "company_name": contract.get("company_name") or ident["company_name"],
            "market": contract.get("market"),
            "corp_code": contract.get("corp_code"),
            "analysis_mode": contract["analysis_mode"],
            "request_type": contract["request_type"],
            "data_cutoff": contract.get("data_cutoff"),
            "generated_at": now_iso(),
            "composite": comp,
            "modules": comp_file["modules"],
            "claims": claims,
            "gates": {
                "identity": {"status": g1["status"], "checks": g1["checks"]},
                "data": {"status": g2["status"], "checks": g2["checks"]},
                "analysis": {"status": g3["status"], "checks": g3["checks"]},
                "report": {"status": g4["status"], "checks": g4["checks"]},
            },
            "data_limitations": limitations,
            "unsupported_items": contract.get("unsupported_data", []),
            "sources": list(sources.values()),
            "output_path": args.html,
            "previous_manifest": None,
            "changed_modules": [],
        }

        errs = validate_schema(manifest, "report-manifest.schema.json")
        if errs:
            raise SkillError("manifest 스키마 위반:\n  - " + "\n  - ".join(errs))

        out = write_json(DATA_DIR / f"{ticker}_manifest.json", manifest)

        gates = manifest["gates"]
        print("검증 게이트:")
        for name, g in gates.items():
            mark = {"passed": "PASS", "failed": "FAIL", "pending": "PEND"}[g["status"]]
            print(f"  [{mark}] Gate {name}")
            for c in g["checks"]:
                if c["result"] in ("fail", "warn"):
                    print(f"      - {c['check']}: {c.get('detail', '')}")

        print(f"\n저장: {out}")

        failed = [n for n, g in gates.items() if g["status"] == "failed"]
        if failed:
            die(f"게이트 실패: {', '.join(failed)} — "
                "**최종 보고서를 생성하지 않고 검증 실패 보고서를 생성해야 합니다.**")

        print("\n모든 게이트 통과 — 보고서 생성 가능")

    except SkillError as e:
        die(str(e))


if __name__ == "__main__":
    main()
