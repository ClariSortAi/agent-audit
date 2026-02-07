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


class NanobotAdapter:
    name = "nanobot"

    _config_candidates = ["nanobot.json", ".nanobot/config.json", "config.json"]

    def detect(self, path: Path) -> bool:
        config = first_existing(path, self._config_candidates)
        if config:
            payload = read_json(config)
            return str(payload.get("agent", "")).lower() in {"nanobot", ""}
        return any(path.glob("**/*nanobot*.json"))

    def get_config(self, path: Path) -> AgentConfig:
        config_path = first_existing(path, self._config_candidates)
        payload = read_json(config_path) if config_path else {}
        perms = payload.get("permissions", {}) if isinstance(payload.get("permissions"), dict) else {}

        return AgentConfig(
            agent_name="Nanobot",
            agent_version=str(payload.get("version", "unknown")),
            root_path=path,
            allowed_paths=list_of_strings(payload.get("allowed_paths", perms.get("filesystem", []))),
            blocked_paths=list_of_strings(payload.get("blocked_paths", [])),
            shell_mode=str(perms.get("shell", payload.get("shell", "unknown"))).lower(),
            endpoints=flatten_endpoint_values(payload.get("network", payload.get("endpoints", []))),
            env_var_refs=list_of_strings(payload.get("env_refs", [])),
            hardcoded_secrets=list_of_strings(payload.get("hardcoded_secrets", [])),
            metadata={"config_path": str(config_path) if config_path else ""},
        )

    def get_skills(self, path: Path) -> list[Skill]:
        skills_path = first_existing(path, ["nanobot-skills.json", ".nanobot/skills.json"])
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
