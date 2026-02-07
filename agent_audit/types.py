from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Skill:
    name: str
    permissions: list[str] = field(default_factory=list)
    source: str = ""


@dataclass(slots=True)
class CheckResult:
    key: str
    title: str
    score: float
    severity: str
    summary: str
    details: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AgentConfig:
    agent_name: str
    agent_version: str
    root_path: Path
    allowed_paths: list[str] = field(default_factory=list)
    blocked_paths: list[str] = field(default_factory=list)
    shell_mode: str = "unknown"
    endpoints: list[str] = field(default_factory=list)
    env_var_refs: list[str] = field(default_factory=list)
    hardcoded_secrets: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScanResult:
    agent_name: str
    agent_version: str
    adapter_name: str
    scanned_path: str
    checks: dict[str, CheckResult]
    risk_score: float
    risk_tier: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checks"] = {
            key: asdict(result)
            for key, result in self.checks.items()
        }
        return payload
