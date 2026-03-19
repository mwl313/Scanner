import math


def sma(values: list[float], period: int) -> list[float]:
    if period <= 0:
        raise ValueError('period must be positive')
    output: list[float] = []
    running = 0.0

    for idx, value in enumerate(values):
        running += value
        if idx >= period:
            running -= values[idx - period]
        if idx + 1 >= period:
            output.append(running / period)
        else:
            output.append(math.nan)
    return output


def rolling_std(values: list[float], period: int) -> list[float]:
    if period <= 0:
        raise ValueError('period must be positive')

    output: list[float] = []
    for idx in range(len(values)):
        if idx + 1 < period:
            output.append(math.nan)
            continue
        window = values[idx + 1 - period : idx + 1]
        mean = sum(window) / period
        variance = sum((v - mean) ** 2 for v in window) / period
        output.append(math.sqrt(variance))
    return output


def bollinger(values: list[float], period: int, std_mult: float) -> tuple[list[float], list[float], list[float]]:
    mid = sma(values, period)
    std = rolling_std(values, period)
    upper: list[float] = []
    lower: list[float] = []

    for m, s in zip(mid, std, strict=False):
        if math.isnan(m) or math.isnan(s):
            upper.append(math.nan)
            lower.append(math.nan)
            continue
        upper.append(m + std_mult * s)
        lower.append(m - std_mult * s)

    return upper, mid, lower


def rsi(values: list[float], period: int) -> list[float]:
    if len(values) < 2:
        return [math.nan for _ in values]

    gains = [0.0]
    losses = [0.0]
    for idx in range(1, len(values)):
        delta = values[idx] - values[idx - 1]
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))

    avg_gain: list[float] = [math.nan] * len(values)
    avg_loss: list[float] = [math.nan] * len(values)

    if len(values) <= period:
        return [math.nan for _ in values]

    first_gain = sum(gains[1 : period + 1]) / period
    first_loss = sum(losses[1 : period + 1]) / period
    avg_gain[period] = first_gain
    avg_loss[period] = first_loss

    for idx in range(period + 1, len(values)):
        avg_gain[idx] = ((avg_gain[idx - 1] * (period - 1)) + gains[idx]) / period
        avg_loss[idx] = ((avg_loss[idx - 1] * (period - 1)) + losses[idx]) / period

    output: list[float] = [math.nan] * len(values)
    for idx in range(period, len(values)):
        loss = avg_loss[idx]
        gain = avg_gain[idx]
        if loss == 0:
            output[idx] = 100.0
            continue
        rs = gain / loss
        output[idx] = 100 - (100 / (1 + rs))
    return output


def is_nan(value: float) -> bool:
    return isinstance(value, float) and math.isnan(value)
