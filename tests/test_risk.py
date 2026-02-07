from agent_audit.core.risk import calculate_risk_score, risk_tier
from agent_audit.types import CheckResult


def test_weighted_risk_score() -> None:
    checks = {
        "filesystem": CheckResult("filesystem", "fs", 10.0, "high", "", []),
        "network": CheckResult("network", "network", 0.0, "low", "", []),
        "shell": CheckResult("shell", "shell", 10.0, "critical", "", []),
        "secrets": CheckResult("secrets", "secrets", 0.0, "low", "", []),
        "skills": CheckResult("skills", "skills", 0.0, "low", "", []),
    }
    assert calculate_risk_score(checks) == 5.0


def test_risk_tiers() -> None:
    assert risk_tier(2.9) == "LOW"
    assert risk_tier(3.0) == "MEDIUM"
    assert risk_tier(6.0) == "HIGH"
    assert risk_tier(9.0) == "CRITICAL"
