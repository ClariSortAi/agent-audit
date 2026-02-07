SEVERITY_LABELS = {
    "low": "LOW",
    "medium": "MEDIUM",
    "high": "HIGH",
    "critical": "CRITICAL",
}


def severity_label(value: str) -> str:
    return SEVERITY_LABELS.get(value.lower(), value.upper())
