from pathlib import Path

from agent_audit.adapters import detect_adapter


FIXTURES = Path(__file__).parent / "fixtures"


def test_detects_openclaw_fixture() -> None:
    adapter = detect_adapter(FIXTURES / "openclaw_basic")
    assert adapter.name == "openclaw"


def test_detects_codex_fixture() -> None:
    adapter = detect_adapter(FIXTURES / "codex_scoped")
    assert adapter.name == "codex"
