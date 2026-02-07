from __future__ import annotations

from urllib.parse import urlparse

from agent_audit.types import CheckResult


KNOWN_API_DOMAINS = {
    "api.openai.com",
    "api.anthropic.com",
    "api.github.com",
}

RISKY_DOMAINS = {
    "raw.githubusercontent.com",
    "pastebin.com",
    "ngrok.io",
    "ngrok-free.app",
}


def evaluate_network(endpoints: list[str]) -> CheckResult:
    key = "network"
    title = "Network Egress"

    if not endpoints:
        return CheckResult(
            key=key,
            title=title,
            score=0.0,
            severity="low",
            summary="No configured external endpoints found.",
            details=[],
        )

    details: list[str] = []
    has_http = False
    unknown_domains: set[str] = set()
    risky_domains: set[str] = set()
    wildcard = False

    for endpoint in endpoints:
        value = endpoint.strip()
        if any(token in value for token in {"*", "0.0.0.0", "any"}):
            wildcard = True
        parsed = urlparse(value if "://" in value else f"https://{value}")
        domain = parsed.netloc or parsed.path
        if parsed.scheme == "http":
            has_http = True
            details.append(f"Non-TLS endpoint: {endpoint}")
        if domain in RISKY_DOMAINS:
            risky_domains.add(domain)
            details.append(f"Code-fetch/exfil domain configured: {domain}")
        if domain and domain not in KNOWN_API_DOMAINS and domain not in RISKY_DOMAINS:
            unknown_domains.add(domain)

    if has_http or wildcard:
        score = 10.0
        severity = "critical"
        summary = "Arbitrary or insecure network egress appears allowed."
    elif risky_domains or len(unknown_domains) > 5:
        score = 7.0
        severity = "high"
        summary = "Broad outbound network access detected."
    elif unknown_domains:
        score = 4.0
        severity = "medium"
        summary = "Custom network endpoints detected; validate trust boundaries."
    else:
        score = 2.0
        severity = "low"
        summary = "Network access is limited to known API domains."

    details.append(f"Configured endpoints: {len(endpoints)}")
    return CheckResult(
        key=key,
        title=title,
        score=score,
        severity=severity,
        summary=summary,
        details=details,
    )
