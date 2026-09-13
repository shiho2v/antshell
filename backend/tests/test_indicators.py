# =============================================================
# File   : test_indicators.py
# Author : @injeinnam
# Week   : 09 | Ch.09 (1/2)
# Created: 2026-09-13
# =============================================================
"""기술지표 계산 검증 — SPEC-CHART-001 AC-008, AC-009, AC-016.

손으로 검증 가능한 고정 입력만 사용한다. 실제 시세 파일에 의존하지 않으므로
데이터가 갱신돼도 기대값이 흔들리지 않는다.
"""

import ast
from pathlib import Path

import pytest
from app import indicators

MODULE_PATH = Path(indicators.__file__)

# 서드파티로 간주하지 않는 표준 라이브러리 모듈.
STANDARD_LIBRARY_MODULES = {"math", "typing", "collections", "itertools", "statistics"}


# --- AC-016: 지표 수치 정확성 (손으로 검증한 기대값) --------------------------


def test_simple_moving_average_matches_hand_computed_values():
    """AC-016 본문에 명시된 기대값. SMA(5) of [1..6] == [None×4, 3.0, 4.0]."""
    result = indicators.simple_moving_average([1, 2, 3, 4, 5, 6], 5)

    assert result == [None, None, None, None, 3.0, 4.0]


def test_exponential_moving_average_matches_hand_computed_values():
    """EMA(3) of [1..5]. k=0.5, 시드는 앞 3개의 SMA=2.0.

    idx3 = 4*0.5 + 2.0*0.5 = 3.0
    idx4 = 5*0.5 + 3.0*0.5 = 4.0
    """
    result = indicators.exponential_moving_average([1, 2, 3, 4, 5], 3)

    assert result == [None, None, 2.0, 3.0, 4.0]


def test_relative_strength_index_is_100_when_there_are_no_losses():
    """상승만 있으면 평균 하락이 0이므로 RSI = 100 (acceptance.md 엣지 케이스)."""
    values = list(range(1, 17))

    result = indicators.relative_strength_index(values, 14)

    assert result[:14] == [None] * 14
    assert result[14] == pytest.approx(100.0)
    assert result[15] == pytest.approx(100.0)


def test_relative_strength_index_matches_hand_computed_values():
    """상승과 하락이 섞인 경우의 주 계산식 검증.

    values=[10, 11, 10, 11, 10], period=2 -> 변화량 +1, -1, +1, -1

    index 2: 평균상승 0.5 / 평균하락 0.5 -> RS 1.0   -> 100 - 100/2.0  = 50.0
    index 3: 평균상승 0.75 / 평균하락 0.25 -> RS 3.0 -> 100 - 100/4.0  = 75.0
    index 4: 평균상승 0.375 / 평균하락 0.625 -> RS 0.6 -> 100 - 100/1.6 = 37.5
    """
    result = indicators.relative_strength_index([10, 11, 10, 11, 10], 2)

    assert result[:2] == [None, None]
    assert result[2] == pytest.approx(50.0)
    assert result[3] == pytest.approx(75.0)
    assert result[4] == pytest.approx(37.5)


def test_relative_strength_index_is_zero_when_there_are_no_gains():
    """하락만 있으면 평균 상승이 0 이므로 RS=0, RSI=0 이다."""
    values = list(range(20, 4, -1))

    result = indicators.relative_strength_index(values, 14)

    assert result[14] == pytest.approx(0.0)


def test_relative_strength_index_handles_flat_series_without_zero_division():
    """변동이 전혀 없는 구간에서도 0 나눗셈이 발생하지 않아야 한다."""
    values = [5] * 16

    result = indicators.relative_strength_index(values, 14)

    assert result[14] is not None
    assert 0.0 <= result[14] <= 100.0


def test_macd_equals_fast_ema_minus_slow_ema():
    """MACD 선은 정의상 EMA(fast) - EMA(slow) 와 같아야 한다."""
    values = [float(index) for index in range(1, 61)]

    fast_ema = indicators.exponential_moving_average(values, 12)
    slow_ema = indicators.exponential_moving_average(values, 26)
    result = indicators.macd(values, 12, 26, 9)

    for index in range(len(values)):
        if fast_ema[index] is None or slow_ema[index] is None:
            assert result["macd"][index] is None
        else:
            assert result["macd"][index] == pytest.approx(fast_ema[index] - slow_ema[index])


def test_macd_histogram_equals_macd_minus_signal():
    values = [float(index) for index in range(1, 61)]

    result = indicators.macd(values, 12, 26, 9)

    for index in range(len(values)):
        macd_value = result["macd"][index]
        signal_value = result["signal"][index]
        if macd_value is None or signal_value is None:
            assert result["histogram"][index] is None
        else:
            assert result["histogram"][index] == pytest.approx(macd_value - signal_value)


# --- AC-009: 최소 관측 기간 미충족 구간은 null -------------------------------


@pytest.mark.parametrize("period,expected_none_count", [(5, 4), (20, 19), (60, 59)])
def test_simple_moving_average_null_prefix_length(period, expected_none_count):
    values = [float(index) for index in range(1, 101)]

    result = indicators.simple_moving_average(values, period)

    assert result[:expected_none_count] == [None] * expected_none_count
    assert result[expected_none_count] is not None


def test_relative_strength_index_null_prefix_length():
    """RSI(14) 는 앞 14개가 null 이고 15번째(index 14)부터 값이 나온다."""
    values = [float(index) for index in range(1, 101)]

    result = indicators.relative_strength_index(values, 14)

    assert result[:14] == [None] * 14
    assert result[14] is not None


def test_indicators_return_same_length_as_input():
    values = [float(index) for index in range(1, 101)]

    assert len(indicators.simple_moving_average(values, 20)) == len(values)
    assert len(indicators.exponential_moving_average(values, 12)) == len(values)
    assert len(indicators.relative_strength_index(values, 14)) == len(values)
    macd_result = indicators.macd(values, 12, 26, 9)
    assert len(macd_result["macd"]) == len(values)
    assert len(macd_result["signal"]) == len(values)
    assert len(macd_result["histogram"]) == len(values)


def test_series_shorter_than_period_is_all_null():
    """레코드가 지표 최소 기간보다 짧아도 오류가 아니라 전 구간 null 이다."""
    short_series = [1.0, 2.0, 3.0]

    assert indicators.simple_moving_average(short_series, 60) == [None] * 3
    assert indicators.exponential_moving_average(short_series, 60) == [None] * 3
    assert indicators.relative_strength_index(short_series, 14) == [None] * 3
    macd_result = indicators.macd(short_series, 12, 26, 9)
    assert macd_result["macd"] == [None] * 3
    assert macd_result["signal"] == [None] * 3


def test_empty_series_returns_empty_lists():
    assert indicators.simple_moving_average([], 20) == []
    assert indicators.relative_strength_index([], 14) == []
    assert indicators.macd([], 12, 26, 9)["macd"] == []


def test_invalid_period_is_rejected():
    with pytest.raises(ValueError):
        indicators.simple_moving_average([1.0, 2.0], 0)
    with pytest.raises(ValueError):
        indicators.exponential_moving_average([1.0, 2.0], -1)


def test_macd_rejects_fast_period_not_smaller_than_slow_period():
    values = [float(index) for index in range(1, 61)]

    with pytest.raises(ValueError):
        indicators.macd(values, 26, 12, 9)
    with pytest.raises(ValueError):
        indicators.macd(values, 12, 12, 9)


# --- AC-008: 신규 서드파티 런타임 의존성 없음 ---------------------------------


def test_indicators_module_imports_standard_library_only():
    """AC-008 — pandas/numpy 등 서드파티 import 가 없어야 한다."""
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))

    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            imported_roots.add(node.module.split(".")[0])

    unexpected = imported_roots - STANDARD_LIBRARY_MODULES
    assert not unexpected, f"서드파티 의존성이 추가됐다: {sorted(unexpected)}"


def test_requirements_txt_has_no_new_runtime_dependency():
    """AC-008 — backend/requirements.txt 에 pandas/numpy/talib 가 없어야 한다."""
    requirements_path = MODULE_PATH.parent.parent / "requirements.txt"
    content = requirements_path.read_text(encoding="utf-8").lower()

    for forbidden in ("pandas", "numpy", "talib", "ta-lib", "pykrx"):
        assert forbidden not in content, f"{forbidden} 가 런타임 의존성에 추가됐다"
