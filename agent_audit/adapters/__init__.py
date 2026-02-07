from __future__ import annotations

from pathlib import Path

from agent_audit.adapters.base import AgentAdapter
from agent_audit.adapters.claude_code import ClaudeCodeAdapter
from agent_audit.adapters.codex import CodexAdapter
from agent_audit.adapters.mcp_generic import MCPGenericAdapter
from agent_audit.adapters.nanobot import NanobotAdapter
from agent_audit.adapters.openclaw import OpenClawAdapter


def all_adapters() -> list[AgentAdapter]:
    return [
        OpenClawAdapter(),
        NanobotAdapter(),
        ClaudeCodeAdapter(),
        CodexAdapter(),
        MCPGenericAdapter(),
    ]


def detect_adapter(path: Path) -> AgentAdapter:
    for adapter in all_adapters():
        if adapter.detect(path):
            return adapter
    raise ValueError(f"Could not detect supported agent at {path}")
