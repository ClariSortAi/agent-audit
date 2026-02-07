from __future__ import annotations

from pathlib import Path

from agent_audit.adapters import detect_adapter
from agent_audit.checks import (
    evaluate_filesystem,
    evaluate_network,
    evaluate_secrets,
    evaluate_shell,
    evaluate_skills,
)
from agent_audit.core.risk import calculate_risk_score, risk_tier
from agent_audit.types import ScanResult


class Scanner:
    def scan_path(self, path: str | Path) -> ScanResult:
        target = Path(path).expanduser().resolve()
        adapter = detect_adapter(target)

        config = adapter.get_config(target)
        skills = adapter.get_skills(target)
        endpoints = adapter.get_endpoints(target)
        if endpoints:
            config.endpoints = endpoints

        checks = {
            "filesystem": evaluate_filesystem(config),
            "network": evaluate_network(config.endpoints),
            "shell": evaluate_shell(config),
            "secrets": evaluate_secrets(config),
            "skills": evaluate_skills(skills),
        }

        score = calculate_risk_score(checks)
        tier = risk_tier(score)

        return ScanResult(
            agent_name=config.agent_name,
            agent_version=config.agent_version,
            adapter_name=adapter.name,
            scanned_path=str(target),
            checks=checks,
            risk_score=score,
            risk_tier=tier,
        )
