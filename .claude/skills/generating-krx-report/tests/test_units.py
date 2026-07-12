#!/usr/bin/env python3
"""단위 테스트 — API 키·네트워크 없이 실행 가능.

    python tests/test_units.py

검증 대상 (Phase 14):
  - 종목코드 형식
  - DART corp_code 매핑
  - API 오류코드 처리 (013=데이터없음 vs 하드오류)
  - 누적값과 분기값 구분 (차분)
  - CAGR 음수 기준값 차단
  - PER 적자기업 차단
  - N/A 점수 제외
  - evidence ID 연결
  - 종합점수 계산
  - 분석 모드별 가중치 합계 100
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import _common as C  # noqa: E402
import calculate_metrics as CM  # noqa: E402
import normalize_data as ND  # noqa: E402
import score_modules as SM  # noqa: E402
import validate_evidence as VE  # noqa: E402
import validate_report as VR  # noqa: E402


class TestTickerFormat(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(C.validate_ticker("009150"), "009150")
        self.assertEqual(C.validate_ticker(" 005930 "), "005930")

    def test_invalid(self):
        for bad in ["9150", "0091500", "abcdef", "", "00915a", "00-915"]:
            with self.assertRaises(C.SkillError, msg=f"{bad!r} 는 거부되어야 한다"):
                C.validate_ticker(bad)


class TestDartStatusCodes(unittest.TestCase):
    """DART 는 오류도 HTTP 200 으로 준다. 본문 status 로 판정해야 한다."""

    def _resp(self, status: str) -> bytes:
        return json.dumps({"status": status, "message": "x", "list": []}).encode()

    def test_013_is_no_data_not_error(self):
        """013 은 '데이터 없음'이며 오류가 아니다. 0 으로 변환해서도 안 된다."""
        with patch.object(C, "_http_get", return_value=self._resp("013")), \
             patch.object(C, "require_dart_key", return_value="k"):
            with self.assertRaises(C.DartNoData):
                C.dart_get_json("fnlttSinglAcntAll.json", {})

    def test_hard_error_raises(self):
        for code in ("010", "011", "012", "100", "101"):
            with patch.object(C, "_http_get", return_value=self._resp(code)), \
                 patch.object(C, "require_dart_key", return_value="k"):
                with self.assertRaises(C.SkillError):
                    C.dart_get_json("company.json", {})

    def test_ok_returns_data(self):
        with patch.object(C, "_http_get", return_value=self._resp("000")), \
             patch.object(C, "require_dart_key", return_value="k"):
            d = C.dart_get_json("company.json", {})
            self.assertEqual(d["status"], "000")

    def test_api_key_is_redacted_in_errors(self):
        url = "https://opendart.fss.or.kr/api/x.json?crtfc_key=SECRET123&corp_code=1"
        self.assertNotIn("SECRET123", C._redact(url))


class TestCorpCodeMapping(unittest.TestCase):
    def test_maps_stock_code_and_skips_unlisted(self):
        xml = (
            "<result>"
            "<list><corp_code>00126380</corp_code><corp_name>삼성전자</corp_name>"
            "<stock_code>005930</stock_code><modify_date>20240101</modify_date></list>"
            "<list><corp_code>00999999</corp_code><corp_name>비상장사</corp_name>"
            "<stock_code> </stock_code><modify_date>20240101</modify_date></list>"
            "</result>"
        ).encode()

        class FakeZip:
            def namelist(self): return ["CORPCODE.xml"]
            def read(self, _): return xml

        # force_refresh=True 가 캐시 조회를 건너뛴다. 캐시 파일 쓰기만 막는다.
        with patch.object(C, "dart_get_zip", return_value=FakeZip()), \
             patch.object(C, "write_json", lambda *a, **k: None):
            m = C.load_corpcode_map(force_refresh=True)

        self.assertEqual(m["005930"]["corp_code"], "00126380")
        self.assertNotIn(" ", m)          # 비상장(stock_code 공백)은 제외
        self.assertEqual(len(m), 1)


class TestSafeArithmetic(unittest.TestCase):
    def test_safe_div_zero_denominator_is_none_not_zero(self):
        self.assertIsNone(C.safe_div(10, 0))
        self.assertIsNone(C.safe_div(10, None))
        self.assertIsNone(C.safe_div(None, 10))
        self.assertEqual(C.safe_div(10, 2), 5)

    def test_pct_change_blocks_nonpositive_base(self):
        """적자(음수) 기준 성장률은 왜곡이므로 None 이어야 한다."""
        self.assertIsNone(C.pct_change(100, -50))
        self.assertIsNone(C.pct_change(100, 0))
        self.assertAlmostEqual(C.pct_change(120, 100), 20.0)

    def test_cagr_blocks_negative_base_year(self):
        """음수 기준연도 CAGR 금지 (Gate 3)."""
        self.assertIsNone(C.cagr(200, -100, 3))
        self.assertIsNone(C.cagr(200, 0, 3))
        self.assertIsNone(C.cagr(-200, 100, 3))   # 최종값 음수도 정의 불가
        self.assertAlmostEqual(C.cagr(133.1, 100, 3), 10.0, places=4)

    def test_clean_number_missing_is_none_not_zero(self):
        """결측치를 0 으로 변환하지 않는다."""
        for v in ("-", "", None, "N/A"):
            self.assertIsNone(C.clean_number(v))
        self.assertEqual(C.clean_number("1,234"), 1234.0)
        self.assertEqual(C.clean_number("(500)"), -500.0)   # 회계 괄호 음수

    def test_assert_finite_blocks_nan(self):
        with self.assertRaises(C.SkillError):
            C.assert_finite({"a": float("nan")})
        with self.assertRaises(C.SkillError):
            C.assert_finite({"a": [float("inf")]})
        C.assert_finite({"a": 1.0, "b": None})   # 통과해야 함

    def test_is_future(self):
        self.assertTrue(C.is_future("2999-01-01"))
        self.assertFalse(C.is_future("2020-01-01"))
        self.assertFalse(C.is_future(None))


class TestCumulativeDifferencing(unittest.TestCase):
    """DART 분기 금액은 누적이다. 분기 단독값은 차분으로만 얻는다."""

    def _report(self, year, code, label, revenue, rcept):
        return {
            "bsns_year": year, "reprt_code": code, "reprt_label": label,
            "fs_div": "CFS", "rcept_no": rcept, "currency": "KRW",
            "accounts": {
                k: {"value": (revenue if k == "revenue" else None),
                    "account_nm": k, "rcept_no": rcept,
                    "flow": ND.ACCOUNTS[k]["flow"]}
                for k in ND.ACCOUNTS
            } | {"total_debt": {"value": None, "account_nm": None,
                                "rcept_no": rcept, "flow": False}},
        }

    def test_quarters_are_differenced(self):
        # 누적: Q1=100, 반기=250, 3Q=430, FY=600  →  단독: 100, 150, 180, 170
        annual = [self._report(2024, C.REPRT_ANNUAL, "사업보고서", 600, "20250301000001")]
        quarterly = [
            self._report(2024, C.REPRT_Q1, "1분기보고서", 100, "20240515000001"),
            self._report(2024, C.REPRT_HALF, "반기보고서", 250, "20240814000001"),
            self._report(2024, C.REPRT_Q3, "3분기보고서", 430, "20241114000001"),
        ]
        out = ND.derive_standalone_quarters(annual, quarterly)
        got = {r["period_label"]: r["accounts"]["revenue"]["value"] for r in out}

        self.assertEqual(got["2024Q1"], 100)
        self.assertEqual(got["2024Q2"], 150)
        self.assertEqual(got["2024Q3"], 180)
        self.assertEqual(got["2024Q4"], 170)
        self.assertTrue(all(r["period_type"] == "quarter_standalone" for r in out))

    def test_missing_adjacent_report_yields_no_quarter_not_zero(self):
        """인접 누적 보고서가 없으면 그 분기를 만들지 않는다. 0 으로 채우지 않는다."""
        annual = []
        quarterly = [self._report(2024, C.REPRT_Q3, "3분기보고서", 430, "r3")]
        out = ND.derive_standalone_quarters(annual, quarterly)
        # 반기 누적이 없으므로 Q3 단독을 만들 수 없다
        self.assertEqual([r["period_label"] for r in out], [])

    def test_q4_needs_annual_and_q3(self):
        annual = [self._report(2024, C.REPRT_ANNUAL, "사업보고서", 600, "ra")]
        quarterly = [self._report(2024, C.REPRT_Q3, "3분기보고서", 430, "r3")]
        out = ND.derive_standalone_quarters(annual, quarterly)
        got = {r["period_label"]: r["accounts"]["revenue"]["value"] for r in out}
        self.assertEqual(got.get("2024Q4"), 170)
        self.assertNotIn("2024Q3", got)   # 반기 누적 부재 → Q3 단독 불가

    def test_balance_sheet_is_not_differenced(self):
        annual = [self._report(2024, C.REPRT_ANNUAL, "사업보고서", 600, "ra")]
        quarterly = [
            self._report(2024, C.REPRT_Q1, "1분기보고서", 100, "r1"),
            self._report(2024, C.REPRT_HALF, "반기보고서", 250, "r2"),
        ]
        out = ND.derive_standalone_quarters(annual, quarterly)
        q2 = next(r for r in out if r["period_label"] == "2024Q2")
        self.assertEqual(q2["accounts"]["equity"]["derivation"], "point_in_time")
        self.assertEqual(q2["accounts"]["revenue"]["derivation"], "cumulative_difference")


class TestEpsCommonVsPreferred(unittest.TestCase):
    """보통주/우선주 EPS 혼동 방지 — 실제 삼성전기 공시에서 확인된 함정.

    과거 사업보고서는 EPS 행의 account_id 가 전부 '-표준계정코드 미사용-' 이라
    이름 매칭으로 넘어가는데, 보통주와 우선주 EPS 가 나란히 존재한다.
    우선주를 집으면 PER·EPS 성장률·CANSLIM C 가 전부 오염된다.
    """

    def _row(self, aid, nm, amt):
        return {"sj_div": "CIS", "account_id": aid, "account_nm": nm,
                "thstrm_amount": str(amt), "rcept_no": "20250315000001"}

    def test_prefers_common_over_preferred_when_ids_present(self):
        rows = [
            self._row("dart_BasicEarningsLossPerSharePreferredStock", "우선주기본주당이익", 9395),
            self._row("ifrs-full_BasicEarningsLossPerShare", "보통주기본주당이익", 9345),
        ]
        v, nm, _ = ND._pick(rows, ND.ACCOUNTS["eps"])
        self.assertEqual(v, 9345.0, "보통주 EPS 를 써야 한다")
        self.assertIn("보통주", nm)

    def test_excludes_preferred_when_account_id_is_unused(self):
        """2023 사업보고서 실제 형태: 모든 EPS 행의 account_id 가 미사용."""
        rows = [
            self._row("-표준계정코드 미사용-", "보통주 기본 및 희석주당이익", 5597),
            self._row("-표준계정코드 미사용-", "우선주 기본 및 희석주당이익", 5647),
            self._row("-표준계정코드 미사용-", "보통주 기본 및 희석주당계속영업이익", 5701),
            self._row("-표준계정코드 미사용-", "우선주 기본 및 희석주당계속영업이익", 5751),
        ]
        v, nm, _ = ND._pick(rows, ND.ACCOUNTS["eps"])
        self.assertEqual(v, 5597.0, "보통주 기본주당이익(5597)을 써야 한다")
        self.assertNotIn("우선주", nm)
        self.assertNotIn("계속영업", nm)   # 총 주당이익 우선

    def test_returns_none_when_only_preferred_exists(self):
        rows = [self._row("-표준계정코드 미사용-", "우선주 기본 및 희석주당이익", 5647)]
        v, _, _ = ND._pick(rows, ND.ACCOUNTS["eps"])
        self.assertIsNone(v, "보통주 EPS 가 없으면 N/A 여야 한다 (우선주로 대체 금지)")

    def test_diluted_only_is_last_resort(self):
        rows = [
            self._row("ifrs-full_DilutedEarningsLossPerShare", "보통주희석주당이익", 8000),
            self._row("-표준계정코드 미사용-", "보통주기본주당이익", 8500),
        ]
        v, nm, _ = ND._pick(rows, ND.ACCOUNTS["eps"])
        self.assertEqual(v, 8500.0, "기본(basic) EPS 를 희석보다 우선해야 한다")


class TestNegativeEarningsPER(unittest.TestCase):
    """적자기업 PER 금지 (Gate 3)."""

    def test_gate3_flags_per_on_negative_earnings(self):
        metrics = {"metrics": {
            "net_income_ttm": {"value": -500, "inputs": {}},
            "per_trailing": {"value": 12.0, "inputs": {}},   # 있으면 안 됨
        }}
        registry = C.load_registry()
        g3 = VR.gate3("009150", [], registry, metrics)
        per_check = next(c for c in g3["checks"] if "적자기업 PER" in c["check"])
        self.assertEqual(per_check["result"], "fail")
        self.assertEqual(g3["status"], "failed")

    def test_gate3_passes_when_per_is_na_for_loss_maker(self):
        metrics = {"metrics": {
            "net_income_ttm": {"value": -500, "inputs": {}},
            "per_trailing": {"value": None, "inputs": {}},   # 올바르게 N/A
        }}
        registry = C.load_registry()
        g3 = VR.gate3("009150", [], registry, metrics)
        per_check = next(c for c in g3["checks"] if "적자기업 PER" in c["check"])
        self.assertEqual(per_check["result"], "pass")

    def test_gate3_flags_cagr_with_negative_base(self):
        metrics = {"metrics": {
            "net_income_ttm": {"value": 100, "inputs": {}},
            "op_cagr_3y": {"value": 15.0, "inputs": {"base_value": -50}},
        }}
        registry = C.load_registry()
        g3 = VR.gate3("009150", [], registry, metrics)
        check = next(c for c in g3["checks"] if "CAGR" in c["check"])
        self.assertEqual(check["result"], "fail")


class TestScoring(unittest.TestCase):
    def test_band_level(self):
        bands = [[None, 3, 0], [3, 8, 1], [8, 15, 2], [15, None, 3]]
        self.assertEqual(SM.band_level(1.0, bands), 0)
        self.assertEqual(SM.band_level(5.0, bands), 1)
        self.assertEqual(SM.band_level(8.0, bands), 2)     # 경계는 하한 포함
        self.assertEqual(SM.band_level(99.0, bands), 3)
        self.assertEqual(SM.band_level(-10.0, bands), 0)

    def test_na_is_excluded_from_score_not_zero(self):
        """N/A 는 분자·분모 모두에서 제외된다. 0점이 아니다."""
        crit = [
            {"id": "A", "name": "a", "type": "auto", "weight": 50,
             "metric": "m1", "bands": [[None, 10, 0], [10, None, 3]]},
            {"id": "B", "name": "b", "type": "auto", "weight": 50,
             "metric": "m2", "bands": [[None, 10, 0], [10, None, 3]]},
        ]
        metrics = {"ticker": "009150", "metrics": {
            "m1": {"value": 20, "na_reason": None},     # level 3
            "m2": {"value": None, "na_reason": "데이터 없음"},   # N/A
        }}
        r = SM.score_module("quality", {"criteria": crit}, metrics, {})

        # A만 채점 → 50/50 × 100 = 100점. B를 0점으로 쳤다면 50점이 됐을 것.
        self.assertEqual(r["score"], 100.0)
        self.assertEqual(r["evidence_coverage"], 0.5)
        self.assertEqual(r["status"], "partial")
        b = next(c for c in r["criteria_scores"] if c["criterion_id"] == "B")
        self.assertIsNone(b["level"])
        self.assertIsNotNone(b["na_reason"])

    def test_all_na_yields_null_score_not_zero(self):
        crit = [{"id": "A", "name": "a", "type": "auto", "weight": 100,
                 "metric": "m1", "bands": [[None, None, 0]]}]
        metrics = {"ticker": "009150",
                   "metrics": {"m1": {"value": None, "na_reason": "없음"}}}
        r = SM.score_module("quality", {"criteria": crit}, metrics, {})
        self.assertIsNone(r["score"])                    # 0 이 아니라 null
        self.assertEqual(r["status"], "insufficient_data")

    def test_missing_credentials_yield_na_not_zero(self):
        crit = [{"id": "T", "name": "t", "type": "auto", "weight": 100,
                 "metric": "index_vs_ma200_pct",
                 "requires_credentials": ["KRX_ID", "KRX_PW"],
                 "bands": [[None, 0, 0], [0, None, 3]]}]
        metrics = {"ticker": "009150",
                   "metrics": {"index_vs_ma200_pct": {"value": None, "na_reason": "no creds"}}}
        r = SM.score_module("trend", {"criteria": crit},
                            metrics, {"KRX_ID": False, "KRX_PW": False})
        c0 = r["criteria_scores"][0]
        self.assertIsNone(c0["level"])
        self.assertIn("자격증명", c0["na_reason"])
        self.assertIsNone(r["score"])

    def test_judged_requires_minimum_evidence(self):
        """근거가 부족하면 등급을 제출해도 채점하지 않는다 (N/A)."""
        crit = {"id": "MOA-01", "name": "m", "type": "judged", "weight": 100,
                "requires_evidence": 2}
        judgment = {"criteria": [
            {"criterion_id": "MOA-01", "level": 3, "evidence_ids": ["E-1"]}  # 1개뿐
        ]}
        r = SM.score_judged(crit, judgment)
        self.assertIsNone(r["level"])
        self.assertIn("근거 부족", r["na_reason"])

    def test_judged_rejects_out_of_range_level(self):
        crit = {"id": "X", "name": "x", "type": "judged", "weight": 10,
                "requires_evidence": 1}
        judgment = {"criteria": [
            {"criterion_id": "X", "level": 7, "evidence_ids": ["E-1"]}
        ]}
        with self.assertRaises(C.SkillError):
            SM.score_judged(crit, judgment)

    def test_score_is_reproducible(self):
        """Gate 3: 저장된 점수를 독립적으로 재계산했을 때 일치해야 한다."""
        registry = C.load_registry()
        result = {
            "module": "quality",
            "criteria_scores": [
                {"criterion_id": "QUA-01", "level": 3},
                {"criterion_id": "QUA-02", "level": 2},
                {"criterion_id": "QUA-03", "level": None},   # N/A → 제외
                {"criterion_id": "QUA-04", "level": 1},
                {"criterion_id": "QUA-05", "level": None},
                {"criterion_id": "QUA-06", "level": 3},
            ],
        }
        # w: QUA-01=18, 02=18, 04=16, 06=15 → Σw=67
        # earned = 18*1 + 18*(2/3) + 16*(1/3) + 15*1 = 18+12+5.333+15 = 50.333
        # score = 50.333/67*100 = 75.1
        self.assertEqual(VR.recompute_score(result, registry), 75.1)


class TestComposite(unittest.TestCase):
    def test_renormalizes_when_modules_missing(self):
        modes = C.load_modes()
        results = [
            {"module": "growth", "score": 80.0, "confidence": 0.9, "evidence_coverage": 1.0},
            {"module": "trend", "score": 60.0, "confidence": 0.8, "evidence_coverage": 0.9},
        ]
        comp = SM.composite(results, "balanced", modes)
        # balanced: growth=15, trend=10 → 재정규화 60/40
        self.assertEqual(comp["weights_used"], {"growth": 60.0, "trend": 40.0})
        self.assertEqual(comp["score"], round(80 * 0.6 + 60 * 0.4, 1))   # 72.0
        self.assertTrue(comp["renormalized"])

    def test_low_completeness_forces_withheld(self):
        """데이터 완전성이 낮으면 점수와 무관하게 판단 유보로 강등된다."""
        modes = C.load_modes()
        results = [
            {"module": "growth", "score": 95.0, "confidence": 0.9, "evidence_coverage": 0.3},
        ]
        comp = SM.composite(results, "balanced", modes)
        self.assertEqual(comp["verdict"], "판단 유보")
        self.assertEqual(comp["score"], 95.0)   # 점수는 그대로 보고된다

    def test_completeness_counts_unscored_modules(self):
        """채점 못 한 모듈을 완전성 계산에서 빼면 안 된다.

        절반이 데이터 부족인데 완전성이 95% 로 보이면 Gate 4(완전성↔결론 강도 일치)가
        무력화된다. 미채점 모듈은 coverage 0 으로 반영되어야 한다.
        """
        modes = C.load_modes()
        results = [
            # balanced: quality=15, growth=15  (채점됨, 완벽)
            {"module": "quality", "score": 80.0, "confidence": 1.0,
             "evidence_coverage": 1.0},
            {"module": "growth", "score": 70.0, "confidence": 1.0,
             "evidence_coverage": 1.0},
            # moat=15, risk=15  (데이터 없음)
            {"module": "moat", "score": None, "confidence": 0.0,
             "evidence_coverage": 0.0},
            {"module": "risk", "score": None, "confidence": 0.0,
             "evidence_coverage": 0.0},
        ]
        comp = SM.composite(results, "balanced", modes)

        # 요청 가중치 합 60 중 30 만 확보 → 완전성 0.5
        self.assertAlmostEqual(comp["data_completeness"], 0.5, places=2)
        self.assertEqual(sorted(comp["unscored_modules"]), ["moat", "risk"])
        # 점수 자체는 채점된 모듈만으로 재정규화된다
        self.assertEqual(comp["score"], 75.0)

    def test_no_scorable_module_yields_withheld(self):
        modes = C.load_modes()
        comp = SM.composite([{"module": "growth", "score": None,
                              "confidence": None, "evidence_coverage": None}],
                            "balanced", modes)
        self.assertIsNone(comp["score"])
        self.assertEqual(comp["verdict"], "판단 유보")

    def test_verdict_is_never_buy_or_sell(self):
        modes = C.load_modes()
        labels = {v["label"] for v in modes["verdict_scale"]}
        self.assertEqual(labels, {"긍정적 관찰", "중립적 관찰", "보수적 관찰", "판단 유보"})
        for lab in labels:
            self.assertNotIn("매수", lab)
            self.assertNotIn("매도", lab)


class TestModeWeights(unittest.TestCase):
    def test_every_mode_sums_to_100(self):
        modes = C.load_modes()
        for name, spec in modes["modes"].items():
            total = sum(spec["weights"].values())
            self.assertEqual(total, 100, f"모드 '{name}' 가중치 합이 {total} (100 이어야 함)")

    def test_modes_cover_registry_modules(self):
        modes = C.load_modes()
        registry = C.load_registry()
        mods = set(registry["modules"])
        for name, spec in modes["modes"].items():
            self.assertEqual(set(spec["weights"]), mods,
                             f"모드 '{name}' 의 모듈 목록이 registry 와 다르다")

    def test_default_mode_exists(self):
        modes = C.load_modes()
        self.assertIn(modes["default"], modes["modes"])


class TestRegistryIntegrity(unittest.TestCase):
    def test_auto_criteria_have_metric_and_bands(self):
        registry = C.load_registry()
        for mod, spec in registry["modules"].items():
            for c in spec["criteria"]:
                if c["type"] == "auto":
                    self.assertIn("metric", c, f"{mod}/{c['id']}: auto 인데 metric 없음")
                    self.assertIn("bands", c, f"{mod}/{c['id']}: auto 인데 bands 없음")
                    for band in c["bands"]:
                        self.assertEqual(len(band), 3)
                        self.assertIn(band[2], (0, 1, 2, 3))

    def test_judged_criteria_declare_evidence_requirement(self):
        registry = C.load_registry()
        for mod, spec in registry["modules"].items():
            for c in spec["criteria"]:
                if c["type"] == "judged":
                    self.assertGreaterEqual(c.get("requires_evidence", 0), 1,
                                            f"{mod}/{c['id']}: 근거 요구량 미선언")

    def test_canslim_reuses_growth_metrics(self):
        """CANSLIM C·A 는 growth 지표를 재사용해야 한다 (중복 계산 금지)."""
        registry = C.load_registry()
        trend = {c["id"]: c for c in registry["modules"]["trend"]["criteria"]}
        growth_metrics = {c["metric"] for c in registry["modules"]["growth"]["criteria"]}

        self.assertEqual(trend["TRD-C"]["reuse_from"], "growth")
        self.assertEqual(trend["TRD-A"]["reuse_from"], "growth")
        self.assertIn(trend["TRD-C"]["metric"], growth_metrics)
        self.assertIn(trend["TRD-A"]["metric"], growth_metrics)

    def test_all_auto_metrics_are_produced_by_calculator(self):
        """registry 가 요구하는 모든 auto 지표를 calculate_metrics 가 만들어야 한다."""
        registry = C.load_registry()
        needed = {
            c["metric"]
            for spec in registry["modules"].values()
            for c in spec["criteria"] if c["type"] == "auto"
        }
        src = (SKILL_ROOT / "scripts" / "calculate_metrics.py").read_text(encoding="utf-8")
        for metric in needed:
            self.assertIn(f'm["{metric}"]', src,
                          f"calculate_metrics.py 가 '{metric}' 을 생성하지 않는다")


class TestEvidenceValidation(unittest.TestCase):
    def _ev(self, **over):
        base = {
            "evidence_id": "Q-TEST-001", "module": "quality", "evidence_type": "metric",
            "metric": "operating_margin_ttm", "value": 12.5, "unit": "%",
            "period_type": "ttm", "fs_div": "CFS",
            "source": {
                "provider": "dart", "source_type": "derived_calculation",
                "rcept_no": "20250301000001",
                "endpoint_or_function": "calculate_metrics.py",
                "retrieved_at": "2026-07-12T10:00:00",
            },
            "calculation": {"formula": "a/b", "input_evidence_ids": ["X"]},
            "limitations": [],
        }
        base.update(over)
        return base

    def test_clean_evidence_passes(self):
        self.assertEqual(VE.check_item(self._ev()), [])

    def test_dart_number_without_rcept_no_or_chain_fails(self):
        """접수번호도 입력 체인도 없으면 공시로 추적할 수 없다."""
        e = self._ev()
        e["source"]["rcept_no"] = None
        e["calculation"]["input_evidence_ids"] = []
        errs = VE.check_item(e)
        self.assertTrue(any("접수번호" in x for x in errs))

    def test_dart_number_traceable_via_evidence_chain_passes(self):
        """다른 지표에서 파생된 값은 직접 접수번호가 없어도 체인으로 추적되면 허용한다."""
        e = self._ev()
        e["source"]["rcept_no"] = None
        e["calculation"]["input_evidence_ids"] = ["Q-REVENUETTM-001"]
        self.assertEqual(VE.check_item(e), [])

    def test_future_date_fails(self):
        e = self._ev()
        e["source"]["retrieved_at"] = "2999-01-01T00:00:00"
        self.assertTrue(any("미래일자" in x for x in VE.check_item(e)))

    def test_pykrx_must_not_be_marked_official(self):
        e = self._ev()
        e["source"]["provider"] = "pykrx"
        e["source"]["source_type"] = "official_api"      # 위장
        e["source"]["underlying_source"] = "KRX"
        e["source"]["endpoint_or_function"] = "get_market_ohlcv"
        self.assertTrue(any("위장" in x for x in VE.check_item(e)))

    def test_pykrx_requires_underlying_source(self):
        """비공식 래퍼는 실제 원천(KRX/Naver)을 밝혀야 한다."""
        e = self._ev()
        e["source"]["provider"] = "pykrx"
        e["source"]["source_type"] = "unofficial_wrapper"
        e["source"]["underlying_source"] = None
        e["source"]["endpoint_or_function"] = "get_market_ohlcv"
        self.assertTrue(any("underlying_source" in x for x in VE.check_item(e)))

    def test_fabricated_endpoint_is_rejected(self):
        """source-priority.yaml 에 없는 엔드포인트는 거부한다 (가짜 API 방지)."""
        e = self._ev()
        e["source"]["endpoint_or_function"] = "getSegmentRevenue.json"   # 존재하지 않음
        self.assertTrue(any("source-priority" in x for x in VE.check_item(e)))

    def test_financial_metric_needs_fs_div(self):
        e = self._ev()
        e["fs_div"] = None
        self.assertTrue(any("연결/별도" in x for x in VE.check_item(e)))

    def test_zero_substitution_detected(self):
        """N/A 사유가 있는데 값이 0 이면 결측을 0 으로 채운 것이다."""
        e = self._ev(value=0, limitations=["N/A 사유: 데이터 없음"])
        errs = VE.check_zero_substitution([e])
        self.assertTrue(any("0 으로 변환" in x for x in errs))

    def test_derived_value_needs_formula(self):
        e = self._ev(calculation=None)
        self.assertTrue(any("재현 불가" in x for x in VE.check_item(e)))


class TestClaimValidation(unittest.TestCase):
    def _claim(self, **over):
        base = {"claim_id": "CLM-0001", "claim": "영업이익률이 개선되었다",
                "claim_type": "fact", "evidence_ids": ["Q-OPM-001"],
                "counter_evidence_ids": [], "confidence": "high",
                "validation": "pending"}
        base.update(over)
        return base

    def _comp(self):
        return {"data_completeness": 0.9, "verdict": "긍정적 관찰"}

    def test_claim_without_evidence_fails(self):
        g4 = VR.gate4("009150", [self._claim(evidence_ids=[])],
                      {"Q-OPM-001"}, self._comp(), {}, None)
        self.assertEqual(g4["status"], "failed")
        self.assertTrue(any("근거 없는 주장" in e for e in g4["errors"]))

    def test_interpretation_needs_two_evidence(self):
        c = self._claim(claim_type="derived_interpretation", evidence_ids=["Q-OPM-001"])
        g4 = VR.gate4("009150", [c], {"Q-OPM-001"}, self._comp(), {}, None)
        self.assertEqual(g4["status"], "failed")

    def test_dangling_evidence_id_fails(self):
        c = self._claim(evidence_ids=["NOPE-999"])
        g4 = VR.gate4("009150", [c], {"Q-OPM-001"}, self._comp(), {}, None)
        self.assertTrue(any("존재하지 않는 evidence" in e for e in g4["errors"]))

    def test_valid_claim_passes(self):
        g4 = VR.gate4("009150", [self._claim()], {"Q-OPM-001"}, self._comp(), {}, None)
        self.assertEqual(g4["status"], "passed")

    def test_target_price_in_html_fails(self):
        html = "<p>목표주가는 250,000원으로 산출된다.</p>"
        g4 = VR.gate4("009150", [self._claim()], {"Q-OPM-001"},
                      self._comp(), {}, html)
        self.assertEqual(g4["status"], "failed")
        self.assertTrue(any("목표주가" in e for e in g4["errors"]))

    def test_negated_target_price_mention_is_allowed(self):
        html = ("<p>목표주가를 제시하지 않는다. 본 보고서는 투자 자문이 아니다.</p>")
        g4 = VR.gate4("009150", [self._claim()], {"Q-OPM-001"},
                      self._comp(), {}, html)
        tp = next(c for c in g4["checks"] if "목표주가" in c["check"])
        self.assertEqual(tp["result"], "pass")

    def test_buy_recommendation_in_html_fails(self):
        html = "<p>본 종목은 매수 의견을 제시한다. 투자 자문이 아니다.</p>"
        g4 = VR.gate4("009150", [self._claim()], {"Q-OPM-001"},
                      self._comp(), {}, html)
        self.assertTrue(any("매수" in e for e in g4["errors"]))

    def test_institutional_net_buy_phrase_is_not_flagged(self):
        """'순매수' 는 수급 용어이지 매수 의견이 아니다."""
        html = ("<p>기관 순매수가 이어졌다. 매수·매도 의견을 제시하지 않는다. "
                "투자 자문이 아니다.</p>")
        g4 = VR.gate4("009150", [self._claim()], {"Q-OPM-001"},
                      self._comp(), {}, html)
        bs = next(c for c in g4["checks"] if "매수·매도" in c["check"])
        self.assertEqual(bs["result"], "pass")

    def test_low_completeness_with_strong_verdict_fails(self):
        comp = {"data_completeness": 0.3, "verdict": "긍정적 관찰"}
        g4 = VR.gate4("009150", [self._claim()], {"Q-OPM-001"}, comp, {}, None)
        self.assertTrue(any("완전성" in e for e in g4["errors"]))

    def test_missing_disclaimer_fails(self):
        html = "<p>분석 결과입니다.</p>"
        g4 = VR.gate4("009150", [self._claim()], {"Q-OPM-001"},
                      self._comp(), {}, html)
        self.assertTrue(any("면책" in e for e in g4["errors"]))


class TestSchemas(unittest.TestCase):
    def test_all_schemas_are_valid_json(self):
        for f in (SKILL_ROOT / "schemas").glob("*.json"):
            with f.open(encoding="utf-8") as fh:
                json.load(fh)

    def test_source_type_enum_matches_policy(self):
        schema = C.read_json(SKILL_ROOT / "schemas" / "evidence-item.schema.json")
        enum = schema["properties"]["source"]["properties"]["source_type"]["enum"]
        self.assertEqual(set(enum), {
            "official_api", "official_filing", "official_download",
            "unofficial_wrapper", "derived_calculation",
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
