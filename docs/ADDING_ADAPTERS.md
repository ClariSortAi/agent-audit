# Adding Adapters

Create one file under `agent_audit/adapters/` and implement `AgentAdapter`.

Required methods:
- `detect(path: Path) -> bool`
- `get_config(path: Path) -> AgentConfig`
- `get_skills(path: Path) -> list[Skill]`
- `get_endpoints(path: Path) -> list[str]`

Then register the adapter in `agent_audit/adapters/__init__.py`.

Use conservative defaults: if config keys are missing, return least privilege assumptions only when explicitly declared.
