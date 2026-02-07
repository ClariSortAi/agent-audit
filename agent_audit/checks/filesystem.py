from __future__ import annotations

from pathlib import Path

from agent_audit.types import AgentConfig, CheckResult
from agent_audit.utils.paths import is_unrestricted_path, normalize_path, references_sensitive_location


def evaluate_filesystem(config: AgentConfig) -> CheckResult:
    key = "filesystem"
    title = "File System Access"
    details: list[str] = []

    allowed_paths = config.allowed_paths
    if not allowed_paths:
        return CheckResult(
            key=key,
            title=title,
            score=10.0,
            severity="high",
            summary="No path constraints detected; access model appears unrestricted.",
            details=["Declare explicit allowed paths in agent config."],
        )

    unrestricted = any(is_unrestricted_path(path) for path in allowed_paths)
    if unrestricted:
        details.extend([f"Unrestricted path detected: {path}" for path in allowed_paths if is_unrestricted_path(path)])

    sensitive_hits = [path for path in allowed_paths if references_sensitive_location(path)]
    details.extend([f"Sensitive location accessible: {path}" for path in sensitive_hits])

    root = normalize_path(config.root_path)
    out_of_scope: list[str] = []
    for raw_path in allowed_paths:
        if is_unrestricted_path(raw_path):
            continue
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = (root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            out_of_scope.append(raw_path)

    if out_of_scope:
        details.extend([f"Path exceeds project scope: {path}" for path in out_of_scope])

    if unrestricted:
        score = 10.0
        severity = "critical"
        summary = "Agent can access effectively any path on disk."
    elif sensitive_hits or out_of_scope:
        score = 6.5
        severity = "high"
        summary = "Agent has broad file system access beyond project scope."
    else:
        score = 1.5
        severity = "low"
        summary = "File access appears scoped to project paths."

    blocked = config.blocked_paths
    if blocked:
        details.append(f"Blocked paths declared: {', '.join(blocked)}")

    return CheckResult(
        key=key,
        title=title,
        score=score,
        severity=severity,
        summary=summary,
        details=details,
    )
