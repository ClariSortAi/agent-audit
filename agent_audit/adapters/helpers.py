from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def read_toml(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def first_existing(base: Path, candidates: list[str]) -> Path | None:
    for candidate in candidates:
        full = base / candidate
        if full.exists() and full.is_file():
            return full
    return None


def list_of_strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if isinstance(value, str):
        return [value]
    return []


def flatten_endpoint_values(value: Any) -> list[str]:
    endpoints: list[str] = []
    if isinstance(value, str):
        endpoints.append(value)
    elif isinstance(value, list):
        for item in value:
            endpoints.extend(flatten_endpoint_values(item))
    elif isinstance(value, dict):
        for dict_value in value.values():
            endpoints.extend(flatten_endpoint_values(dict_value))
    return endpoints


def flatten_skills(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        results: list[dict[str, Any]] = []
        for name, metadata in value.items():
            if isinstance(metadata, dict):
                current = {"name": name, **metadata}
                results.append(current)
        return results
    return []
