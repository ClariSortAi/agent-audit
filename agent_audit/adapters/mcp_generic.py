from __future__ import annotations

from pathlib import Path

from agent_audit.adapters.helpers import (
    first_existing,
    flatten_endpoint_values,
    list_of_strings,
    read_json,
)
from agent_audit.types import AgentConfig, Skill


class MCPGenericAdapter:
    name = "mcp_generic"

    _config_candidates = ["mcp.json", ".mcp/config.json", "mcp-servers.json"]

    def detect(self, path: Path) -> bool:
        if first_existing(path, self._config_candidates):
            return True
        for candidate in path.glob("**/*.json"):
            payload = read_json(candidate)
            if "mcpServers" in payload or "mcp_servers" in payload:
                return True
        return False

    def get_config(self, path: Path) -> AgentConfig:
        config_path = first_existing(path, self._config_candidates)
        payload = read_json(config_path) if config_path else {}
        servers = payload.get("mcpServers", payload.get("mcp_servers", {}))

        return AgentConfig(
            agent_name="MCP",
            agent_version=str(payload.get("version", "unknown")),
            root_path=path,
            allowed_paths=list_of_strings(payload.get("allowedPaths", [])),
            blocked_paths=list_of_strings(payload.get("blockedPaths", [])),
            shell_mode=str(payload.get("shell", "unknown")).lower(),
            endpoints=flatten_endpoint_values(servers),
            env_var_refs=list_of_strings(payload.get("env", [])),
            hardcoded_secrets=list_of_strings(payload.get("secrets", [])),
            metadata={"config_path": str(config_path) if config_path else ""},
        )

    def get_skills(self, path: Path) -> list[Skill]:
        return []

    def get_endpoints(self, path: Path) -> list[str]:
        return self.get_config(path).endpoints
