from __future__ import annotations

from agent_audit.types import CheckResult, Skill


HIGH_RISK_PERMISSIONS = {
    "shell",
    "exec",
    "filesystem.write",
    "filesystem.*",
    "network.*",
}

MEDIUM_RISK_PERMISSIONS = {
    "network",
    "filesystem.read",
    "process.spawn",
}


def evaluate_skills(skills: list[Skill]) -> CheckResult:
    key = "skills"
    title = "Skills / Plugins"

    if not skills:
        return CheckResult(
            key=key,
            title=title,
            score=0.0,
            severity="low",
            summary="No installed skills/plugins detected.",
            details=[],
        )

    high_count = 0
    medium_count = 0
    details: list[str] = []

    for skill in skills:
        perms = {perm.lower() for perm in skill.permissions}
        if perms & HIGH_RISK_PERMISSIONS:
            high_count += 1
            details.append(f"High-risk skill: {skill.name} ({', '.join(sorted(perms))})")
        elif perms & MEDIUM_RISK_PERMISSIONS:
            medium_count += 1
            details.append(f"Medium-risk skill: {skill.name} ({', '.join(sorted(perms))})")

    if high_count:
        score = 9.0
        severity = "high"
        summary = f"{high_count} high-risk skill(s) detected."
    elif medium_count:
        score = 5.0
        severity = "medium"
        summary = f"{medium_count} medium-risk skill(s) detected."
    else:
        score = 2.0
        severity = "low"
        summary = "Installed skills appear low risk from declared permissions."

    details.append(f"Total installed skills: {len(skills)}")
    return CheckResult(
        key=key,
        title=title,
        score=score,
        severity=severity,
        summary=summary,
        details=details,
    )
