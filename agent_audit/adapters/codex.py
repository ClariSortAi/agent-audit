from __future__ import annotations

from pathlib import Path

from agent_audit.adapters.helpers import (
    first_existing,
    flatten_endpoint_values,
    flatten_skills,
    list_of_strings,
    read_json,
    read_toml,
)
from agent_audit.types import AgentConfig, Skill


class CodexAdapter:
    name = "codex"

    _config_candidates = [
        ".codex/config.toml",
        "codex.toml",
        "codex.json",
    ]

    def detect(self, path: Path) -> bool:
        return first_existing(path, self._config_candidates) is not None

    def get_config(self, path: Path) -> AgentConfig:
        config_path = first_existing(path, self._config_candidates)
        if not config_path:
            payload: dict = {}
        elif config_path.suffix == ".toml":
            payload = read_toml(config_path)
        else:
            payload = read_json(config_path)

        permissions = payload.get("permissions", {}) if isinstance(payload.get("permissions"), dict) else {}
        sandbox = payload.get("sandbox", {}) if isinstance(payload.get("sandbox"), dict) else {}

        allowed_paths = list_of_strings(
            permissions.get("allowed_paths", sandbox.get("writable_roots", payload.get("writable_roots", [])))
        )
        blocked_paths = list_of_strings(permissions.get("blocked_paths", payload.get("blocked_paths", [])))
        shell_mode = str(
            permissions.get("shell", payload.get("shell", sandbox.get("shell", "unknown")))
        ).lower()

        endpoints = flatten_endpoint_values(payload.get("network", payload.get("endpoints", [])))

        return AgentConfig(
            agent_name="Codex",
            agent_version=str(payload.get("version", "unknown")),
            root_path=path,
            allowed_paths=allowed_paths,
            blocked_paths=blocked_paths,
            shell_mode=shell_mode,
            endpoints=endpoints,
            env_var_refs=list_of_strings(payload.get("env", payload.get("env_vars", []))),
            hardcoded_secrets=list_of_strings(payload.get("hardcoded_secrets", [])),
            metadata={"config_path": str(config_path) if config_path else ""},
        )

    def get_skills(self, path: Path) -> list[Skill]:
        skills_path = first_existing(path, [".codex/skills.json", "skills.json"])
        payload = read_json(skills_path) if skills_path else {}
        skills_payload = flatten_skills(payload.get("skills", payload))
        return [
            Skill(
                name=str(item.get("name", "unknown")),
                permissions=list_of_strings(item.get("permissions", [])),
                source=str(skills_path) if skills_path else "",
            )
            for item in skills_payload
        ]

    def get_endpoints(self, path: Path) -> list[str]:
        return self.get_config(path).endpoints
