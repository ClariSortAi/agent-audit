from __future__ import annotations

from agent_audit.types import CheckResult


WEIGHTS = {
    "filesystem": 0.25,
    "network": 0.20,
    "shell": 0.25,
    "secrets": 0.15,
    "skills": 0.15,
}


def calculate_risk_score(checks: dict[str, CheckResult]) -> float:
    total = 0.0
    for key, weight in WEIGHTS.items():
        check = checks.get(key)
        if check is None:
            continue
        total += check.score * weight
    return round(total, 1)


def risk_tier(score: float) -> str:
    if score >= 9.0:
        return "CRITICAL"
    if score >= 6.0:
        return "HIGH"
    if score >= 3.0:
        return "MEDIUM"
    return "LOW"
