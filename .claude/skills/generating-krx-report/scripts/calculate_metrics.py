#!/usr/bin/env python3
"""지표 계산 — **모든 산술은 여기서만 일어난다.**

LLM 은 성장률·CAGR·수익률·밸류에이션·총점을 암산하지 않는다 (Phase 3).
각 지표는 formula, inputs, 그리고 입력의 rcept_no 를 함께 남겨 **재현 가능**해야 한다 (Gate 3).

계산 규칙 (Gate 3):
  - 분모 0/None → None (**0 이 아니다**)
  - 기준값이 0 이하인 YoY·CAGR → None (음수 기준 성장률 금지)
  - 적자기업 PER/EV-EBITDA → None (na_reason 기록)
  - 자격증명 부재로 못 구한 값 → None (**0 으로 채점하지 않는다**)

사용법:
    python calculate_metrics.py 009150

출력:
    data/normalized/{ticker}_metrics.json
"""
from __future__ import annotations

import argparse

from _common import (
    SkillError,
    cagr,
    die,
    log,
    metrics_path,
    normalized_path,
    now_iso,
    pct_change,
    read_json,
    safe_div,
    validate_ticker,
    write_json,
)

TTM_QUARTERS = 4


def M(
    value: float | None,
    unit: str,
    formula: str | None = None,
    inputs: dict | None = None,
    rcept_nos: list[str] | None = None,
    period: str | None = None,
    period_type: str | None = None,
    na_reason: str | None = None,
    limitations: list[str] | None = None,
) -> dict:
    """지표 1개의 표준 표현. value=None 은 N/A 이며 0 과 명확히 구분된다."""
    return {
        "value": value,
        "unit": unit,
        "formula": formula,
        "inputs": inputs or {},
        "rcept_nos": [r for r in (rcept_nos or []) if r],
        "period": period,
        "period_type": period_type,
        "na_reason": na_reason if value is None else None,
        "limitations": limitations or [],
    }


def _acc(q: dict, key: str) -> float | None:
    return q["accounts"].get(key, {}).get("value")


def _rcepts(qs: list[dict], key: str) -> list[str]:
    out: list[str] = []
    for q in qs:
        out.extend(q["accounts"].get(key, {}).get("input_rcept_nos", []) or [])
    return list(dict.fromkeys(out))


def ttm_sum(quarters: list[dict], key: str) -> tuple[float | None, list[str], str | None]:
    """최근 4개 분기 단독값의 합. 하나라도 결측이면 None (**부분합을 TTM 이라 부르지 않는다**)."""
    if len(quarters) < TTM_QUARTERS:
        return None, [], f"분기 단독값이 {len(quarters)}개뿐이라 TTM(4개 분기) 산출 불가"
    window = quarters[-TTM_QUARTERS:]
    vals = [_acc(q, key) for q in window]
    if any(v is None for v in vals):
        missing = [q["period_label"] for q, v in zip(window, vals) if v is None]
        return None, [], f"TTM 구간에 결측 분기 존재: {', '.join(missing)} (0 으로 대체하지 않음)"
    return sum(vals), _rcepts(window, key), None


def latest_bs(quarters: list[dict], annual: list[dict], key: str) -> tuple[float | None, str | None, str | None]:
    """재무상태표 최신 시점값. (value, rcept_no, period)"""
    if quarters:
        q = quarters[-1]
        v = _acc(q, key)
        if v is not None:
            return v, q["accounts"][key].get("rcept_no"), q["period_label"]
    for a in annual:  # annual 은 최신순
        v = a["accounts"].get(key, {}).get("value")
        if v is not None:
            return v, a["accounts"][key].get("rcept_no"), f"{a['bsns_year']} 사업보고서"
    return None, None, None


def annual_series(annual: list[dict], key: str) -> list[tuple[int, float, str | None]]:
    """(연도, 값, rcept_no) 오름차순. 결측 연도는 제외."""
    out = [
        (a["bsns_year"], a["accounts"][key]["value"], a["accounts"][key].get("rcept_no"))
        for a in annual
        if a["accounts"].get(key, {}).get("value") is not None
    ]
    return sorted(out, key=lambda t: t[0])


def yoy_quarter(quarters: list[dict], key: str) -> dict:
    """최근 분기 단독값의 전년 동기 대비 증감률. 동일 분기끼리만 비교한다 (Gate 3)."""
    if not quarters:
        return M(None, "%", na_reason="분기 단독값이 없다")

    cur = quarters[-1]
    cur_v = _acc(cur, key)
    if cur_v is None:
        return M(None, "%", period=cur["period_label"],
                 na_reason=f"{cur['period_label']} {key} 결측")

    prior = next(
        (q for q in quarters
         if q["quarter"] == cur["quarter"] and q["year"] == cur["year"] - 1),
        None,
    )
    if prior is None:
        return M(None, "%", period=cur["period_label"],
                 na_reason=f"전년 동기({cur['year'] - 1}Q{cur['quarter']}) 데이터 없음")

    prev_v = _acc(prior, key)
    if prev_v is None:
        return M(None, "%", period=cur["period_label"],
                 na_reason=f"전년 동기 {key} 결측")

    val = pct_change(cur_v, prev_v)
    if val is None:
        return M(None, "%", period=cur["period_label"],
                 inputs={"current": cur_v, "prior_year": prev_v},
                 na_reason="전년 동기 기준값이 0 이하 — 증감률이 의미를 갖지 않는다 "
                           "(적자→적자 변화를 성장률로 표기하지 않는다)")

    return M(
        round(val, 2), "%",
        formula=f"({cur['period_label']} − {prior['period_label']}) / |{prior['period_label']}| × 100",
        inputs={"current": cur_v, "prior_year": prev_v},
        rcept_nos=_rcepts([cur, prior], key),
        period=f"{cur['period_label']} vs {prior['period_label']}",
        period_type="quarter_standalone",
    )


def cagr_metric(annual: list[dict], key: str, years: int = 3) -> dict:
    """N년 CAGR. 기준연도 값이 0 이하이면 None (Gate 3)."""
    series = annual_series(annual, key)
    if len(series) < years + 1:
        return M(None, "%",
                 na_reason=f"{years}년 CAGR 에 {years + 1}개 연말값이 필요하나 {len(series)}개뿐")

    first_y, first_v, first_r = series[-(years + 1)]
    last_y, last_v, last_r = series[-1]

    val = cagr(last_v, first_v, years)
    if val is None:
        return M(None, "%",
                 inputs={"base_year": first_y, "base_value": first_v,
                         "final_year": last_y, "final_value": last_v},
                 na_reason=f"기준연도({first_y}) 값이 0 이하이거나 최종값이 음수 — "
                           "CAGR 이 정의되지 않는다")

    return M(
        round(val, 2), "%",
        formula=f"(({last_y} / {first_y}) ^ (1/{years}) − 1) × 100",
        inputs={"base_year": first_y, "base_value": first_v,
                "final_year": last_y, "final_value": last_v, "years": years},
        rcept_nos=[first_r, last_r],
        period=f"{first_y}~{last_y}",
        period_type="annual",
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="지표 계산 (모든 산술의 단일 지점)")
    ap.add_argument("ticker")
    args = ap.parse_args()

    try:
        ticker = validate_ticker(args.ticker)
        nz = read_json(normalized_path(ticker))

        annual = nz["annual"]                    # 최신순
        annual_asc = sorted(annual, key=lambda a: a["bsns_year"])
        quarters = nz["quarterly_standalone"]    # 오름차순
        shares = nz["shares"]
        mkt = nz["market"]
        fs_div = nz["fs_div"]

        m: dict[str, dict] = {}

        # ── TTM 기초값 ───────────────────────────────────────────────────────
        rev_ttm, rev_r, rev_na = ttm_sum(quarters, "revenue")
        op_ttm, op_r, op_na = ttm_sum(quarters, "operating_income")
        ni_ttm, ni_r, ni_na = ttm_sum(quarters, "net_income")
        ocf_ttm, ocf_r, ocf_na = ttm_sum(quarters, "ocf")
        capex_ttm, capex_r, _ = ttm_sum(quarters, "capex")
        dep_ttm, dep_r, _ = ttm_sum(quarters, "depreciation")
        tax_ttm, _, _ = ttm_sum(quarters, "income_tax")
        pretax_ttm, _, _ = ttm_sum(quarters, "pretax_income")
        int_ttm, int_r, _ = ttm_sum(quarters, "interest_expense")

        ttm_period = (
            f"{quarters[-4]['period_label']}~{quarters[-1]['period_label']}"
            if len(quarters) >= 4 else None
        )

        # TTM 이 불가하면 최근 사업보고서(연간)로 폴백하고 **폴백 사실을 남긴다**
        ttm_fallback = False
        if rev_ttm is None and annual_asc:
            a = annual_asc[-1]
            rev_ttm = a["accounts"]["revenue"]["value"]
            op_ttm = a["accounts"]["operating_income"]["value"]
            ni_ttm = a["accounts"]["net_income"]["value"]
            ocf_ttm = a["accounts"]["ocf"]["value"]
            capex_ttm = a["accounts"]["capex"]["value"]
            dep_ttm = a["accounts"]["depreciation"]["value"]
            tax_ttm = a["accounts"]["income_tax"]["value"]
            pretax_ttm = a["accounts"]["pretax_income"]["value"]
            int_ttm = a["accounts"]["interest_expense"]["value"]
            ttm_period = f"{a['bsns_year']} 사업보고서(연간)"
            ttm_fallback = True
            log(f"TTM 산출 불가({rev_na}) → {a['bsns_year']} 연간값으로 폴백")

        fb_lim = (["TTM 대신 최근 연간값으로 폴백했다 — 최신 분기를 반영하지 않는다"]
                  if ttm_fallback else [])

        m["revenue_ttm"] = M(rev_ttm, "KRW", "최근 4개 분기 단독값 합",
                             rcept_nos=rev_r, period=ttm_period, period_type="ttm",
                             na_reason=rev_na, limitations=fb_lim)
        m["operating_income_ttm"] = M(op_ttm, "KRW", "최근 4개 분기 단독값 합",
                                      rcept_nos=op_r, period=ttm_period, period_type="ttm",
                                      na_reason=op_na, limitations=fb_lim)
        m["net_income_ttm"] = M(ni_ttm, "KRW", "최근 4개 분기 단독값 합",
                                rcept_nos=ni_r, period=ttm_period, period_type="ttm",
                                na_reason=ni_na, limitations=fb_lim)

        # ── 재무상태표 시점값 ────────────────────────────────────────────────
        equity, eq_r, eq_p = latest_bs(quarters, annual, "equity")
        cash, cash_r, _ = latest_bs(quarters, annual, "cash")
        debt, debt_r, _ = latest_bs(quarters, annual, "total_debt")
        cur_a, _, _ = latest_bs(quarters, annual, "current_assets")
        cur_l, _, _ = latest_bs(quarters, annual, "current_liabilities")

        net_debt = (debt - cash) if (debt is not None and cash is not None) else None
        m["net_debt"] = M(net_debt, "KRW", "총차입금 − 현금및현금성자산",
                          inputs={"total_debt": debt, "cash": cash},
                          rcept_nos=[debt_r, cash_r], period=eq_p,
                          period_type="point_in_time",
                          na_reason=None if net_debt is not None else
                          "차입금 또는 현금 계정을 확정하지 못했다 (무차입과 미확인을 구분한다)")

        # ── Quality ─────────────────────────────────────────────────────────
        opm = safe_div(op_ttm, rev_ttm)
        m["operating_margin_ttm"] = M(
            round(opm * 100, 2) if opm is not None else None, "%",
            "operating_income_ttm / revenue_ttm × 100",
            {"operating_income_ttm": op_ttm, "revenue_ttm": rev_ttm},
            op_r + rev_r, ttm_period, "ttm",
            na_reason=None if opm is not None else "매출 또는 영업이익 TTM 결측",
            limitations=fb_lim)

        npm = safe_div(ni_ttm, rev_ttm)
        m["net_margin_ttm"] = M(
            round(npm * 100, 2) if npm is not None else None, "%",
            "net_income_ttm / revenue_ttm × 100",
            {"net_income_ttm": ni_ttm, "revenue_ttm": rev_ttm},
            ni_r + rev_r, ttm_period, "ttm", limitations=fb_lim)

        roe = safe_div(ni_ttm, equity)
        m["roe_ttm"] = M(
            round(roe * 100, 2) if roe is not None else None, "%",
            "net_income_ttm / equity(기말) × 100",
            {"net_income_ttm": ni_ttm, "equity": equity},
            ni_r + [eq_r], ttm_period, "ttm",
            na_reason=None if roe is not None else "순이익 TTM 또는 자본총계 결측",
            limitations=(fb_lim + ["평균자본이 아닌 기말자본을 분모로 사용했다"]))

        # ROIC — 가정(유효세율)이 필요하므로 가정을 명시한다
        eff_tax = safe_div(tax_ttm, pretax_ttm)
        if eff_tax is not None and not (0 <= eff_tax <= 0.6):
            eff_tax = None  # 비정상 유효세율(환급·이연 등)은 신뢰하지 않는다
        invested = (equity + net_debt) if (equity is not None and net_debt is not None) else None
        roic = None
        if op_ttm is not None and eff_tax is not None and invested is not None and invested > 0:
            roic = safe_div(op_ttm * (1 - eff_tax), invested)
        m["roic_ttm"] = M(
            round(roic * 100, 2) if roic is not None else None, "%",
            "영업이익_TTM × (1 − 유효세율) / (자본총계 + 순차입금) × 100",
            {"operating_income_ttm": op_ttm, "effective_tax_rate": eff_tax,
             "invested_capital": invested},
            op_r + [eq_r], ttm_period, "ttm",
            na_reason=None if roic is not None else
            "유효세율 또는 투하자본을 확정하지 못했다 (투하자본 ≤ 0 포함)",
            limitations=["유효세율 = 법인세비용/세전이익 (가정). 투하자본 = 자본총계 + 순차입금 (정의 가정)"])

        cc = safe_div(ocf_ttm, ni_ttm) if (ni_ttm or 0) > 0 else None
        m["cash_conversion_ttm"] = M(
            round(cc, 3) if cc is not None else None, "x",
            "ocf_ttm / net_income_ttm",
            {"ocf_ttm": ocf_ttm, "net_income_ttm": ni_ttm},
            ocf_r + ni_r, ttm_period, "ttm",
            na_reason=None if cc is not None else
            "순이익이 0 이하이거나 결측 — 현금전환율이 의미를 갖지 않는다",
            limitations=fb_lim)

        fcf = (ocf_ttm - abs(capex_ttm)) if (ocf_ttm is not None and capex_ttm is not None) else None
        m["fcf_ttm"] = M(fcf, "KRW", "ocf_ttm − |capex_ttm|",
                         {"ocf_ttm": ocf_ttm, "capex_ttm": capex_ttm},
                         ocf_r + capex_r, ttm_period, "ttm",
                         na_reason=None if fcf is not None else "영업현금흐름 또는 CAPEX 결측",
                         limitations=fb_lim)

        fcfm = safe_div(fcf, rev_ttm)
        m["fcf_margin_ttm"] = M(
            round(fcfm * 100, 2) if fcfm is not None else None, "%",
            "fcf_ttm / revenue_ttm × 100",
            {"fcf_ttm": fcf, "revenue_ttm": rev_ttm},
            ocf_r + rev_r, ttm_period, "ttm", limitations=fb_lim)

        nde = safe_div(net_debt, equity)
        m["net_debt_to_equity"] = M(
            round(nde, 3) if nde is not None else None, "x",
            "net_debt / equity",
            {"net_debt": net_debt, "equity": equity},
            [debt_r, cash_r, eq_r], eq_p, "point_in_time",
            na_reason=None if nde is not None else "순차입금 또는 자본총계 결측")

        # 이자비용을 별도 공시하지 않는 기업은 '금융원가'가 대용된다.
        # 그 경우 이자 외 항목이 섞이므로 **대용 사실을 반드시 드러낸다**.
        int_acc = ""
        if quarters:
            int_acc = (quarters[-1]["accounts"].get("interest_expense", {})
                       .get("account_nm") or "")
        elif annual_asc:
            int_acc = (annual_asc[-1]["accounts"].get("interest_expense", {})
                       .get("account_nm") or "")
        int_lims = []
        if "금융원가" in int_acc:
            int_lims.append(
                "이자비용이 별도 공시되지 않아 '금융원가'를 대용했다 — "
                "외환손실·파생손실 등 이자 외 항목이 포함될 수 있어 이자보상배율이 과소평가될 수 있다"
            )

        icov = safe_div(op_ttm, abs(int_ttm)) if (int_ttm not in (None, 0)) else None
        m["interest_coverage"] = M(
            round(icov, 2) if icov is not None else None, "x",
            "operating_income_ttm / |interest_expense_ttm|",
            {"operating_income_ttm": op_ttm, "interest_expense_ttm": int_ttm},
            op_r + int_r, ttm_period, "ttm",
            na_reason=None if icov is not None else "이자비용·금융원가 계정을 찾지 못했거나 0",
            limitations=int_lims)

        crat = safe_div(cur_a, cur_l)
        m["current_ratio"] = M(
            round(crat, 2) if crat is not None else None, "x",
            "유동자산 / 유동부채", {"current_assets": cur_a, "current_liabilities": cur_l},
            [eq_r], eq_p, "point_in_time")

        cap_ocf = safe_div(abs(capex_ttm) if capex_ttm is not None else None, ocf_ttm)
        m["capex_to_ocf"] = M(
            round(cap_ocf, 3) if cap_ocf is not None else None, "x",
            "|capex_ttm| / ocf_ttm", {"capex_ttm": capex_ttm, "ocf_ttm": ocf_ttm},
            capex_r + ocf_r, ttm_period, "ttm")

        # 희석 — 연도별 발행주식수 스냅샷이 2개 이상 있어야 계산된다
        hist = shares.get("history") or []
        share_chg = None
        share_na = "발행주식수 스냅샷이 1개뿐이라 증감률 산출 불가"
        share_inputs: dict = {}
        share_rcepts: list[str] = []
        if len(hist) >= 2:
            cur_s, prev_s = hist[0], hist[1]
            chg = pct_change(cur_s["issued_shares"], prev_s["issued_shares"])
            if chg is not None:
                share_chg = round(chg, 3)
                share_na = None
            share_inputs = {
                f"{cur_s['bsns_year']}": cur_s["issued_shares"],
                f"{prev_s['bsns_year']}": prev_s["issued_shares"],
            }
            share_rcepts = [cur_s.get("rcept_no"), prev_s.get("rcept_no")]
        m["share_change_1y"] = M(
            share_chg, "%", "(최근 발행주식수 − 직전 발행주식수) / 직전 × 100",
            share_inputs, share_rcepts,
            period_type="annual", na_reason=share_na,
            limitations=["사업보고서 연 1회 스냅샷 기준 — 기중 증자는 반영이 지연될 수 있다"])

        # ── Growth ──────────────────────────────────────────────────────────
        m["rev_yoy_q"] = yoy_quarter(quarters, "revenue")
        m["op_yoy_q"] = yoy_quarter(quarters, "operating_income")
        m["eps_yoy_q"] = yoy_quarter(quarters, "eps")
        m["rev_cagr_3y"] = cagr_metric(annual, "revenue", 3)
        m["op_cagr_3y"] = cagr_metric(annual, "operating_income", 3)
        m["eps_cagr_3y"] = cagr_metric(annual, "eps", 3)

        # 성장 가속도 = 이번 분기 매출 YoY − 직전 분기 매출 YoY
        accel = None
        accel_na = "직전 분기 YoY 를 구할 수 없어 가속도 산출 불가"
        accel_in: dict = {}
        if len(quarters) >= 2:
            prev_yoy = yoy_quarter(quarters[:-1], "revenue")
            cur_yoy = m["rev_yoy_q"]
            if cur_yoy["value"] is not None and prev_yoy["value"] is not None:
                accel = round(cur_yoy["value"] - prev_yoy["value"], 2)
                accel_na = None
                # 입력 키를 실제 지표명으로 둔다 → evidence 체인이 연결된다
                accel_in = {"rev_yoy_q": cur_yoy["value"],
                            "previous_quarter_rev_yoy": prev_yoy["value"]}
        m["growth_acceleration_pp"] = M(
            accel, "%p", "이번분기 매출YoY(rev_yoy_q) − 직전분기 매출YoY", accel_in,
            period_type="quarter_standalone", na_reason=accel_na)

        # 수익성 동반 성장 = 영업이익 YoY − 매출 YoY
        gap = None
        gap_na = "매출 또는 영업이익 YoY 결측"
        gap_in: dict = {}
        if m["op_yoy_q"]["value"] is not None and m["rev_yoy_q"]["value"] is not None:
            gap = round(m["op_yoy_q"]["value"] - m["rev_yoy_q"]["value"], 2)
            gap_na = None
            gap_in = {"op_yoy_q": m["op_yoy_q"]["value"],
                      "rev_yoy_q": m["rev_yoy_q"]["value"]}
        m["profitable_growth_gap_pp"] = M(
            gap, "%p", "op_yoy_q − rev_yoy_q", gap_in,
            period_type="quarter_standalone", na_reason=gap_na)

        # ── 시가총액: 종가(Naver/pykrx) × 발행주식수(DART) ────────────────────
        close = mkt["close"]
        issued = shares["issued_shares"]
        treasury = shares.get("treasury_shares")
        as_of = mkt["as_of"]

        mcap = close * issued if (close and issued) else None

        mcap_lims = [
            f"종가는 {as_of} 기준(pykrx→Naver, 비공식), "
            f"발행주식수는 {shares['bsns_year']} 사업보고서 기준 — **기준일이 다르다**",
        ]
        if shares.get("has_preferred"):
            pref = shares.get("preferred_shares")
            mcap_lims.append(
                f"보통주 {issued:,.0f}주만 반영했다 (KRX 상장주식수 정의와 동일). "
                f"우선주 {pref:,.0f}주는 제외되었다 — 보통주 종가를 우선주에 곱할 수 없기 때문이다. "
                "따라서 PER·PBR 은 **보통주 기준**이며, 분자(시가총액)는 우선주를 빼지만 "
                "분모(순이익·자본총계)는 우선주 몫을 포함해 다소 보수적으로 나온다."
            )

        # KRX 공표 시가총액과 교차검증한다 (자격증명이 있을 때).
        # 괴리가 크면 주식 종류(보통주/우선주) 혼동 등 계산 오류일 수 있으므로
        # **숨기지 않고 limitation 으로 드러낸다.**
        xcheck = mkt.get("krx_market_cap_crosscheck")
        if xcheck and mcap:
            krx_mcap = xcheck["market_cap"]
            diff_pct = (mcap - krx_mcap) / krx_mcap * 100 if krx_mcap else None
            if diff_pct is not None:
                if abs(diff_pct) < 0.5:
                    mcap_lims.append(
                        f"KRX 공표 시가총액과 대조: 일치 (괴리 {diff_pct:+.2f}%)"
                    )
                else:
                    mcap_lims.append(
                        f"⚠️ KRX 공표 시가총액({krx_mcap:,.0f})과 {diff_pct:+.2f}% 괴리. "
                        f"주식수 기준일 차이 또는 주식 종류 처리 차이일 수 있다 — "
                        f"밸류에이션 해석 시 감안할 것."
                    )

        m["market_cap"] = M(
            mcap, "KRW", "종가 × 보통주 발행주식수",
            {"close": close, "common_shares": issued,
             "preferred_shares_excluded": shares.get("preferred_shares"),
             "krx_published_market_cap": (xcheck or {}).get("market_cap")},
            [shares.get("rcept_no")], as_of, "point_in_time",
            na_reason=None if mcap else "종가 또는 발행주식수 결측",
            limitations=mcap_lims)
        m["close_price"] = M(close, "KRW", None, {}, [], as_of, "point_in_time")

        # ── Valuation ───────────────────────────────────────────────────────
        # 적자기업 PER 금지 (Gate 3)
        if ni_ttm is None:
            per = None
            per_na = "순이익 TTM 결측"
        elif ni_ttm <= 0:
            per = None
            per_na = "적자기업 — PER 을 적용하지 않는다 (Gate 3)"
        else:
            per = safe_div(mcap, ni_ttm)
            per_na = None if per is not None else "시가총액 결측"
        m["per_trailing"] = M(
            round(per, 2) if per is not None else None, "x",
            "market_cap / net_income_ttm",
            {"market_cap": mcap, "net_income_ttm": ni_ttm},
            ni_r, f"{as_of} / {ttm_period}", "ttm", na_reason=per_na,
            limitations=["Trailing 기준. Forward PER 은 검증된 Forward EPS 가 없어 계산하지 않는다"])

        pbr = safe_div(mcap, equity)
        m["pbr"] = M(round(pbr, 2) if pbr is not None else None, "x",
                     "market_cap / equity", {"market_cap": mcap, "equity": equity},
                     [eq_r], f"{as_of} / {eq_p}", "point_in_time",
                     na_reason=None if pbr is not None else "시가총액 또는 자본총계 결측")

        ebitda = (op_ttm + abs(dep_ttm)) if (op_ttm is not None and dep_ttm is not None) else None
        ev = (mcap + net_debt) if (mcap is not None and net_debt is not None) else None
        # 감가상각비를 현금흐름표 본문에 표시하지 않는 기업이 있다 (주석에만 존재).
        # fnlttSinglAcntAll 로는 확보할 수 없으므로 **EBITDA·EV/EBITDA 는 N/A** 가 된다.
        # 추정하지 않는다 — 0 으로 채우지도 않는다.
        if dep_ttm is None:
            eve = None
            eve_na = (
                "감가상각비가 재무제표 본문에 공시되지 않아 EBITDA 를 산출할 수 없다 "
                "(fnlttSinglAcntAll 미제공, 주석에만 존재). 추정하지 않는다."
            )
        elif ebitda is None or ebitda <= 0:
            eve = None
            eve_na = "EBITDA 가 0 이하 — EV/EBITDA 를 적용하지 않는다"
        else:
            eve = safe_div(ev, ebitda)
            eve_na = None if eve is not None else "EV 결측"

        m["ebitda_ttm"] = M(
            ebitda, "KRW", "operating_income_ttm + |depreciation_ttm|",
            {"operating_income_ttm": op_ttm, "depreciation_ttm": dep_ttm},
            op_r + dep_r, ttm_period, "ttm",
            na_reason=None if ebitda is not None else eve_na,
            limitations=["현금흐름표의 감가상각비를 사용했다 (영업외 항목 포함 가능)"])
        m["ev"] = M(ev, "KRW", "market_cap + net_debt",
                    {"market_cap": mcap, "net_debt": net_debt}, [], as_of, "point_in_time")
        m["ev_ebitda"] = M(round(eve, 2) if eve is not None else None, "x",
                           "ev / ebitda_ttm", {"ev": ev, "ebitda_ttm": ebitda},
                           [], f"{as_of} / {ttm_period}", "ttm", na_reason=eve_na)

        psr = safe_div(mcap, rev_ttm)
        m["psr"] = M(round(psr, 2) if psr is not None else None, "x",
                     "market_cap / revenue_ttm", {"market_cap": mcap, "revenue_ttm": rev_ttm},
                     rev_r, f"{as_of} / {ttm_period}", "ttm")

        ey = safe_div(ni_ttm, mcap)
        m["earnings_yield"] = M(
            round(ey * 100, 2) if ey is not None else None, "%",
            "net_income_ttm / market_cap × 100",
            {"net_income_ttm": ni_ttm, "market_cap": mcap}, ni_r,
            f"{as_of} / {ttm_period}", "ttm")

        fy = safe_div(fcf, mcap)
        m["fcf_yield"] = M(
            round(fy * 100, 2) if fy is not None else None, "%",
            "fcf_ttm / market_cap × 100", {"fcf_ttm": fcf, "market_cap": mcap},
            ocf_r, f"{as_of} / {ttm_period}", "ttm")

        # ── Trend ───────────────────────────────────────────────────────────
        series = mkt["series"]
        closes = [p["close"] for p in series]
        highs = [p["high"] for p in series]
        vols = [p["volume"] for p in series]

        win = min(250, len(highs))
        high_52w = max(highs[-win:]) if win else None
        pfh = safe_div(close - high_52w, high_52w) if high_52w else None
        m["high_52w"] = M(high_52w, "KRW", f"최근 {win} 영업일 고가 최대값", {}, [], as_of, "range")
        m["pct_from_52w_high"] = M(
            round(pfh * 100, 2) if pfh is not None else None, "%",
            "(종가 − 52주고가) / 52주고가 × 100",
            {"close": close, "high_52w": high_52w}, [], as_of, "point_in_time",
            limitations=[f"{win} 영업일 기준 (52주 미만이면 그만큼만 사용)"])

        vol60 = vols[-60:]
        avg60 = sum(vol60) / len(vol60) if vol60 else None
        vr = safe_div(vols[-1], avg60)
        m["volume_ratio_vs_60d"] = M(
            round(vr, 2) if vr is not None else None, "x",
            "최근 거래량 / 60일 평균 거래량",
            {"last_volume": vols[-1], "avg_volume_60d": avg60}, [], as_of, "point_in_time")

        # 상대강도·시장방향 — 지수가 없으면 N/A (**0 아님**)
        index = mkt.get("index")
        if index and len(index["series"]) >= 200:
            idx_closes = [p["close"] for p in index["series"]]

            n6 = min(120, len(closes), len(idx_closes))  # 약 6개월 영업일
            stock_ret = pct_change(closes[-1], closes[-n6])
            index_ret = pct_change(idx_closes[-1], idx_closes[-n6])
            rs = (round(stock_ret - index_ret, 2)
                  if (stock_ret is not None and index_ret is not None) else None)
            m["rs_vs_index_6m_pp"] = M(
                rs, "%p", "종목 6개월 수익률 − 지수 6개월 수익률",
                {"stock_return": stock_ret, "index_return": index_ret,
                 "index": index["index_name"], "trading_days": n6},
                [], as_of, "range",
                na_reason=None if rs is not None else "수익률 계산 불가")

            ma200 = sum(idx_closes[-200:]) / 200
            ivm = safe_div(idx_closes[-1] - ma200, ma200)
            m["index_vs_ma200_pct"] = M(
                round(ivm * 100, 2) if ivm is not None else None, "%",
                "(지수 종가 − 200일 이동평균) / 200일 이동평균 × 100",
                {"index_close": idx_closes[-1], "ma200": ma200,
                 "index": index["index_name"]},
                [], as_of, "point_in_time")
        else:
            na = ("KRX_ID/KRX_PW 미설정으로 지수 데이터를 조회할 수 없다. "
                  "**N/A 이며 0 이 아니다 — 0점으로 채점하지 않는다.**")
            m["rs_vs_index_6m_pp"] = M(None, "%p", na_reason=na)
            m["index_vs_ma200_pct"] = M(None, "%", na_reason=na)

        # 수급 — 없으면 N/A
        flow = mkt.get("investor_flow")
        if flow and mcap:
            net = (flow.get("inst_net") or 0) + (flow.get("foreign_net") or 0)
            ratio = safe_div(net, mcap)
            m["inst_foreign_net_60d_to_mktcap"] = M(
                round(ratio * 100, 3) if ratio is not None else None, "%",
                "(기관 순매수 + 외국인 순매수, 60일) / 시가총액 × 100",
                {"inst_net": flow.get("inst_net"), "foreign_net": flow.get("foreign_net"),
                 "market_cap": mcap},
                [], as_of, "range",
                limitations=["pykrx→KRX 경유 (비공식). 거래대금 기준 순매수"])
        else:
            m["inst_foreign_net_60d_to_mktcap"] = M(
                None, "%",
                na_reason="KRX_ID/KRX_PW 미설정으로 수급 데이터를 조회할 수 없다. "
                          "**N/A 이며 0 이 아니다.**")

        available = sum(1 for v in m.values() if v["value"] is not None)
        result = {
            "ticker": ticker,
            "fs_div": fs_div,
            "as_of": as_of,
            "ttm_period": ttm_period,
            "ttm_fallback": ttm_fallback,
            "metrics": m,
            "summary": {"total": len(m), "available": available, "na": len(m) - available},
            "calculated_at": now_iso(),
        }

        out = write_json(metrics_path(ticker), result)
        print(f"저장: {out}")
        print(f"  지표 {len(m)}개 중 {available}개 산출, {len(m) - available}개 N/A")
        na_list = [k for k, v in m.items() if v["value"] is None]
        if na_list:
            print(f"  N/A: {', '.join(na_list)}")

    except SkillError as e:
        die(str(e))


if __name__ == "__main__":
    main()
