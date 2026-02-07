from __future__ import annotations

import re
from pathlib import Path

from agent_audit.types import AgentConfig, CheckResult


SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[\"']?([A-Za-z0-9_\-]{10,})"),
    re.compile(r"(?i)sk-[A-Za-z0-9]{12,}"),
]


def _scan_file_for_hardcoded_secrets(path: Path) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []

    hits: list[str] = []
    for pattern in SECRET_PATTERNS:
        for match in pattern.findall(text):
            if isinstance(match, tuple):
                candidate = match[-1]
            else:
                candidate = match
            if candidate:
                hits.append(str(candidate)[:4] + "...redacted")
    return sorted(set(hits))


def evaluate_secrets(config: AgentConfig) -> CheckResult:
    key = "secrets"
    title = "Secrets Exposure"

    file_hits: list[str] = []
    config_path = config.metadata.get("config_path", "") if isinstance(config.metadata, dict) else ""
    if config_path:
        file_hits = _scan_file_for_hardcoded_secrets(Path(config_path))

    hardcoded = sorted(set(config.hardcoded_secrets + file_hits))
    env_refs = sorted(set(config.env_var_refs))

    details: list[str] = []
    if env_refs:
        details.append(f"Environment secrets referenced: {', '.join(env_refs)}")
    if hardcoded:
        details.extend([f"Hardcoded secret detected: {value}" for value in hardcoded])

    if hardcoded:
        score = 10.0
        severity = "critical"
        summary = "Hardcoded secrets detected in configuration."
    elif env_refs:
        score = 5.0
        severity = "medium"
        summary = "Sensitive environment variables are referenced by agent config."
    else:
        score = 0.0
        severity = "low"
        summary = "No secret exposure signals found in static configuration."

    return CheckResult(
        key=key,
        title=title,
        score=score,
        severity=severity,
        summary=summary,
        details=details,
    )
