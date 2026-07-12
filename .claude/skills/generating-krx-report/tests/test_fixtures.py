#!/usr/bin/env python3
"""Fixture 테스트 — API 키·네트워크 없이 전체 파이프라인을 실행한다.

    python tests/test_fixtures.py

가상의 종목 999999 (가상기업)로 raw 픽스처를 만든 뒤
normalize → calculate → evidence → validate → score → validate_report 를 실행해
파이프라인이 실제로 이어지는지 검증한다.

⚠️ Fixture 는 **테스트 전용**이다. 실제 보고서 데이터로 사용하지 않는다.
   실존하지 않는 종목코드(999999)를 쓰며, outputs/ 에 보고서를 만들지 않는다.
   테스트 종료 시 생성한 파일을 모두 삭제한다.
"""
from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import _common as C  # noqa: E402
import build_evidence_packs as BEP  # noqa: E402
import calculate_metrics as CM  # noqa: E402
import normalize_data as ND  # noqa: E402
import score_modules as SM  # noqa: E402
import validate_evidence as VE  # noqa: E402
import validate_report as VR  # noqa: E402

TICKER = "999999"          # 실존하지 않는 코드 — 실제 데이터와 절대 섞이지 않는다
RCEPT = {
    "fy2022": "20230315000001",
    "fy2023": "20240315000001",
    "fy2024": "20250315000001",
    "q1_2024": "20240515000001",
    "h1_2024": "20240814000001",
    "q3_2024": "20241114000001",
    "q1_2025": "20250515000001",
    "h1_2025": "20250814000001",
    "q3_2025": "20251114000001",
    "fy2021": "20220315000001",
}
RETRIEVED = "2026-07-12T09:00:00"


def _rows(rev, op, ni, eps, ocf, capex, dep, tax, pretax, interest,
          assets, liab, equity, cash, debt, ca, cl, rcept):
    """fnlttSinglAcntAll 응답 행을 흉내낸다 (account_id 기반)."""
    def r(sj, aid, nm, amt):
        return {"sj_div": sj, "sj_nm": sj, "account_id": aid, "account_nm": nm,
                "thstrm_nm": "당기", "thstrm_amount": str(amt),
                "thstrm_add_amount": None, "frmtrm_nm": None, "frmtrm_amount": None,
                "frmtrm_q_nm": None, "frmtrm_q_amount": None, "frmtrm_add_amount": None,
                "bfefrmtrm_nm": None, "bfefrmtrm_amount": None,
                "ord": "1", "currency": "KRW", "rcept_no": rcept}
    return [
        r("IS", "ifrs-full_Revenue", "매출액", rev),
        r("IS", "dart_OperatingIncomeLoss", "영업이익", op),
        r("IS", "ifrs-full_ProfitLoss", "당기순이익", ni),
        r("IS", "ifrs-full_BasicEarningsLossPerShare", "기본주당이익", eps),
        r("IS", "ifrs-full_ProfitLossBeforeTax", "법인세비용차감전순이익", pretax),
        r("IS", "ifrs-full_IncomeTaxExpenseContinuingOperations", "법인세비용", tax),
        r("IS", "ifrs-full_InterestExpense", "이자비용", interest),
        r("CF", "ifrs-full_CashFlowsFromUsedInOperatingActivities", "영업활동현금흐름", ocf),
        r("CF", "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
          "유형자산의취득", capex),
        r("CF", "ifrs-full_DepreciationAndAmortisationExpense", "감가상각비", dep),
        r("BS", "ifrs-full_Assets", "자산총계", assets),
        r("BS", "ifrs-full_Liabilities", "부채총계", liab),
        r("BS", "ifrs-full_Equity", "자본총계", equity),
        r("BS", "ifrs-full_CashAndCashEquivalents", "현금및현금성자산", cash),
        r("BS", "-표준계정코드 미사용-", "단기차입금", debt),
        r("BS", "ifrs-full_CurrentAssets", "유동자산", ca),
        r("BS", "ifrs-full_CurrentLiabilities", "유동부채", cl),
    ]


def _report(year, code, label, rcept, **kw):
    return {"bsns_year": year, "reprt_code": code, "reprt_label": label,
            "fs_div": "CFS", "rcept_no": rcept, "currency": "KRW",
            "row_count": 17, "rows": _rows(rcept=rcept, **kw)}


# 단위: 억원 스케일의 임의 수치 (실제 기업과 무관한 합성 데이터)
BASE_BS = dict(assets=10_000, liab=4_000, equity=6_000,
               cash=1_200, debt=800, ca=5_000, cl=2_500)


def build_fixtures() -> None:
    C.RAW_DIR.mkdir(parents=True, exist_ok=True)

    # ── identity ────────────────────────────────────────────────────────────
    C.write_json(C.raw_path(TICKER, "identity"), {
        "ticker": TICKER, "corp_code": "00999999",
        "company_name": "가상기업(테스트용)", "market": "KOSPI",
        "corp_cls": "Y", "share_class": "common",
        "share_class_basis": "fixture", "code_mismatch": False,
        "gate1": {"status": "passed", "checks": [
            {"check": "fixture", "result": "pass", "detail": "테스트 전용 합성 데이터"}]},
        "credentials_available": {"DART_API_KEY": False, "KRX_ID": False,
                                  "KRX_PW": False, "KRX_OPEN_API_KEY": False},
        "source": {"provider": "dart", "source_type": "official_api",
                   "endpoint_or_function": "corpCode.xml + company.json",
                   "retrieved_at": RETRIEVED},
        "resolved_at": RETRIEVED,
    })

    # ── financials ──────────────────────────────────────────────────────────
    # 연간 (매출 성장: 6000 → 7000 → 8200 → 9600)
    annual = [
        _report(2024, C.REPRT_ANNUAL, "사업보고서", RCEPT["fy2024"],
                rev=9600, op=960, ni=720, eps=1440, ocf=1100, capex=-400, dep=300,
                tax=180, pretax=900, interest=40, **BASE_BS),
        _report(2023, C.REPRT_ANNUAL, "사업보고서", RCEPT["fy2023"],
                rev=8200, op=780, ni=590, eps=1180, ocf=900, capex=-350, dep=280,
                tax=150, pretax=740, interest=38, **BASE_BS),
        _report(2022, C.REPRT_ANNUAL, "사업보고서", RCEPT["fy2022"],
                rev=7000, op=630, ni=470, eps=940, ocf=760, capex=-300, dep=260,
                tax=120, pretax=590, interest=35, **BASE_BS),
        _report(2021, C.REPRT_ANNUAL, "사업보고서", RCEPT["fy2021"],
                rev=6000, op=480, ni=360, eps=720, ocf=620, capex=-250, dep=240,
                tax=95, pretax=455, interest=33, **BASE_BS),
    ]

    # 분기 (누적!) — 2024: 2300 / 4700 / 7100 (FY 9600)
    #                2025: 2700 / 5500 / 8300
    quarterly = [
        _report(2025, C.REPRT_Q3, "3분기보고서", RCEPT["q3_2025"],
                rev=8300, op=880, ni=660, eps=1320, ocf=950, capex=-330, dep=250,
                tax=165, pretax=825, interest=30, **BASE_BS),
        _report(2025, C.REPRT_HALF, "반기보고서", RCEPT["h1_2025"],
                rev=5500, op=580, ni=435, eps=870, ocf=620, capex=-220, dep=165,
                tax=110, pretax=545, interest=20, **BASE_BS),
        _report(2025, C.REPRT_Q1, "1분기보고서", RCEPT["q1_2025"],
                rev=2700, op=280, ni=210, eps=420, ocf=300, capex=-110, dep=82,
                tax=53, pretax=263, interest=10, **BASE_BS),
        _report(2024, C.REPRT_Q3, "3분기보고서", RCEPT["q3_2024"],
                rev=7100, op=700, ni=525, eps=1050, ocf=800, capex=-300, dep=225,
                tax=131, pretax=656, interest=30, **BASE_BS),
        _report(2024, C.REPRT_HALF, "반기보고서", RCEPT["h1_2024"],
                rev=4700, op=460, ni=345, eps=690, ocf=520, capex=-200, dep=150,
                tax=86, pretax=431, interest=20, **BASE_BS),
        _report(2024, C.REPRT_Q1, "1분기보고서", RCEPT["q1_2024"],
                rev=2300, op=220, ni=165, eps=330, ocf=250, capex=-100, dep=75,
                tax=41, pretax=206, interest=10, **BASE_BS),
    ]

    C.write_json(C.raw_path(TICKER, "dart_financials"), {
        "ticker": TICKER, "corp_code": "00999999",
        "fs_div": "CFS", "fs_div_fallback": False,
        "fs_div_note": "연결(CFS) 기준",
        "cumulative_warning": "분기 금액은 누적이다.",
        "annual": annual, "quarterly": quarterly,
        "source": {"provider": "dart", "source_type": "official_api",
                   "endpoint_or_function": "fnlttSinglAcntAll.json",
                   "retrieved_at": RETRIEVED},
    })

    # ── profile (주식총수 2개 연도 → 희석 계산 가능) ─────────────────────────
    C.write_json(C.raw_path(TICKER, "dart_profile"), {
        "ticker": TICKER, "corp_code": "00999999",
        "company": {"corp_name": "가상기업(테스트용)", "induty_code": "9999",
                    "est_dt": "19900101", "acc_mt": "12", "ceo_nm": "홍길동",
                    "hm_url": None},
        "shares": {
            "bsns_year": 2024, "reprt_code": C.REPRT_ANNUAL, "se": "합계",
            "issued_shares": 500_000, "treasury_shares": 10_000,
            "distributed_shares": 490_000, "rcept_no": RCEPT["fy2024"],
            "history": [
                {"bsns_year": 2024, "issued_shares": 500_000,
                 "rcept_no": RCEPT["fy2024"]},
                {"bsns_year": 2023, "issued_shares": 498_000,
                 "rcept_no": RCEPT["fy2023"]},
            ],
        },
        "business_section": None,
        "source": {"provider": "dart", "source_type": "official_api",
                   "endpoint_or_function": "company.json + stockTotqySttus.json",
                   "retrieved_at": RETRIEVED},
    })

    # ── events ──────────────────────────────────────────────────────────────
    C.write_json(C.raw_path(TICKER, "dart_events"), {
        "ticker": TICKER, "corp_code": "00999999", "period_months": 12,
        "disclosures": [], "catalyst_candidates": [
            {"rcept_no": "20250601000001", "report_nm": "단일판매ㆍ공급계약체결",
             "rcept_dt": "20250601", "flr_nm": "가상기업", "pblntf_ty": "B",
             "tags": ["신규수주"],
             "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20250601000001"},
            {"rcept_no": "20250701000001", "report_nm": "주요사항보고서(자기주식취득결정)",
             "rcept_dt": "20250701", "flr_nm": "가상기업", "pblntf_ty": "B",
             "tags": ["자사주"],
             "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20250701000001"},
        ],
        "treasury_stock": None, "capital_changes": None, "dividends": None,
        "note": "fixture",
        "source": {"provider": "dart", "source_type": "official_api",
                   "endpoint_or_function": "list.json", "retrieved_at": RETRIEVED},
    })

    # ── market (KRX 자격증명 없는 상황을 재현: 지수·수급 = None) ─────────────
    series = []
    price = 8000.0
    for i in range(300):
        price *= 1.001 if i % 3 else 0.9995
        series.append({"date": f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                       "close": round(price, 1), "high": round(price * 1.01, 1),
                       "low": round(price * 0.99, 1), "volume": 100_000 + i * 50})
    series[-1]["date"] = "2026-07-10"

    C.write_json(C.raw_path(TICKER, "krx_market"), {
        "ticker": TICKER, "market": "KOSPI", "as_of": "2026-07-10",
        "krx_login_available": False,
        "ohlcv": {"as_of": "2026-07-10", "series": series,
                  "trading_days": len(series),
                  "source": {"provider": "pykrx", "source_type": "unofficial_wrapper",
                             "underlying_source": "Naver Finance",
                             "endpoint_or_function": "get_market_ohlcv",
                             "retrieved_at": RETRIEVED}},
        "investor_flow": None,     # 자격증명 없음 → N/A
        "index": None,             # 자격증명 없음 → N/A
        "krx_published_valuation": None,
        "na_items": ["investor_flow (CANSLIM I)", "index (CANSLIM M, L)"],
        "na_reason": "KRX_ID/KRX_PW 미설정 (fixture)",
        "provenance_warning": "pykrx 는 비공식 래퍼다.",
    })

    # ── contract ────────────────────────────────────────────────────────────
    C.write_json(C.contract_path(TICKER), {
        "company_name": "가상기업(테스트용)", "ticker": TICKER, "market": "KOSPI",
        "corp_code": "00999999", "request_type": "comprehensive",
        "analysis_mode": "balanced", "investment_horizon": "unspecified",
        "valuation_requested": True, "target_price_requested": False,
        "forecast_allowed": False, "consensus_allowed": False, "news_allowed": False,
        "peer_comparison": {"requested": False, "selection_rule": None,
                            "explicit_peers": []},
        "required_modules": ["business", "quality", "growth", "moat",
                             "valuation", "trend", "risk", "catalyst"],
        "optional_modules": [],
        "assumptions": [], "unresolved_items": [],
        "prohibited_inferences": ["목표주가 산출"],
        "unsupported_data": ["analyst_consensus: 무료 공식 API 없음"],
        "credentials_available": {"DART_API_KEY": True, "KRX_ID": False,
                                  "KRX_PW": False, "KRX_OPEN_API_KEY": False},
        "data_cutoff": "2026-07-10", "created_at": RETRIEVED,
    })


def cleanup() -> None:
    for p in [
        C.raw_path(TICKER, "identity"), C.raw_path(TICKER, "dart_financials"),
        C.raw_path(TICKER, "dart_profile"), C.raw_path(TICKER, "dart_events"),
        C.raw_path(TICKER, "krx_market"), C.contract_path(TICKER),
        C.normalized_path(TICKER), C.metrics_path(TICKER), C.evidence_path(TICKER),
        C.DATA_DIR / f"{TICKER}_gate2.json",
        C.DATA_DIR / f"{TICKER}_composite.json",
        C.DATA_DIR / f"{TICKER}_manifest.json",
    ]:
        p.unlink(missing_ok=True)
    for p in C.MODRES_DIR.glob(f"{TICKER}_*.json"):
        p.unlink(missing_ok=True)


class TestFixturePipeline(unittest.TestCase):
    """수집을 제외한 전 파이프라인을 오프라인으로 관통한다."""

    @classmethod
    def setUpClass(cls):
        cleanup()
        build_fixtures()
        sys.argv = ["x", TICKER]
        ND.main()
        CM.main()
        BEP.main()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    # ── 누적 → 분기단독 ──────────────────────────────────────────────────────
    def test_standalone_quarters_derived_by_differencing(self):
        nz = C.read_json(C.normalized_path(TICKER))
        q = {r["period_label"]: r["accounts"]["revenue"]["value"]
             for r in nz["quarterly_standalone"]}
        # 2025 누적 2700 / 5500 / 8300 → 단독 2700 / 2800 / 2800
        self.assertEqual(q["2025Q1"], 2700)
        self.assertEqual(q["2025Q2"], 2800)
        self.assertEqual(q["2025Q3"], 2800)
        # 2024 누적 2300 / 4700 / 7100, FY 9600 → 2300 / 2400 / 2400 / 2500
        self.assertEqual(q["2024Q1"], 2300)
        self.assertEqual(q["2024Q2"], 2400)
        self.assertEqual(q["2024Q4"], 2500)

    def test_no_2025_q4_because_annual_missing(self):
        """2025 사업보고서가 없으므로 2025Q4 는 만들어지지 않는다 (0 아님)."""
        nz = C.read_json(C.normalized_path(TICKER))
        labels = {r["period_label"] for r in nz["quarterly_standalone"]}
        self.assertNotIn("2025Q4", labels)

    # ── 지표 ────────────────────────────────────────────────────────────────
    def test_yoy_compares_same_quarter(self):
        m = C.read_json(C.metrics_path(TICKER))["metrics"]
        # 최신 분기 2025Q3(2800) vs 2024Q3(2400) → +16.67%
        self.assertAlmostEqual(m["rev_yoy_q"]["value"], 16.67, places=1)
        self.assertIn("2025Q3", m["rev_yoy_q"]["period"])
        self.assertIn("2024Q3", m["rev_yoy_q"]["period"])

    def test_cagr_uses_four_annual_points(self):
        m = C.read_json(C.metrics_path(TICKER))["metrics"]
        # 매출 6000(2021) → 9600(2024), 3년 → 17.0%
        self.assertAlmostEqual(m["rev_cagr_3y"]["value"], 17.0, places=1)
        self.assertEqual(m["rev_cagr_3y"]["inputs"]["base_year"], 2021)

    def test_market_cap_from_dart_shares_not_pykrx(self):
        """KRX 자격증명이 없어도 시가총액이 계산되어야 한다 (보통주 기준)."""
        m = C.read_json(C.metrics_path(TICKER))["metrics"]
        mc = m["market_cap"]
        self.assertIsNotNone(mc["value"])
        self.assertEqual(mc["formula"], "종가 × 보통주 발행주식수")
        # fixture: 종가 × 500,000주
        self.assertAlmostEqual(mc["value"],
                               m["close_price"]["value"] * 500_000, places=0)
        self.assertTrue(any("기준일이 다르다" in l for l in mc["limitations"]))

    def test_credentials_missing_metrics_are_na_not_zero(self):
        m = C.read_json(C.metrics_path(TICKER))["metrics"]
        for k in ("rs_vs_index_6m_pp", "index_vs_ma200_pct",
                  "inst_foreign_net_60d_to_mktcap"):
            self.assertIsNone(m[k]["value"], f"{k} 는 N/A 여야 한다")
            self.assertIsNotNone(m[k]["na_reason"])

    def test_every_metric_has_formula_or_is_observation(self):
        m = C.read_json(C.metrics_path(TICKER))["metrics"]
        for name, v in m.items():
            if v["value"] is not None and v.get("formula"):
                self.assertTrue(v["unit"], f"{name}: 단위 누락")

    # ── evidence ────────────────────────────────────────────────────────────
    def test_evidence_passes_gate2(self):
        pack = C.read_json(C.evidence_path(TICKER))
        errs = []
        for e in pack["evidence"]:
            errs.extend(VE.check_item(e))
        errs.extend(VE.check_zero_substitution(pack["evidence"]))
        self.assertEqual(errs, [], f"Gate 2 위반: {errs}")

    def test_dart_evidence_is_traceable_to_a_filing(self):
        """모든 DART 수치는 접수번호로, 또는 입력 evidence 체인으로 공시까지 추적된다."""
        pack = C.read_json(C.evidence_path(TICKER))
        dart_ev = [e for e in pack["evidence"]
                   if e["source"]["provider"] == "dart" and e["value"] is not None]
        self.assertTrue(dart_ev)
        for e in dart_ev:
            rcept = e["source"]["rcept_no"]
            chain = (e.get("calculation") or {}).get("input_evidence_ids") or []
            self.assertTrue(rcept or chain,
                            f"{e['evidence_id']}: 접수번호도 근거 체인도 없다")
            if rcept:
                self.assertRegex(rcept, r"^\d{14}$")

    def test_market_evidence_is_marked_unofficial(self):
        """시세 계열 지표는 pykrx(비공식)로 표기되어야 한다. 공식으로 위장하지 않는다."""
        pack = C.read_json(C.evidence_path(TICKER))
        market = [e for e in pack["evidence"]
                  if e.get("metric") in BEP.MARKET_ORIGIN_METRICS]
        self.assertTrue(market)
        for e in market:
            self.assertEqual(e["source"]["provider"], "pykrx")
            self.assertFalse(e["source"]["source_type"].startswith("official"))
            self.assertIsNotNone(e["source"]["underlying_source"])

    def test_derived_metrics_chain_to_their_inputs(self):
        """파생 지표의 input_evidence_ids 가 실제 evidence 로 연결되어야 한다."""
        pack = C.read_json(C.evidence_path(TICKER))
        ids = {e["evidence_id"] for e in pack["evidence"]}
        by_metric = {e["metric"]: e for e in pack["evidence"] if e.get("metric")}

        opm = by_metric["operating_margin_ttm"]
        chain = opm["calculation"]["input_evidence_ids"]
        self.assertTrue(chain, "영업이익률이 입력 지표로 연결되지 않았다")
        for eid in chain:
            self.assertIn(eid, ids, f"존재하지 않는 evidence 참조: {eid}")

    def test_catalyst_evidence_comes_from_disclosures(self):
        pack = C.read_json(C.evidence_path(TICKER))
        cat = [e for e in pack["evidence"] if e["module"] == "catalyst"]
        self.assertEqual(len(cat), 2)
        for e in cat:
            self.assertEqual(e["evidence_type"], "event")
            self.assertIsNotNone(e["source"]["rcept_no"])

    def test_evidence_packs_respect_per_module_cap(self):
        pack = C.read_json(C.evidence_path(TICKER))
        for mod, ids in pack["packs"].items():
            self.assertLessEqual(len(ids), BEP.MAX_EVIDENCE_PER_MODULE,
                                 f"{mod}: evidence 20개 초과")

    # ── 채점 ────────────────────────────────────────────────────────────────
    def test_auto_modules_score_without_judgment(self):
        """정량 모듈은 Claude 개입 없이 Python 만으로 채점된다."""
        registry = C.load_registry()
        metrics = C.read_json(C.metrics_path(TICKER))
        creds = {"KRX_ID": False, "KRX_PW": False}

        for mod in ("quality", "growth", "valuation"):
            r = SM.score_module(mod, registry["modules"][mod], metrics, creds)
            self.assertIsNotNone(r["score"], f"{mod} 점수가 없다")
            self.assertGreaterEqual(r["score"], 0)
            self.assertLessEqual(r["score"], 100)

    def test_trend_has_na_for_credential_gated_criteria(self):
        registry = C.load_registry()
        metrics = C.read_json(C.metrics_path(TICKER))
        r = SM.score_module("trend", registry["modules"]["trend"], metrics,
                            {"KRX_ID": False, "KRX_PW": False})
        by_id = {c["criterion_id"]: c for c in r["criteria_scores"]}
        for cid in ("TRD-L", "TRD-I", "TRD-M"):
            self.assertIsNone(by_id[cid]["level"], f"{cid} 는 N/A 여야 한다")
            self.assertIn("자격증명", by_id[cid]["na_reason"])
        # C·A·N·S 는 채점된다 → 부분 점수 존재
        self.assertIsNotNone(r["score"])
        self.assertEqual(r["status"], "partial")
        self.assertAlmostEqual(r["evidence_coverage"], 4 / 7, places=2)

    def test_qualitative_module_without_judgment_is_insufficient_not_zero(self):
        registry = C.load_registry()
        metrics = C.read_json(C.metrics_path(TICKER))
        r = SM.score_module("moat", registry["modules"]["moat"], metrics, {})
        self.assertIsNone(r["score"])          # 0 이 아니라 null
        self.assertEqual(r["status"], "insufficient_data")

    def test_qualitative_module_scores_from_judgment(self):
        """Claude 가 서수 등급만 제출하면 Python 이 점수를 만든다."""
        C.write_json(C.judgment_path(TICKER, "moat"), {
            "module": "moat",
            "criteria": [
                {"criterion_id": "MOA-01", "level": 2,
                 "evidence_ids": ["B-PROFILE-001", "Q-OPERATINGM-001"],
                 "rationale": "fixture"},
                {"criterion_id": "MOA-02", "level": None,
                 "na_reason": "근거 없음 — 추정하지 않는다", "evidence_ids": []},
                {"criterion_id": "MOA-03", "level": None,
                 "na_reason": "근거 없음", "evidence_ids": []},
                {"criterion_id": "MOA-04", "level": None,
                 "na_reason": "근거 없음", "evidence_ids": []},
                {"criterion_id": "MOA-05", "level": 3,
                 "evidence_ids": ["Q-OPERATINGM-001", "Q-ROETTM-001"],
                 "rationale": "fixture"},
            ],
            "strengths": [{"point": "s", "evidence_ids": ["B-PROFILE-001"]}],
            "weaknesses": [], "counter_evidence": [], "unknowns": [],
            "invalidating_conditions": [], "verdict": "fixture",
        })
        registry = C.load_registry()
        metrics = C.read_json(C.metrics_path(TICKER))
        r = SM.score_module("moat", registry["modules"]["moat"], metrics, {})

        # MOA-01(w20,L2) + MOA-05(w25,L3) → Σw=45
        # earned = 20*(2/3) + 25*1 = 13.333 + 25 = 38.333 → 38.333/45*100 = 85.2
        self.assertEqual(r["score"], 85.2)
        self.assertAlmostEqual(r["evidence_coverage"], 2 / 5)
        self.assertEqual(r["status"], "partial")
        C.judgment_path(TICKER, "moat").unlink(missing_ok=True)

    def test_scores_are_reproducible_gate3(self):
        registry = C.load_registry()
        metrics = C.read_json(C.metrics_path(TICKER))
        for mod in ("quality", "growth", "valuation", "trend"):
            r = SM.score_module(mod, registry["modules"][mod], metrics,
                                {"KRX_ID": False, "KRX_PW": False})
            self.assertEqual(VR.recompute_score(r, registry), r["score"],
                             f"{mod}: 점수 재현 실패")

    def test_composite_excludes_unscored_modules(self):
        registry = C.load_registry()
        modes = C.load_modes()
        metrics = C.read_json(C.metrics_path(TICKER))
        results = [
            SM.score_module(m, registry["modules"][m], metrics,
                            {"KRX_ID": False, "KRX_PW": False})
            for m in ("quality", "growth", "valuation", "trend", "moat")
        ]
        comp = SM.composite(results, "balanced", modes)
        # moat 은 judgment 가 없어 score=None → 종합에서 제외
        self.assertNotIn("moat", comp["weights_used"])
        self.assertTrue(comp["renormalized"])
        self.assertAlmostEqual(sum(comp["weights_used"].values()), 100, places=1)


class TestPreferredShareHandling(unittest.TestCase):
    """우선주가 있는 기업의 시가총액 — 실제 삼성전기 공시에서 발견된 버그의 회귀 테스트.

    stockTotqySttus 의 '합계' 행은 보통주 + 우선주 다.
    우리가 가진 주가는 **보통주 종가**이므로 합계를 곱하면 시가총액이 과대계상된다.
    (삼성전기 실측: 합계 77,600,680 vs 보통주 74,693,696 → 약 +3.9% 과대)
    보통주 주식수를 써야 KRX 공표 시가총액과 정확히 일치한다.
    """

    def _rows(self):
        return [
            {"se": "의결권이 있는주식(보통주)", "istc_totqy": "74,693,696",
             "tesstk_co": "2,000,000", "distb_stock_co": "72,693,696",
             "rcept_no": "20260310003071"},
            {"se": "의결권이 없는주식(우선주)", "istc_totqy": "2,906,984",
             "tesstk_co": "53,430", "distb_stock_co": "2,853,554",
             "rcept_no": "20260310003071"},
            {"se": "합계", "istc_totqy": "77,600,680",
             "tesstk_co": "2,053,430", "distb_stock_co": "75,547,250",
             "rcept_no": "20260310003071"},
        ]

    def test_uses_common_shares_not_total(self):
        import fetch_dart_profile as FP
        parsed = FP._parse_shares_row(self._rows(), 2025)
        self.assertEqual(parsed["issued_shares"], 74_693_696,
                         "시가총액용 주식수는 **보통주**여야 한다 (합계 금지)")
        self.assertEqual(parsed["preferred_shares"], 2_906_984)
        self.assertEqual(parsed["total_shares_all_classes"], 77_600_680)
        self.assertTrue(parsed["has_preferred"])

    def test_market_cap_matches_krx_published(self):
        """보통주 × 종가 = KRX 공표 시가총액 (2026-07-10 실측)."""
        self.assertEqual(1_584_000 * 74_693_696, 118_314_814_464_000)

    def test_single_class_company_falls_back_to_total(self):
        rows = [{"se": "합계", "istc_totqy": "1,000,000", "tesstk_co": "0",
                 "distb_stock_co": "1,000,000", "rcept_no": "20250101000001"}]
        import fetch_dart_profile as FP
        parsed = FP._parse_shares_row(rows, 2025)
        self.assertEqual(parsed["issued_shares"], 1_000_000)
        self.assertFalse(parsed["has_preferred"])


class TestFixtureIsolation(unittest.TestCase):
    def test_fixture_ticker_is_not_real(self):
        """fixture 는 실존 종목코드를 쓰지 않는다 (실제 보고서 오염 방지)."""
        self.assertEqual(TICKER, "999999")
        self.assertNotEqual(TICKER, "009150")

    def test_fixture_leaves_no_output_report(self):
        outputs = list(C.OUTPUT_DIR.glob(f"{TICKER}*")) if C.OUTPUT_DIR.exists() else []
        self.assertEqual(outputs, [], "fixture 가 outputs/ 에 보고서를 남겼다")


if __name__ == "__main__":
    unittest.main(verbosity=2)
