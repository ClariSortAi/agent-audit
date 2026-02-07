from __future__ import annotations

from agent_audit.types import AgentConfig, CheckResult


def evaluate_shell(config: AgentConfig) -> CheckResult:
    key = "shell"
    title = "Shell Execution"

    mode = (config.shell_mode or "unknown").lower()
    if mode in {"none", "disabled", "off"}:
        return CheckResult(
            key=key,
            title=title,
            score=0.0,
            severity="low",
            summary="Shell execution appears disabled.",
            details=[],
        )

    if mode in {"filtered", "restricted", "allowlist"}:
        return CheckResult(
            key=key,
            title=title,
            score=5.0,
            severity="medium",
            summary="Shell execution is enabled with filters.",
            details=["Review allowlist and escaping controls."],
        )

    if mode in {"unrestricted", "true", "enabled", "on"}:
        return CheckResult(
            key=key,
            title=title,
            score=10.0,
            severity="critical",
            summary="Agent can execute unrestricted shell commands.",
            details=["Treat runtime as equivalent to current user shell access."],
        )

    return CheckResult(
        key=key,
        title=title,
        score=7.5,
        severity="high",
        summary="Shell policy is unclear; assume broad command execution.",
        details=[f"Observed shell mode: {mode}"],
    )
