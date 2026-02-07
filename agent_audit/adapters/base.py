from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from agent_audit.types import AgentConfig, Skill


class AgentAdapter(Protocol):
    name: str

    def detect(self, path: Path) -> bool:
        """Return True if this adapter matches the path."""

    def get_config(self, path: Path) -> AgentConfig:
        """Parse and normalize config."""

    def get_skills(self, path: Path) -> list[Skill]:
        """Return normalized skills/plugins."""

    def get_endpoints(self, path: Path) -> list[str]:
        """Return configured endpoints."""


@dataclass(slots=True)
class AdapterMatch:
    adapter: AgentAdapter
    path: Path
