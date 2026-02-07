from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Literal

import typer

from agent_audit import __version__
from agent_audit.core.monitor import ProcessMonitor
from agent_audit.core.reporter import render
from agent_audit.core.scanner import Scanner

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _fail(message: str, code: int = 2) -> None:
    typer.secho(message, fg=typer.colors.RED, err=True)
    raise typer.Exit(code=code)


@app.command()
def version() -> None:
    """Print version."""
    typer.echo(__version__)


@app.command()
def scan(
    path: Path = typer.Argument(Path("."), help="Agent directory to scan"),
    output_format: Literal["table", "json", "markdown"] = typer.Option(
        "table", "--format", help="Output format"
    ),
) -> None:
    """Statically scan an agent configuration."""
    scanner = Scanner()
    try:
        result = scanner.scan_path(path)
    except ValueError as exc:
        _fail(str(exc))
    typer.echo(render(result, output_format=output_format))


@app.command()
def compare(
    path_one: Path = typer.Argument(..., help="First agent path"),
    path_two: Path = typer.Argument(..., help="Second agent path"),
    output_format: Literal["table", "json", "markdown"] = typer.Option(
        "table", "--format", help="Output format"
    ),
) -> None:
    """Compare two agent scan results."""
    scanner = Scanner()
    try:
        first = scanner.scan_path(path_one)
        second = scanner.scan_path(path_two)
    except ValueError as exc:
        _fail(str(exc))

    payload = {
        "left": {
            "path": str(path_one),
            "name": first.agent_name,
            "adapter": first.adapter_name,
            "risk_score": first.risk_score,
            "risk_tier": first.risk_tier,
            "checks": {key: check.severity for key, check in first.checks.items()},
        },
        "right": {
            "path": str(path_two),
            "name": second.agent_name,
            "adapter": second.adapter_name,
            "risk_score": second.risk_score,
            "risk_tier": second.risk_tier,
            "checks": {key: check.severity for key, check in second.checks.items()},
        },
    }

    if output_format == "json":
        typer.echo(json.dumps(payload, indent=2))
        return

    lines = [
        "| Metric | Agent 1 | Agent 2 |",
        "|---|---:|---:|",
        f"| Name | {first.agent_name} | {second.agent_name} |",
        (
            f"| Risk score | {first.risk_score:.1f} ({first.risk_tier}) | "
            f"{second.risk_score:.1f} ({second.risk_tier}) |"
        ),
        (
            f"| File system | {first.checks['filesystem'].severity.upper()} | "
            f"{second.checks['filesystem'].severity.upper()} |"
        ),
        (
            f"| Network | {first.checks['network'].severity.upper()} | "
            f"{second.checks['network'].severity.upper()} |"
        ),
        f"| Shell | {first.checks['shell'].severity.upper()} | {second.checks['shell'].severity.upper()} |",
        (
            f"| Secrets | {first.checks['secrets'].severity.upper()} | "
            f"{second.checks['secrets'].severity.upper()} |"
        ),
        f"| Skills | {first.checks['skills'].severity.upper()} | {second.checks['skills'].severity.upper()} |",
    ]
    rendered = "\n".join(lines)
    if output_format == "markdown":
        typer.echo(rendered)
        return
    typer.echo(rendered)


def _render_event_line(kind: str, target: str, severity: str, timestamp: str) -> str:
    return f"{timestamp} [{severity.upper()}] {kind:<7} {target}"


@app.command()
def monitor(
    pid: int | None = typer.Option(None, "--pid", help="PID of the agent process to monitor"),
    command: str | None = typer.Option(
        None,
        "--exec",
        help="Command to launch and monitor (example: --exec 'openclaw run')",
    ),
    duration: float = typer.Option(20.0, "--duration", min=1.0, help="Duration in seconds"),
    interval: float = typer.Option(
        0.5,
        "--interval",
        min=0.1,
        help="Polling interval in seconds",
    ),
    path: Path | None = typer.Option(
        None,
        "--path",
        help="Project root path used for file-scope severity classification",
    ),
    live: bool = typer.Option(False, "--live", help="Stream events as they are collected"),
    output_format: Literal["table", "json"] = typer.Option("table", "--format", help="Output format"),
) -> None:
    """Monitor a running agent process by PID."""
    if pid is None and command is None:
        raise typer.BadParameter("Provide either --pid or --exec.")
    if pid is not None and command is not None:
        raise typer.BadParameter("Use only one of --pid or --exec.")

    proc: subprocess.Popen[bytes] | None = None
    target_pid = pid
    if command is not None:
        proc = subprocess.Popen(
            command,
            shell=True,  # noqa: S602
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        target_pid = proc.pid

    if target_pid is None:
        raise typer.BadParameter("Could not determine process PID for monitoring.")
    if not Path(f"/proc/{target_pid}").exists():
        _fail(f"PID {target_pid} is not running or not visible from this namespace.")

    try:
        monitor = ProcessMonitor(pid=target_pid, project_root=path)
        events = monitor.run(duration_seconds=duration, interval_seconds=interval)
        summary = monitor.session.summarize()

        if live:
            for event in events:
                typer.echo(_render_event_line(event.kind, event.target, event.severity, event.timestamp))

        if output_format == "json":
            payload = {
                "pid": target_pid,
                "command": command,
                "duration_seconds": duration,
                "events": [
                    {
                        "timestamp": event.timestamp,
                        "kind": event.kind,
                        "target": event.target,
                        "severity": event.severity,
                    }
                    for event in events
                ],
                "summary": {
                    "events": summary.events,
                    "alerts_high": summary.alerts_high,
                    "alerts_medium": summary.alerts_medium,
                },
            }
            typer.echo(json.dumps(payload, indent=2))
            return

        typer.echo(
            f"Session summary: events={summary.events} high={summary.alerts_high} medium={summary.alerts_medium}"
        )
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()


if __name__ == "__main__":
    app()
