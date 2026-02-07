from pathlib import Path

from agent_audit.core.scanner import Scanner


FIXTURES = Path(__file__).parent / "fixtures"


def test_scan_openclaw_fixture_is_high_risk() -> None:
    result = Scanner().scan_path(FIXTURES / "openclaw_basic")
    assert result.adapter_name == "openclaw"
    assert result.risk_score >= 7.0
    assert result.risk_tier in {"HIGH", "CRITICAL"}


def test_scan_codex_fixture_is_lower_risk() -> None:
    result = Scanner().scan_path(FIXTURES / "codex_scoped")
    assert result.adapter_name == "codex"
    assert result.risk_score < 7.0
