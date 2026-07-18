#!/usr/bin/env python3
"""채점 — **모든 점수 산술의 단일 지점** (Gate 3).

LLM 은 점수를 계산하지 않는다.
  - auto   criterion: metrics.json 값 + registry 의 bands 로 Python 이 자동 채점
  - judged criterion: Claude 가 서수 등급(0~3)과 evidence_id 만 제출한 judgment 파일을 읽어
                      Python 이 가중 환산한다. **Claude 는 산술하지 않는다.**

핵심 규칙:
  - N/A criterion 은 분자·분모 모두에서 제외한다. **0점을 주지 않는다.**
  - 데이터 부족은 낮은 점수가 아니라 낮은 confidence / evidence_coverage 로 표현한다.
  - 채점 가능한 criterion 이 하나도 없으면 score=null, status=insufficient_data.
  - 종합점수는 실행된 모듈의 가중치를 재정규화(합 100)해 계산한다.

사용법:
    python score_modules.py 009150
    python score_modules.py 009150 --modules quality,growth

judgment 파일 형식 (정성 모듈에서 Claude 가 작성):
    data/module-results/{ticker}_{module}_judgment.json
    {
      "module": "moat",
      "criteria": [
        {"criterion_id": "MOA-01", "level": 2,
         "evidence_ids": ["B-FILING-001", "Q-OPERATINGMA-001"],
         "rationale": "..."},
        {"criterion_id": "MOA-02", "level": null,
         "na_reason": "근거 없음 — 추정하지 않는다", "evidence_ids": []}
      ],
      "strengths": [...], "weaknesses": [...], "counter_evidence": [...],
      "unknowns": [...], "invalidating_conditions": [...], "verdict": "..."
    }

출력:
    data/module-results/{ticker}_{module}.json
    data/{ticker}_composite.json
"""
from __future__ import annotations

import argparse

from _common import (
    DATA_DIR,
    SkillError,
    contract_path,
    die,
    judgment_path,
    load_modes,
    load_registry,
    log,
    metrics_path,
    module_result_path,
    now_iso,
    read_json,
    safe_div,
    validate_schema,
    validate_ticker,
    write_json,
)

MAX_LEVEL = 3


def band_level(value: float, bands: list) -> int | None:
    """[min, max, level] 구간에서 level 을 찾는다. null = 무한대."""
    for lo, hi, level in bands:
        lo_ok = (lo is None) or (value >= lo)
        hi_ok = (hi is None) or (value < hi)
        if lo_ok and hi_ok:
            return int(level)
    return None


def score_auto(crit: dict, metrics: dict, creds: dict) -> dict:
    """자동 채점. 값이 없으면 level=None (N/A) — **0 이 아니다**."""
    metric = crit["metric"]
    m = metrics["metrics"].get(metric)

    base = {
        "criterion_id": crit["id"],
        "name": crit["name"],
        "type": "auto",
        "weight": crit["weight"],
        "metric": metric,
        "evidence_ids": [],
        "rationale": None,
    }

    # 자격증명이 필요한데 없는 경우 → N/A (0점 아님)
    need = crit.get("requires_credentials") or []
    if need and not all(creds.get(c) for c in need):
        return {**base, "level": None, "metric_value": None,
                "na_reason": f"자격증명 없음 ({', '.join(need)}) — "
                             "데이터를 조회할 수 없어 N/A. 0점으로 채점하지 않는다."}

    if m is None:
        return {**base, "level": None, "metric_value": None,
                "na_reason": f"지표 '{metric}' 이 계산되지 않았다"}

    if m["value"] is None:
        return {**base, "level": None, "metric_value": None,
                "na_reason": m.get("na_reason") or "지표 값이 N/A"}

    level = band_level(float(m["value"]), crit["bands"])
    if level is None:
        return {**base, "level": None, "metric_value": m["value"],
                "na_reason": "밴드에 해당하는 구간이 없다 (registry bands 확인 필요)"}

    return {**base, "level": level, "metric_value": m["value"], "na_reason": None}


def score_judged(crit: dict, judgment: dict | None) -> dict:
    """Claude 의 서수 등급을 읽어 채점한다. **여기서 Claude 는 산술하지 않았다.**"""
    base = {
        "criterion_id": crit["id"],
        "name": crit["name"],
        "type": "judged",
        "weight": crit["weight"],
        "metric": None,
        "metric_value": None,
    }

    if judgment is None:
        return {**base, "level": None, "evidence_ids": [], "rationale": None,
                "na_reason": "judgment 파일이 없다 — 이 모듈은 아직 분석되지 않았다"}

    entry = next(
        (c for c in judgment.get("criteria", []) if c.get("criterion_id") == crit["id"]),
        None,
    )
    if entry is None:
        return {**base, "level": None, "evidence_ids": [], "rationale": None,
                "na_reason": f"judgment 에 {crit['id']} 항목이 없다"}

    level = entry.get("level")
    eids = entry.get("evidence_ids") or []

    if level is None:
        return {**base, "level": None, "evidence_ids": eids,
                "rationale": entry.get("rationale"),
                "na_reason": entry.get("na_reason") or "Claude 가 N/A 로 판단"}

    if not isinstance(level, int) or not (0 <= level <= MAX_LEVEL):
        raise SkillError(
            f"{crit['id']}: level 은 0~{MAX_LEVEL} 의 정수여야 한다 (받은 값: {level!r})"
        )

    # 근거 요구량 검증 — 근거 없는 판단은 채점하지 않는다 (Phase 8)
    need = crit.get("requires_evidence", 1)
    if len(eids) < need:
        return {**base, "level": None, "evidence_ids": eids,
                "rationale": entry.get("rationale"),
                "na_reason": f"근거 부족 — {need}개 필요하나 {len(eids)}개 제출됨. "
                             "근거 없는 주장은 채점하지 않는다."}

    return {**base, "level": level, "evidence_ids": eids,
            "rationale": entry.get("rationale"), "na_reason": None}


def score_module(module: str, spec: dict, metrics: dict, creds: dict) -> dict:
    """모듈 1개 채점. 점수 = Σ(w × level/3) / Σ(w, 채점된 것만) × 100."""
    judgment = None
    jp = judgment_path(metrics["ticker"], module)
    if jp.exists():
        judgment = read_json(jp)

    rows = [
        score_auto(c, metrics, creds) if c["type"] == "auto" else score_judged(c, judgment)
        for c in spec["criteria"]
    ]

    scored = [r for r in rows if r["level"] is not None]
    total_w = sum(r["weight"] for r in scored)

    if not scored or total_w == 0:
        score = None
        status = "insufficient_data"
    else:
        earned = sum(r["weight"] * r["level"] / MAX_LEVEL for r in scored)
        score = round(earned / total_w * 100, 1)
        status = "completed" if len(scored) == len(rows) else "partial"

    coverage = round(len(scored) / len(rows), 3) if rows else None

    # confidence: 데이터 확보율을 기본으로 하되, **judged criterion 에 한해** 근거 밀도를 반영한다.
    # **점수와 독립적이다** — 데이터가 부족하면 점수를 깎지 않고 confidence 를 낮춘다.
    #
    # ⚠️ auto criterion 은 criterion 단위 evidence_ids 가 비어 있는 것이 정상이다
    #    (근거는 metrics.json 의 지표 자체이며 evidence pack 에 별도로 존재한다).
    #    이를 '근거 없음'으로 세면 정량 모듈의 confidence 가 항상 0 이 되어,
    #    종합 신뢰도가 무너지고 판단 유보가 잘못 강제된다.
    conf = coverage
    judged_scored = [r for r in scored if r.get("type") == "judged"]
    if judged_scored:
        avg_ev = sum(len(r.get("evidence_ids") or []) for r in judged_scored) / len(judged_scored)
        conf = round(min(1.0, (coverage or 0) * min(1.0, avg_ev / 2.0)), 3)
    if judgment and judgment.get("counter_evidence"):
        conf = round(max(0.0, (conf or 0) - 0.1 * len(judgment["counter_evidence"])), 3)

    evidence_ids = sorted({
        eid for r in rows for eid in (r.get("evidence_ids") or [])
    })

    result = {
        "module": module,
        "ticker": metrics["ticker"],
        "status": status,
        "score": score,
        "max_score": 100,
        "confidence": conf,
        "evidence_coverage": coverage,
        "verdict": (judgment or {}).get("verdict"),
        "criteria_scores": rows,
        "strengths": (judgment or {}).get("strengths", [])[:5],
        "weaknesses": (judgment or {}).get("weaknesses", [])[:5],
        "counter_evidence": (judgment or {}).get("counter_evidence", []),
        "unknowns": (judgment or {}).get("unknowns", []),
        "invalidating_conditions": (judgment or {}).get("invalidating_conditions", []),
        "evidence_ids": evidence_ids,
        "validation": "pending",
        "validation_errors": [],
        "computed_at": now_iso(),
    }

    errs = validate_schema(result, "module-result.schema.json")
    if errs:
        raise SkillError(
            f"모듈 {module} 결과가 스키마를 위반했습니다:\n  - " + "\n  - ".join(errs)
        )
    return result


def composite(results: list[dict], mode: str, modes_cfg: dict) -> dict:
    """종합점수 — 실행·채점된 모듈의 가중치를 재정규화(합 100)해 계산한다."""
    weights = modes_cfg["modes"][mode]["weights"]

    usable = [r for r in results if r["score"] is not None and weights.get(r["module"], 0) > 0]
    total_w = sum(weights[r["module"]] for r in usable)

    if not usable or total_w == 0:
        return {
            "score": None, "confidence": None, "data_completeness": None,
            "verdict": "판단 유보",
            "verdict_reason": "채점 가능한 모듈이 없다. 데이터 부족으로 종합 판단을 유보한다.",
            "weights_used": {}, "renormalized": False,
            "formula": "N/A", "strongest_module": None, "weakest_module": None,
        }

    renorm = {r["module"]: round(weights[r["module"]] / total_w * 100, 2) for r in usable}
    score = round(sum(r["score"] * renorm[r["module"]] for r in usable) / 100, 1)

    # ── 신뢰도·데이터 완전성은 **요청된 모든 모듈**에 대해 계산한다 ──────────────
    # 채점된 모듈만 평균내면, 절반이 데이터 부족이어도 완전성이 95% 로 보이는
    # 착시가 생긴다. 채점 못 한 모듈은 coverage 0 으로 잡아야 정직하다.
    # (score 는 채점된 모듈만으로 재정규화하는 것이 맞다 — N/A 에 0점을 줄 수 없으므로.)
    requested = [r for r in results if weights.get(r["module"], 0) > 0]
    total_all = sum(weights[r["module"]] for r in requested)

    if total_all > 0:
        conf = round(
            sum((r["confidence"] or 0) * weights[r["module"]] for r in requested)
            / total_all, 3)
        completeness = round(
            sum((r["evidence_coverage"] or 0) * weights[r["module"]] for r in requested)
            / total_all, 3)
    else:
        conf = completeness = 0.0

    unscored = [r["module"] for r in requested if r["score"] is None]

    # 등급 결정 — 점수만으로 정하지 않는다.
    scale = modes_cfg["verdict_scale"]
    withheld = next(c for c in scale if c["id"] == "withheld")
    fw = withheld["force_when"]

    if completeness < fw["data_completeness_below"] or conf < fw["confidence_below"]:
        verdict = "판단 유보"
        reason = (
            f"데이터 완전성 {completeness:.0%}, 판단 신뢰도 {conf:.0%} — "
            f"임계(완전성 {fw['data_completeness_below']:.0%}, "
            f"신뢰도 {fw['confidence_below']:.0%}) 미만이므로 "
            "점수와 무관하게 판단을 유보한다."
        )
        if unscored:
            reason += f" 미채점 모듈: {', '.join(unscored)}."
    else:
        tier = next(
            c for c in sorted(
                [c for c in scale if c["id"] != "withheld"],
                key=lambda c: -c["min_score"])
            if score >= c["min_score"]
        )
        verdict = tier["label"]
        reason = (f"종합점수 {score}점 (데이터 완전성 {completeness:.0%}, "
                  f"판단 신뢰도 {conf:.0%})")
        if unscored:
            reason += (
                f" ※ {', '.join(unscored)} 모듈은 데이터·판단 부재로 채점되지 않아 "
                "종합점수에서 제외되었다 — 이 결론은 나머지 모듈에 한정된다."
            )

    ranked = sorted(usable, key=lambda r: r["score"], reverse=True)

    return {
        "score": score,
        "confidence": conf,
        "data_completeness": completeness,
        "verdict": verdict,
        "verdict_reason": reason,
        "weights_used": renorm,
        "renormalized": len(usable) < len([w for w in weights.values() if w > 0]),
        "formula": (
            "score = Σ(모듈점수 × 재정규화가중치) / 100  [채점된 모듈만]; "
            "confidence·data_completeness = Σ(값 × 원가중치) / Σ(원가중치)  [요청된 모든 모듈]"
        ),
        "strongest_module": ranked[0]["module"],
        "weakest_module": ranked[-1]["module"],
        "unscored_modules": unscored,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="모듈 채점 + 종합점수 (모든 산술의 단일 지점)")
    ap.add_argument("ticker")
    ap.add_argument("--modules", help="쉼표구분. 생략 시 계약의 required_modules")
    args = ap.parse_args()

    try:
        ticker = validate_ticker(args.ticker)
        registry = load_registry()
        modes_cfg = load_modes()
        metrics = read_json(metrics_path(ticker))
        contract = read_json(contract_path(ticker))

        mods = (
            [m.strip() for m in args.modules.split(",") if m.strip()]
            if args.modules else contract["required_modules"]
        )
        unknown = [m for m in mods if m not in registry["modules"]]
        if unknown:
            raise SkillError(f"알 수 없는 모듈: {', '.join(unknown)}")

        creds = contract.get("credentials_available", {})
        results = []
        for mod in mods:
            r = score_module(mod, registry["modules"][mod], metrics, creds)
            write_json(module_result_path(ticker, mod), r)
            results.append(r)

            s = "N/A" if r["score"] is None else f"{r['score']:.1f}"
            log(f"{mod}: score={s} conf={r['confidence']} "
                f"coverage={r['evidence_coverage']} status={r['status']}")

        comp = composite(results, contract["analysis_mode"], modes_cfg)
        out = write_json(DATA_DIR / f"{ticker}_composite.json", {
            "ticker": ticker,
            "analysis_mode": contract["analysis_mode"],
            "composite": comp,
            "modules": [
                {
                    "module": r["module"], "score": r["score"],
                    "confidence": r["confidence"],
                    "evidence_coverage": r["evidence_coverage"],
                    "status": r["status"],
                    "weight": comp["weights_used"].get(r["module"]),
                    "counted_in_composite": r["module"] in comp["weights_used"],
                }
                for r in results
            ],
            "computed_at": now_iso(),
        })

        print(f"저장: {out}")
        print(f"\n종합: {comp['verdict']} "
              f"(점수 {comp['score']} / 신뢰도 {comp['confidence']} / "
              f"데이터 완전성 {comp['data_completeness']})")
        print(f"  {comp['verdict_reason']}")
        if comp["renormalized"]:
            print("  ※ 일부 모듈만 실행되어 가중치를 재정규화했습니다.")
        for r in results:
            s = "N/A" if r["score"] is None else f"{r['score']:5.1f}"
            w = comp["weights_used"].get(r["module"])
            print(f"  {r['module']:<10} {s}  "
                  f"(가중 {w if w else '제외':>6}, coverage {r['evidence_coverage']})")

    except SkillError as e:
        die(str(e))


if __name__ == "__main__":
    main()
