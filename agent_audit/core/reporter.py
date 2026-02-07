from __future__ import annotations

from io import StringIO
import json
from typing import Literal

from agent_audit.types import ScanResult

try:
    from rich.console import Console
    from rich.table import Table

    HAS_RICH = True
except ImportError:  # pragma: no cover - fallback for minimal envs
    HAS_RICH = False


def _table_with_rich(result: ScanResult) -> str:
    buffer = StringIO()
    console = Console(file=buffer, force_terminal=False, color_system=None)
    console.print(f"agent-audit scan :: {result.agent_name} ({result.adapter_name})")
    console.print(f"Risk Score: {result.risk_score:.1f}/10 [{result.risk_tier}]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Check")
    table.add_column("Severity")
    table.add_column("Score")
    table.add_column("Summary")

    for check in result.checks.values():
        table.add_row(check.title, check.severity.upper(), f"{check.score:.1f}", check.summary)

    console.print(table)
    return buffer.getvalue().rstrip()


def _table_plain(result: ScanResult) -> str:
    lines = [
        f"agent-audit scan :: {result.agent_name} ({result.adapter_name})",
        f"Risk Score: {result.risk_score:.1f}/10 [{result.risk_tier}]",
        "",
    ]
    for check in result.checks.values():
        lines.append(f"- {check.title}: {check.severity.upper()} ({check.score:.1f})")
        lines.append(f"  {check.summary}")
        for detail in check.details:
            lines.append(f"  * {detail}")
    return "\n".join(lines)


def to_markdown(result: ScanResult) -> str:
    lines = [
        f"# agent-audit report: {result.agent_name}",
        "",
        f"- adapter: `{result.adapter_name}`",
        f"- path: `{result.scanned_path}`",
        f"- risk: **{result.risk_score:.1f}/10 ({result.risk_tier})**",
        "",
        "| Check | Severity | Score | Summary |",
        "|---|---:|---:|---|",
    ]
    for check in result.checks.values():
        lines.append(
            f"| {check.title} | {check.severity.upper()} | {check.score:.1f} | {check.summary} |"
        )
    return "\n".join(lines)


def render(
    result: ScanResult,
    output_format: Literal["table", "json", "markdown"] = "table",
) -> str:
    if output_format == "json":
        return json.dumps(result.to_dict(), indent=2)
    if output_format == "markdown":
        return to_markdown(result)
    if HAS_RICH:
        return _table_with_rich(result)
    return _table_plain(result)
