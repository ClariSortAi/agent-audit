from __future__ import annotations

import json
import os
from pathlib import Path

from typer.testing import CliRunner

from agent_audit.cli import app


FIXTURES = Path(__file__).parent / "fixtures"


def test_compare_json_output() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "compare",
            str(FIXTURES / "openclaw_basic"),
            str(FIXTURES / "codex_scoped"),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["left"]["name"] == "OpenClaw"
    assert payload["right"]["name"] == "Codex"


def test_scan_table_output_not_duplicated() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "scan",
            str(FIXTURES / "openclaw_basic"),
            "--format",
            "table",
        ],
    )
    assert result.exit_code == 0
    assert result.stdout.count("agent-audit scan ::") == 1


def test_scan_unknown_path_returns_user_error() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["scan", "/tmp/aa-does-not-exist"])
    assert result.exit_code == 2
    assert "Could not detect supported agent" in result.stderr
    assert "Traceback" not in result.stdout


def test_monitor_json_output() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "monitor",
            "--pid",
            str(os.getpid()),
            "--duration",
            "1",
            "--interval",
            "0.2",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["pid"] == os.getpid()
    assert "summary" in payload


def test_monitor_exec_json_output() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "monitor",
            "--exec",
            "sleep 1",
            "--duration",
            "1",
            "--interval",
            "0.2",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "sleep 1"


def test_monitor_requires_pid_or_exec() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["monitor", "--duration", "1"])
    assert result.exit_code != 0


def test_monitor_nonexistent_pid_fails_cleanly() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "monitor",
            "--pid",
            "999999",
            "--duration",
            "1",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 2
    assert "not running or not visible" in result.stderr


def test_monitor_exec_json_output_ignores_child_stdout() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "monitor",
            "--exec",
            "printf noisy-output",
            "--duration",
            "1",
            "--interval",
            "0.2",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "printf noisy-output"


def test_compare_unknown_path_returns_user_error() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "compare",
            "/tmp/aa-empty",
            str(FIXTURES / "codex_scoped"),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 2
    assert "Could not detect supported agent" in result.stderr
