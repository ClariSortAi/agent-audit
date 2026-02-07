# Architecture

`agent-audit` uses a plugin-first static scanning pipeline:

1. Adapter registry auto-detects agent type from config/manifests.
2. Adapter normalizes raw config into `AgentConfig` + `Skill` + endpoints.
3. Check modules compute per-domain risk findings.
4. Risk engine computes weighted 0-10 score.
5. Reporter renders table/json/markdown output.

Core constraint: no runtime import of agent code. Only config/manifests are read.

Runtime monitoring is implemented as a PID-based poller (`ProcessMonitor`) that reads `/proc` state
for file descriptors, sockets, and child processes, then emits normalized `MonitorEvent` entries.
