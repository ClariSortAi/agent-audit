from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import Iterable


@dataclass(slots=True)
class MonitorEvent:
    kind: str
    target: str
    severity: str = "low"
    timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    )


@dataclass(slots=True)
class MonitorSummary:
    events: int
    alerts_high: int
    alerts_medium: int


class SessionMonitor:
    def __init__(self) -> None:
        self._events: list[MonitorEvent] = []

    def record(self, event: MonitorEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> list[MonitorEvent]:
        return list(self._events)

    def summarize(self) -> MonitorSummary:
        high = sum(1 for event in self._events if event.severity.lower() in {"high", "critical"})
        medium = sum(1 for event in self._events if event.severity.lower() == "medium")
        return MonitorSummary(events=len(self._events), alerts_high=high, alerts_medium=medium)


SENSITIVE_PATH_MARKERS = {
    ".ssh",
    ".aws",
    ".gnupg",
    ".env",
    "/etc",
    "/var/lib",
}


def _timestamp() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def _is_proc_alive(pid: int) -> bool:
    return Path(f"/proc/{pid}").exists()


def _all_process_ids() -> list[int]:
    proc_dir = Path("/proc")
    pids: list[int] = []
    for child in proc_dir.iterdir():
        if child.name.isdigit():
            pids.append(int(child.name))
    return pids


def _read_ppid(pid: int) -> int | None:
    stat_path = Path(f"/proc/{pid}/stat")
    try:
        data = stat_path.read_text(encoding="utf-8")
    except OSError:
        return None
    fields = data.split()
    if len(fields) < 4:
        return None
    try:
        return int(fields[3])
    except ValueError:
        return None


def _collect_descendants(root_pid: int) -> set[int]:
    pids = _all_process_ids()
    parent_map: dict[int, int] = {}
    for pid in pids:
        ppid = _read_ppid(pid)
        if ppid is not None:
            parent_map[pid] = ppid

    descendants = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, ppid in parent_map.items():
            if ppid in descendants and pid not in descendants:
                descendants.add(pid)
                changed = True
    return descendants


def _cmdline_for_pid(pid: int) -> str:
    cmdline = Path(f"/proc/{pid}/cmdline")
    try:
        raw = cmdline.read_bytes()
    except OSError:
        return f"pid:{pid}"
    parts = [part.decode("utf-8", errors="replace") for part in raw.split(b"\x00") if part]
    return " ".join(parts) if parts else f"pid:{pid}"


def _severity_for_exec(command: str) -> str:
    lower = command.lower()
    if any(token in lower for token in ("sudo ", "curl ", "wget ", "nc ", "ssh ")):
        return "high"
    if any(token in lower for token in ("python", "node", "bash", "sh ")):
        return "medium"
    return "low"


def _severity_for_file(path: str, is_write: bool, project_root: Path | None) -> str:
    lower = path.lower()
    if lower == "/dev/null" or lower.startswith("/dev/pts/"):
        return "low"
    if any(marker in lower for marker in SENSITIVE_PATH_MARKERS):
        return "critical"
    if project_root:
        target = Path(path)
        if target.is_absolute():
            try:
                target.relative_to(project_root)
            except ValueError:
                return "high" if is_write else "medium"
    return "medium" if is_write else "low"


def _parse_flags(flags_value: str) -> int | None:
    try:
        return int(flags_value.strip(), 8)
    except ValueError:
        return None


def _decode_ipv4(raw: str) -> str:
    try:
        packed = bytes.fromhex(raw)
    except ValueError:
        return raw
    if len(packed) != 4:
        return raw
    octets = [str(value) for value in packed[::-1]]
    return ".".join(octets)


def _load_socket_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for proc_file, proto in (("/proc/net/tcp", "tcp"), ("/proc/net/udp", "udp")):
        path = Path(proc_file)
        if not path.exists():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 10:
                continue
            remote = parts[2]
            inode = parts[9]
            if ":" not in remote:
                continue
            ip_hex, port_hex = remote.split(":", 1)
            endpoint = f"{_decode_ipv4(ip_hex)}:{int(port_hex, 16)}"
            index[inode] = f"{proto}://{endpoint}"
    return index


class ProcessMonitor:
    def __init__(self, pid: int, project_root: Path | None = None) -> None:
        self.pid = pid
        self.project_root = project_root.resolve() if project_root else None
        self.session = SessionMonitor()
        self._seen_exec_pids: set[int] = {pid}
        self._seen_files: set[tuple[int, str, bool]] = set()
        self._seen_socket_inodes: set[str] = set()

    def _iter_fd_paths(self, pid: int) -> list[Path]:
        fd_dir = Path(f"/proc/{pid}/fd")
        if not fd_dir.exists():
            return []
        try:
            return list(fd_dir.iterdir())
        except (OSError, PermissionError):
            return []

    def _file_events_for_pid(self, pid: int) -> list[MonitorEvent]:
        events: list[MonitorEvent] = []
        for fd_path in self._iter_fd_paths(pid):
            try:
                target = fd_path.readlink()
            except OSError:
                continue
            target_str = str(target)
            if not target_str.startswith("/"):
                continue

            fdinfo = Path(f"/proc/{pid}/fdinfo/{fd_path.name}")
            is_write = False
            try:
                info = fdinfo.read_text(encoding="utf-8")
            except OSError:
                info = ""
            for line in info.splitlines():
                if line.startswith("flags:"):
                    _, value = line.split(":", 1)
                    flags = _parse_flags(value)
                    if flags is not None and (flags & 0o3) in {1, 2}:
                        is_write = True
                    break

            entry = (pid, target_str, is_write)
            if entry in self._seen_files:
                continue
            self._seen_files.add(entry)

            event = MonitorEvent(
                kind="WRITE" if is_write else "READ",
                target=target_str,
                severity=_severity_for_file(target_str, is_write, self.project_root),
                timestamp=_timestamp(),
            )
            events.append(event)
        return events

    def _socket_events_for_pid(self, pid: int, socket_index: dict[str, str]) -> list[MonitorEvent]:
        events: list[MonitorEvent] = []
        for fd_path in self._iter_fd_paths(pid):
            try:
                link = fd_path.readlink()
            except OSError:
                continue
            value = str(link)
            if not value.startswith("socket:[") or not value.endswith("]"):
                continue
            inode = value[len("socket:[") : -1]
            if inode in self._seen_socket_inodes:
                continue
            self._seen_socket_inodes.add(inode)
            endpoint = socket_index.get(inode, f"socket_inode:{inode}")
            severity = "medium"
            if "127.0.0.1" in endpoint or "0.0.0.0" in endpoint:
                severity = "low"
            event = MonitorEvent(kind="NETWORK", target=endpoint, severity=severity, timestamp=_timestamp())
            events.append(event)
        return events

    def _exec_events(self, descendants: Iterable[int]) -> list[MonitorEvent]:
        events: list[MonitorEvent] = []
        for pid in descendants:
            if pid in self._seen_exec_pids:
                continue
            self._seen_exec_pids.add(pid)
            command = _cmdline_for_pid(pid)
            events.append(
                MonitorEvent(
                    kind="EXEC",
                    target=command,
                    severity=_severity_for_exec(command),
                    timestamp=_timestamp(),
                )
            )
        return events

    def poll(self) -> list[MonitorEvent]:
        if not _is_proc_alive(self.pid):
            return []
        descendants = _collect_descendants(self.pid)
        socket_index = _load_socket_index()
        events: list[MonitorEvent] = []
        events.extend(self._exec_events(descendants))
        for pid in descendants:
            events.extend(self._file_events_for_pid(pid))
            events.extend(self._socket_events_for_pid(pid, socket_index))
        for event in events:
            self.session.record(event)
        return events

    def run(
        self,
        duration_seconds: float,
        interval_seconds: float = 0.5,
    ) -> list[MonitorEvent]:
        deadline = datetime.now(tz=timezone.utc).timestamp() + duration_seconds
        collected: list[MonitorEvent] = []
        while datetime.now(tz=timezone.utc).timestamp() < deadline:
            if not _is_proc_alive(self.pid):
                break
            collected.extend(self.poll())
            sleep(interval_seconds)
        return collected
