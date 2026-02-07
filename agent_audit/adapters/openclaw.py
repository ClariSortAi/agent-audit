from __future__ import annotations

from pathlib import Path

from agent_audit.adapters.helpers import (
    first_existing,
    flatten_endpoint_values,
    flatten_skills,
    list_of_strings,
    read_json,
)
from agent_audit.types import AgentConfig, Skill


class OpenClawAdapter:
    name = "openclaw"

    _config_candidates = [
        "openclaw.json",
        ".openclaw/config.json",
        "config/openclaw.json",
    ]

    def detect(self, path: Path) -> bool:
        config = first_existing(path, self._config_candidates)
        if config:
            return True
        return any(path.glob("**/*openclaw*.json"))

    def get_config(self, path: Path) -> AgentConfig:
        config_path = first_existing(path, self._config_candidates)
        payload = read_json(config_path) if config_path else {}

        permissions = payload.get("permissions", {}) if isinstance(payload.get("permissions"), dict) else {}
        shell_mode = str(permissions.get("shell", payload.get("shell", "unknown"))).lower()

        endpoints = flatten_endpoint_values(payload.get("endpoints", []))
        endpoints.extend(flatten_endpoint_values(payload.get("mcpServers", {})))

        return AgentConfig(
            agent_name="OpenClaw",
            agent_version=str(payload.get("version", "unknown")),
            root_path=path,
            allowed_paths=list_of_strings(payload.get("allowedPaths", permissions.get("allowedPaths", []))),
            blocked_paths=list_of_strings(payload.get("blockedPaths", permissions.get("blockedPaths", []))),
            shell_mode=shell_mode,
            endpoints=endpoints,
            env_var_refs=list_of_strings(payload.get("env", [])),
            hardcoded_secrets=list_of_strings(payload.get("hardcodedSecrets", [])),
            metadata={"config_path": str(config_path) if config_path else ""},
        )

    def get_skills(self, path: Path) -> list[Skill]:
        skills_path = first_existing(path, ["skills.json", ".openclaw/skills.json"])
        payload = read_json(skills_path) if skills_path else {}
        skills_payload = flatten_skills(payload.get("skills", payload))

        skills: list[Skill] = []
        for item in skills_payload:
            skills.append(
                Skill(
                    name=str(item.get("name", "unknown")),
                    permissions=list_of_strings(item.get("permissions", [])),
                    source=str(skills_path) if skills_path else "",
                )
            )
        return skills

    def get_endpoints(self, path: Path) -> list[str]:
        return self.get_config(path).endpoints
