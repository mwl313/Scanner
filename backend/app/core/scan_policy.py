from __future__ import annotations

from dataclasses import dataclass


ALLOWED_SCAN_UNIVERSE_LIMITS: tuple[int, ...] = (120, 200, 300, 500, 0)
DEFAULT_SCAN_UNIVERSE_LIMIT: int = 300
PRE_SCREEN_SCAN_UNIVERSE_LIMITS: frozenset[int] = frozenset({500, 0})


@dataclass(frozen=True)
class StrategyScanPolicy:
    universe_limit: int
    pre_screen_enabled: bool


def normalize_scan_universe_limit(value: int | None) -> int:
    if value is None:
        return DEFAULT_SCAN_UNIVERSE_LIMIT

    try:
        normalized = int(value)
    except (TypeError, ValueError):
        return DEFAULT_SCAN_UNIVERSE_LIMIT

    if normalized in ALLOWED_SCAN_UNIVERSE_LIMITS:
        return normalized
    return DEFAULT_SCAN_UNIVERSE_LIMIT


def is_pre_screen_required(universe_limit: int) -> bool:
    return int(universe_limit) in PRE_SCREEN_SCAN_UNIVERSE_LIMITS


def resolve_strategy_scan_policy(universe_limit: int | None) -> StrategyScanPolicy:
    normalized = normalize_scan_universe_limit(universe_limit)
    return StrategyScanPolicy(
        universe_limit=normalized,
        pre_screen_enabled=is_pre_screen_required(normalized),
    )
