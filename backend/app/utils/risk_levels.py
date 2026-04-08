from __future__ import annotations

import json
from functools import lru_cache

from app.config import settings

RiskLevel = str
RISK_LEVEL_ORDER: tuple[RiskLevel, ...] = ("low", "medium-low", "medium", "high")
_RANK = {level: idx for idx, level in enumerate(RISK_LEVEL_ORDER)}


@lru_cache(maxsize=1)
def _thresholds() -> tuple[float, float, float]:
    """Return (low_risk_ceiling, decision_threshold, high_risk_threshold)."""
    low = 0.3
    decision = float(settings.fallback_risk_threshold)
    high = 0.9
    try:
        cfg = json.loads(open(settings.threshold_policy_path, "r", encoding="utf-8").read())
        low = float(cfg.get("low_risk_ceiling", low))
        decision = float(cfg.get("decision_threshold", decision))
        high = float(cfg.get("high_risk_threshold", high))
    except Exception:
        pass
    return low, decision, high


def level_from_score(score: float | int | None) -> RiskLevel:
    """Map numeric score to canonical AML risk level using trained thresholds."""
    if score is None:
        return "low"
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "low"

    low, decision, high = _thresholds()
    if s >= high:
        return "high"
    if s >= decision:
        return "medium"
    if s <= low:
        return "low"
    return "medium-low"


def normalize_level(level: str | None) -> RiskLevel:
    if not level:
        return "low"
    v = str(level).strip().lower()
    return v if v in _RANK else "low"


def max_level(*levels: str | None) -> RiskLevel:
    """Return the highest-severity level from a list of levels."""
    best = "low"
    for level in levels:
        n = normalize_level(level)
        if _RANK[n] > _RANK[best]:
            best = n
    return best


def level_rank(level: str | None) -> int:
    return _RANK[normalize_level(level)]

