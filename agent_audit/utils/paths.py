from __future__ import annotations

from pathlib import Path


SENSITIVE_SEGMENTS = {
    ".ssh",
    ".aws",
    ".gnupg",
    ".config",
    ".env",
    "/etc",
    "/var",
}


def normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def is_unrestricted_path(raw_path: str) -> bool:
    path = raw_path.strip()
    return path in {"/", "*", "**", "~", "~/", "C:\\", "D:\\"}


def references_sensitive_location(raw_path: str) -> bool:
    return any(segment in raw_path for segment in SENSITIVE_SEGMENTS)


def is_within(base: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(base)
        return True
    except ValueError:
        return False
