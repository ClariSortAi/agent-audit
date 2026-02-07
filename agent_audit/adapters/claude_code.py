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


class ClaudeCodeAdapter:
    name = "claude_code"

    _config_candidates = [
        ".claude/settings.json",
        "claude-code.json",
    ]

    def detect(self, path: Path) -> bool:
        return first_existing(path, self._config_candidates) is not None

    def get_config(self, path: Path) -> AgentConfig:
        config_path = first_existing(path, self._config_candidates)
        payload = read_json(config_path) if config_path else {}
        permissions = payload.get("permissions", {}) if isinstance(payload.get("permissions"), dict) else {}

        return AgentConfig(
            agent_name="Claude Code",
            agent_version=str(payload.get("version", "unknown")),
            root_path=path,
            allowed_paths=list_of_strings(permissions.get("allow", payload.get("allow", []))),
            blocked_paths=list_of_strings(permissions.get("deny", payload.get("deny", []))),
            shell_mode=str(permissions.get("shell", payload.get("shell", "unknown"))).lower(),
            endpoints=flatten_endpoint_values(payload.get("mcpServers", {})),
            env_var_refs=list_of_strings(payload.get("env", [])),
            hardcoded_secrets=list_of_strings(payload.get("secrets", [])),
            metadata={"config_path": str(config_path) if config_path else ""},
        )

    def get_skills(self, path: Path) -> list[Skill]:
        skills_path = first_existing(path, [".claude/skills.json", "claude-skills.json"])
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
