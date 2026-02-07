from pathlib import Path
import os

import pytest

from agent_audit.core.monitor import (
    MonitorEvent,
    ProcessMonitor,
    SessionMonitor,
    _severity_for_file,
)


def test_monitor_summary_counts_alerts() -> None:
    monitor = SessionMonitor()
    monitor.record(MonitorEvent(kind="READ", target="file.txt", severity="low"))
    monitor.record(MonitorEvent(kind="EXEC", target="npm install", severity="medium"))
    monitor.record(MonitorEvent(kind="READ", target="~/.ssh/id_rsa", severity="critical"))

    summary = monitor.summarize()
    assert summary.events == 3
    assert summary.alerts_medium == 1
    assert summary.alerts_high == 1


def test_file_severity_sensitive_path_is_critical() -> None:
    severity = _severity_for_file("/home/user/.ssh/id_rsa", is_write=False, project_root=None)
    assert severity == "critical"


def test_file_severity_dev_null_is_low() -> None:
    severity = _severity_for_file("/dev/null", is_write=True, project_root=None)
    assert severity == "low"


def test_file_severity_outside_project_write_is_high(tmp_path: Path) -> None:
    severity = _severity_for_file("/opt/other/file.txt", is_write=True, project_root=tmp_path)
    assert severity == "high"


def test_process_monitor_runs_on_current_pid() -> None:
    monitor = ProcessMonitor(pid=os.getpid())
    events = monitor.run(duration_seconds=1.0, interval_seconds=0.2)
    assert isinstance(events, list)


def test_iter_fd_paths_handles_permission_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monitor = ProcessMonitor(pid=os.getpid())

    def _raise_permission(_self: Path) -> list[Path]:
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "iterdir", _raise_permission)
    assert monitor._iter_fd_paths(os.getpid()) == []
