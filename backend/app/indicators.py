# =============================================================
# File   : indicators.py
# Author : @injeinnam
# Week   : 09 | Ch.09 (1/2)
# Created: 2026-09-13
# =============================================================
"""기술지표 계산 — SPEC-CHART-001 REQ-008, REQ-009, REQ-010.

REQ-009 에 따라 표준 라이브러리만 사용한다. pandas/numpy 를 쓰지 않는 이유는
백엔드 런타임 의존성을 늘리지 않기 위해서이며, 종목당 수백 개 수준의 시계열에서는
순수 파이썬 순회로 충분하다.

모든 함수는 입력과 같은 길이의 리스트를 반환한다. 지표가 요구하는 최소 관측 기간을
채우지 못한 구간은 None 이다 (REQ-010). 호출자는 이 None 을 JSON null 로 그대로
내보내면 된다.
"""


def _validate_period(period):
    if not isinstance(period, int) or period < 1:
        raise ValueError(f"period 는 1 이상의 정수여야 합니다: {period!r}")


def simple_moving_average(values, period):
    """단순 이동평균(SMA).

    각 지점에서 직전 period 개 값의 산술평균을 낸다.
    앞의 period-1 개 구간은 계산에 필요한 관측치가 부족하므로 None 이다.
    """
    _validate_period(period)
    results = []
    for index in range(len(values)):
        if index + 1 < period:
            results.append(None)
            continue
        window = values[index + 1 - period : index + 1]
        results.append(sum(window) / period)
    return results


def exponential_moving_average(values, period):
    """지수 이동평균(EMA).

    시드는 앞 period 개의 단순평균이고, 이후로는
    EMA = 현재값 x k + 직전EMA x (1-k), k = 2/(period+1) 로 갱신한다.
    """
    _validate_period(period)
    results = [None] * len(values)
    if len(values) < period:
        return results

    smoothing = 2.0 / (period + 1)
    current = sum(values[:period]) / period
    results[period - 1] = current
    for index in range(period, len(values)):
        current = values[index] * smoothing + current * (1.0 - smoothing)
        results[index] = current
    return results


def _rsi_from_averages(average_gain, average_loss):
    """평균 상승/하락폭으로부터 RSI 값을 만든다.

    평균 하락이 0 이면 RS 가 무한대가 되므로 0 나눗셈을 피해 100 을 돌려준다
    (acceptance.md 엣지 케이스에 명시된 관례).
    """
    if average_loss == 0.0:
        return 100.0
    relative_strength = average_gain / average_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def relative_strength_index(values, period=14):
    """상대강도지수(RSI) — Wilder 평활 방식.

    첫 값은 index=period 에서 나온다. 앞 period 개의 변화량으로 평균을 잡아야
    하는데, 변화량은 값이 2개 있어야 1개가 생기기 때문이다.
    """
    _validate_period(period)
    results = [None] * len(values)
    if len(values) <= period:
        return results

    gains = []
    losses = []
    for index in range(1, len(values)):
        change = values[index] - values[index - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    average_gain = sum(gains[:period]) / period
    average_loss = sum(losses[:period]) / period
    results[period] = _rsi_from_averages(average_gain, average_loss)

    for index in range(period + 1, len(values)):
        change_index = index - 1
        average_gain = (average_gain * (period - 1) + gains[change_index]) / period
        average_loss = (average_loss * (period - 1) + losses[change_index]) / period
        results[index] = _rsi_from_averages(average_gain, average_loss)
    return results


def _exponential_moving_average_over_sparse(sparse_values, period):
    """앞부분이 None 인 시계열에 EMA 를 적용하고 원래 위치로 되돌린다.

    MACD 선은 EMA(slow) 가 준비되기 전까지 None 이라, 그대로 EMA 를 걸면
    None 이 계산에 섞인다. None 을 걷어내고 계산한 뒤 인덱스를 복원한다.
    """
    results = [None] * len(sparse_values)
    dense_indexes = []
    dense_values = []
    for index, value in enumerate(sparse_values):
        if value is not None:
            dense_indexes.append(index)
            dense_values.append(value)

    if len(dense_values) < period:
        return results

    dense_results = exponential_moving_average(dense_values, period)
    for offset, original_index in enumerate(dense_indexes):
        results[original_index] = dense_results[offset]
    return results


def macd(values, fast_period=12, slow_period=26, signal_period=9):
    """MACD — 빠른 EMA 와 느린 EMA 의 차이, 그 신호선과 히스토그램.

    반환 형태:
        {"macd": [...], "signal": [...], "histogram": [...]}
    세 리스트 모두 입력과 길이가 같다.
    """
    _validate_period(fast_period)
    _validate_period(slow_period)
    _validate_period(signal_period)
    if fast_period >= slow_period:
        raise ValueError(
            f"fast_period 는 slow_period 보다 작아야 합니다: {fast_period} >= {slow_period}"
        )

    fast_line = exponential_moving_average(values, fast_period)
    slow_line = exponential_moving_average(values, slow_period)

    macd_line = []
    for index in range(len(values)):
        if fast_line[index] is None or slow_line[index] is None:
            macd_line.append(None)
            continue
        macd_line.append(fast_line[index] - slow_line[index])

    signal_line = _exponential_moving_average_over_sparse(macd_line, signal_period)

    histogram = []
    for index in range(len(values)):
        macd_value = macd_line[index]
        signal_value = signal_line[index]
        if macd_value is None or signal_value is None:
            histogram.append(None)
            continue
        histogram.append(macd_value - signal_value)

    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}
