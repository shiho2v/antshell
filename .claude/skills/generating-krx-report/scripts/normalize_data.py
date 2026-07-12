#!/usr/bin/env python3
"""정규화 — 원시 DART/KRX 응답을 계산 가능한 표준 구조로 변환한다.

**이 스크립트의 존재 이유**: DART 분기보고서 금액은 누적(YTD)이며
`thstrm_add_amount` 는 누락이 잦다 (design-review.md 2.3).
분기 단독값을 API 필드 하나로 믿지 않고 **연속 누적 보고서를 차분**해 파생한다.

    Q1 = 1Q누적
    Q2 = 반기누적 − 1Q누적
    Q3 = 3Q누적 − 반기누적
    Q4 = 사업보고서(FY) − 3Q누적

인접 보고서가 없으면 해당 분기는 **N/A** 다. **0 이 아니다.**
재무상태표(BS)는 시점값이므로 차분하지 않는다.

사용법:
    python normalize_data.py 009150

출력:
    data/normalized/{ticker}_normalized.json
"""
from __future__ import annotations

import argparse

from _common import (
    REPRT_ANNUAL,
    REPRT_HALF,
    REPRT_Q1,
    REPRT_Q3,
    SkillError,
    clean_number,
    die,
    log,
    normalized_path,
    now_iso,
    raw_path,
    read_json,
    validate_ticker,
    write_json,
)

# ── 계정 매핑 ───────────────────────────────────────────────────────────────
# account_id(XBRL 표준계정ID)를 1순위로, account_nm 키워드를 폴백으로 쓴다.
# account_id 가 '-표준계정코드 미사용-' 인 경우가 있어 이름 폴백이 필요하다.
#
# flow=True  : 기간 항목 (IS/CIS/CF) → 누적 차분 대상
# flow=False : 시점 항목 (BS)        → 차분하지 않음
ACCOUNTS: dict[str, dict] = {
    "revenue": {
        "sj": {"IS", "CIS"}, "flow": True,
        "ids": ["ifrs-full_Revenue", "ifrs-full_RevenueFromContractsWithCustomers"],
        "names": ["매출액", "수익(매출액)", "영업수익"],
    },
    "operating_income": {
        "sj": {"IS", "CIS"}, "flow": True,
        "ids": ["dart_OperatingIncomeLoss", "ifrs-full_ProfitLossFromOperatingActivities"],
        "names": ["영업이익", "영업이익(손실)", "영업손실"],
    },
    "net_income": {
        "sj": {"IS", "CIS"}, "flow": True,
        "ids": ["ifrs-full_ProfitLoss"],
        "names": ["당기순이익", "당기순이익(손실)", "분기순이익", "반기순이익"],
    },
    # EPS 는 _pick_eps() 가 전담한다 (보통주/우선주 구분 필요 — 아래 주석 참조).
    "eps": {
        "sj": {"IS", "CIS"}, "flow": True,
        "ids": ["ifrs-full_BasicEarningsLossPerShare"],
        "names": [],          # 일반 이름매칭 사용 금지 — 우선주를 잡을 수 있다
        "picker": "eps",
    },
    "pretax_income": {
        "sj": {"IS", "CIS"}, "flow": True,
        "ids": ["ifrs-full_ProfitLossBeforeTax"],
        "names": ["법인세비용차감전순이익", "법인세차감전순이익"],
    },
    "income_tax": {
        "sj": {"IS", "CIS"}, "flow": True,
        "ids": ["ifrs-full_IncomeTaxExpenseContinuingOperations"],
        "names": ["법인세비용"],
    },
    # 이자비용을 별도 계정으로 공시하지 않는 기업이 많다. 그 경우 '금융원가'를 대용한다.
    # **금융원가는 이자비용 외 항목(외환손실·파생손실 등)을 포함할 수 있다** →
    # 이 대용 사실은 account_nm 으로 드러나며 calculate_metrics 가 limitation 으로 기록한다.
    "interest_expense": {
        "sj": {"IS", "CIS"}, "flow": True,
        "ids": ["ifrs-full_InterestExpense", "ifrs-full_FinanceCosts"],
        "names": ["이자비용", "금융원가"],
    },
    "depreciation": {
        "sj": {"CF"}, "flow": True,
        "ids": ["ifrs-full_DepreciationAndAmortisationExpense"],
        "names": ["감가상각비", "감가상각비와 무형자산상각비"],
    },
    "ocf": {
        "sj": {"CF"}, "flow": True,
        "ids": ["ifrs-full_CashFlowsFromUsedInOperatingActivities"],
        "names": ["영업활동현금흐름", "영업활동으로인한현금흐름", "영업활동으로 인한 현금흐름"],
    },
    "capex": {
        "sj": {"CF"}, "flow": True,
        "ids": [
            "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
        ],
        "names": ["유형자산의취득", "유형자산의 취득"],
    },
    "assets": {
        "sj": {"BS"}, "flow": False,
        "ids": ["ifrs-full_Assets"], "names": ["자산총계"],
    },
    "liabilities": {
        "sj": {"BS"}, "flow": False,
        "ids": ["ifrs-full_Liabilities"], "names": ["부채총계"],
    },
    "equity": {
        "sj": {"BS"}, "flow": False,
        "ids": ["ifrs-full_Equity"], "names": ["자본총계"],
    },
    "current_assets": {
        "sj": {"BS"}, "flow": False,
        "ids": ["ifrs-full_CurrentAssets"], "names": ["유동자산"],
    },
    "current_liabilities": {
        "sj": {"BS"}, "flow": False,
        "ids": ["ifrs-full_CurrentLiabilities"], "names": ["유동부채"],
    },
    "cash": {
        "sj": {"BS"}, "flow": False,
        "ids": ["ifrs-full_CashAndCashEquivalents"],
        "names": ["현금및현금성자산"],
    },
}

# 순차입금 계산용 — 표준 ID 가 기업마다 갈려 이름 폴백 비중이 크다.
DEBT_NAMES = ["단기차입금", "장기차입금", "유동성장기부채", "사채", "유동성사채"]


def _pick(rows: list[dict], spec: dict) -> tuple[float | None, str | None, str | None]:
    """(value, account_nm, rcept_no). account_id 우선, 없으면 이름 부분일치."""
    if spec.get("picker") == "eps":
        return _pick_eps(rows, spec)

    cands = [r for r in rows if (r.get("sj_div") or "") in spec["sj"]]

    for aid in spec["ids"]:
        for r in cands:
            if (r.get("account_id") or "").strip() == aid:
                v = clean_number(r.get("thstrm_amount"))
                if v is not None:
                    return v, r.get("account_nm"), r.get("rcept_no")

    for nm in spec["names"]:
        for r in cands:
            acc = (r.get("account_nm") or "").strip()
            if acc == nm or nm in acc:
                v = clean_number(r.get("thstrm_amount"))
                if v is not None:
                    return v, acc, r.get("rcept_no")

    return None, None, None


def _pick_eps(rows: list[dict], spec: dict) -> tuple[float | None, str | None, str | None]:
    """주당이익 전용 추출 — **보통주와 우선주를 반드시 구분한다.**

    실제 공시에서 확인된 함정 (삼성전기 2022~2023 사업보고서):
      - 과거 연도에는 EPS 행의 account_id 가 전부 '-표준계정코드 미사용-' 이라
        ID 매칭이 실패하고 **이름 매칭으로 넘어간다**.
      - 그 행들은 '보통주 기본 및 희석주당이익' / '우선주 기본 및 희석주당이익' 처럼
        나란히 존재한다. 단순 부분일치('주당이익')는 **우선주 EPS 를 집을 수 있다**.
      - 우선주 EPS 는 보통주보다 높다(예: 9,395 vs 9,345). 이를 잘못 쓰면
        PER·EPS 성장률·CANSLIM C 가 전부 오염된다.

    규칙:
      1) 우선주 행은 **무조건 제외**한다.
      2) ifrs-full_BasicEarningsLossPerShare (IFRS 상 보통주 기본주당이익)를 최우선.
      3) 이름 매칭 시 '보통주' 를 요구하고, 기본(basic) > 희석(diluted),
         총이익 > 계속영업이익 순으로 우선한다.
      4) 어느 것도 없으면 None (**0 이 아니다**).
    """
    cands = [
        r for r in rows
        if (r.get("sj_div") or "") in spec["sj"]
        and "주당" in (r.get("account_nm") or "")
        and "우선주" not in (r.get("account_nm") or "")          # (1) 우선주 배제
        and "우선주" not in (r.get("account_id") or "")
    ]
    if not cands:
        return None, None, None

    # (2) 표준 ID 우선
    for r in cands:
        if (r.get("account_id") or "").strip() == "ifrs-full_BasicEarningsLossPerShare":
            v = clean_number(r.get("thstrm_amount"))
            if v is not None:
                return v, r.get("account_nm"), r.get("rcept_no")

    # (3) 이름 기반 순위: 기본 우선, 계속영업이익 후순위
    def rank(r: dict) -> tuple[int, int, int]:
        nm = (r.get("account_nm") or "")
        return (
            0 if "보통주" in nm else 1,       # 보통주 명시 우선
            0 if "기본" in nm else 1,         # 기본(basic) 우선
            1 if "계속영업" in nm else 0,     # 계속영업이익은 후순위(총 주당이익 우선)
        )

    for r in sorted(cands, key=rank):
        v = clean_number(r.get("thstrm_amount"))
        if v is not None:
            return v, r.get("account_nm"), r.get("rcept_no")

    return None, None, None


def _sum_debt(rows: list[dict]) -> float | None:
    """차입금 합계. 하나도 못 찾으면 None (**0 아님** — '무차입'과 '미확인'을 구분한다)."""
    total = None
    for r in rows:
        if (r.get("sj_div") or "") != "BS":
            continue
        acc = (r.get("account_nm") or "").strip()
        if any(d in acc for d in DEBT_NAMES):
            v = clean_number(r.get("thstrm_amount"))
            if v is not None:
                total = (total or 0.0) + v
    return total


def extract_report(rec: dict) -> dict:
    """한 보고서(연도+reprt_code)에서 표준 계정을 뽑는다. 값이 없으면 None 유지."""
    rows = rec["rows"]
    out: dict = {
        "bsns_year": rec["bsns_year"],
        "reprt_code": rec["reprt_code"],
        "reprt_label": rec["reprt_label"],
        "fs_div": rec["fs_div"],
        "rcept_no": rec["rcept_no"],
        "currency": rec.get("currency"),
        "accounts": {},
    }
    for key, spec in ACCOUNTS.items():
        v, acc_nm, rcept = _pick(rows, spec)
        out["accounts"][key] = {
            "value": v,
            "account_nm": acc_nm,
            "rcept_no": rcept or rec["rcept_no"],
            "flow": spec["flow"],
        }
    debt = _sum_debt(rows)
    out["accounts"]["total_debt"] = {
        "value": debt,
        "account_nm": "차입금 합계 (단기+장기+사채)" if debt is not None else None,
        "rcept_no": rec["rcept_no"],
        "flow": False,
    }
    return out


def derive_standalone_quarters(
    annual: list[dict], quarterly: list[dict]
) -> list[dict]:
    """누적 보고서를 차분해 분기 단독값을 만든다.

    반환 항목의 period_type 은 모두 'quarter_standalone' 이다.
    차분에 필요한 인접 보고서가 없으면 그 분기는 생성하지 않는다 (N/A → 존재하지 않음).
    """
    # (year, reprt_code) → 추출된 보고서
    by_key: dict[tuple[int, str], dict] = {}
    for rec in quarterly + annual:
        by_key[(rec["bsns_year"], rec["reprt_code"])] = rec

    years = sorted({y for (y, _) in by_key})
    results: list[dict] = []

    # 분기 → (당해 누적 보고서, 직전 누적 보고서). 직전이 None 이면 차분 없이 그대로 사용.
    quarter_defs = [
        (1, REPRT_Q1, None),
        (2, REPRT_HALF, REPRT_Q1),
        (3, REPRT_Q3, REPRT_HALF),
        (4, REPRT_ANNUAL, REPRT_Q3),
    ]

    for year in years:
        for q, cur_code, prev_code in quarter_defs:
            cur = by_key.get((year, cur_code))
            if not cur:
                continue
            prev = by_key.get((year, prev_code)) if prev_code else None
            if prev_code and not prev:
                # 직전 누적이 없으면 차분 불가 → 이 분기는 만들지 않는다 (0 으로 채우지 않는다)
                continue

            acc: dict = {}
            for key, spec in ACCOUNTS.items():
                cur_a = cur["accounts"][key]
                if not spec["flow"]:
                    # 시점 항목: 차분하지 않고 당해 누적 보고서의 값을 그대로 쓴다
                    acc[key] = {
                        "value": cur_a["value"],
                        "derivation": "point_in_time",
                        "rcept_no": cur_a["rcept_no"],
                        "input_rcept_nos": [cur_a["rcept_no"]] if cur_a["rcept_no"] else [],
                    }
                    continue

                if prev is None:
                    # 1분기: 누적 = 단독
                    acc[key] = {
                        "value": cur_a["value"],
                        "derivation": "q1_cumulative_equals_standalone",
                        "rcept_no": cur_a["rcept_no"],
                        "input_rcept_nos": [cur_a["rcept_no"]] if cur_a["rcept_no"] else [],
                    }
                    continue

                prev_a = prev["accounts"][key]
                if cur_a["value"] is None or prev_a["value"] is None:
                    acc[key] = {
                        "value": None,
                        "derivation": "unavailable",
                        "na_reason": "누적 차분에 필요한 값이 결측 (0 으로 대체하지 않음)",
                        "rcept_no": cur_a["rcept_no"],
                        "input_rcept_nos": [],
                    }
                    continue

                acc[key] = {
                    "value": cur_a["value"] - prev_a["value"],
                    "derivation": "cumulative_difference",
                    "formula": (
                        f"{cur['reprt_label']}({year}) 누적 − {prev['reprt_label']}({year}) 누적"
                    ),
                    "inputs": {"cumulative_current": cur_a["value"],
                               "cumulative_previous": prev_a["value"]},
                    "rcept_no": cur_a["rcept_no"],
                    "input_rcept_nos": [
                        r for r in (cur_a["rcept_no"], prev_a["rcept_no"]) if r
                    ],
                }

            results.append({
                "year": year,
                "quarter": q,
                "period_label": f"{year}Q{q}",
                "period_type": "quarter_standalone",
                "fs_div": cur["fs_div"],
                "source_reprt_code": cur_code,
                "accounts": acc,
            })

    results.sort(key=lambda r: (r["year"], r["quarter"]))
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="원시 데이터 정규화 + 누적→분기단독 차분")
    ap.add_argument("ticker")
    args = ap.parse_args()

    try:
        ticker = validate_ticker(args.ticker)

        fin = read_json(raw_path(ticker, "dart_financials"))
        profile = read_json(raw_path(ticker, "dart_profile"))

        annual = [extract_report(r) for r in fin["annual"]]
        quarterly_cum = [extract_report(r) for r in fin["quarterly"]]
        log(f"연간 {len(annual)}개 / 분기 누적 {len(quarterly_cum)}개 추출")

        standalone = derive_standalone_quarters(annual, quarterly_cum)
        log(f"분기 단독값 {len(standalone)}개 파생 (누적 차분)")

        if standalone:
            latest = standalone[-1]
            rev = latest["accounts"]["revenue"]["value"]
            log(f"최근 분기: {latest['period_label']} 매출 "
                f"{f'{rev:,.0f}' if rev is not None else 'N/A'} "
                f"({latest['accounts']['revenue']['derivation']})")

        # 시세
        market = read_json(raw_path(ticker, "krx_market"))

        result = {
            "ticker": ticker,
            "fs_div": fin["fs_div"],
            "fs_div_fallback": fin["fs_div_fallback"],
            "fs_div_note": fin["fs_div_note"],
            "currency": next(
                (a.get("currency") for a in annual if a.get("currency")), "KRW"),
            "shares": profile["shares"],
            "annual": annual,
            "quarterly_cumulative": quarterly_cum,
            "quarterly_standalone": standalone,
            "market": {
                "as_of": market["as_of"],
                "close": market["ohlcv"]["series"][-1]["close"],
                "series": market["ohlcv"]["series"],
                "investor_flow": market.get("investor_flow"),
                "index": market.get("index"),
                "krx_published_valuation": market.get("krx_published_valuation"),
                "krx_market_cap_crosscheck": market.get("krx_market_cap_crosscheck"),
                "krx_login_available": market.get("krx_login_available"),
            },
            "derivation_notes": [
                "분기 단독값은 연속 누적 보고서 차분으로 파생했다 (thstrm_add_amount 미사용).",
                "재무상태표(BS)는 시점값이므로 차분하지 않았다.",
                "차분에 필요한 인접 보고서가 없는 분기는 생성하지 않았다 (0 으로 대체하지 않음).",
                f"재무 기준: {fin['fs_div']}"
                + (" (연결 부재로 별도 폴백)" if fin["fs_div_fallback"] else ""),
            ],
            "normalized_at": now_iso(),
        }

        out = write_json(normalized_path(ticker), result)
        print(f"저장: {out}")
        print(f"  연간 {len(annual)} / 분기단독 {len(standalone)} / 기준 {fin['fs_div']}")

    except SkillError as e:
        die(str(e))


if __name__ == "__main__":
    main()
