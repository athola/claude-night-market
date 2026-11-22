# ADR-0009: Sidecar Service Discovery via Port Files

**Date**: 2026-04-01
**Status**: Accepted, amended 2026-11-22 (see the amendment below)
**Deciders**: Claude Night Market maintainers

## Context

ADR-0001 established filesystem-based plugin detection for
inter-plugin communication.
That pattern works well for code that runs inside the Claude Code
process (skills, hooks, Python imports).
However, the oracle plugin introduces a new class of interaction:
a long-running **sidecar daemon** that serves ML inference over
localhost HTTP.

This is a qualitative shift from file-based detection to
process-level communication.
Without a documented pattern, each plugin that adds a sidecar
process would invent its own discovery mechanism, leading to
inconsistent port management, lifecycle handling, and failure
modes.

## Research Background

Five research channels informed this decision on 2026-03-31. The
load-bearing findings are recorded below rather than in a separate
report.
The ONNX Python API provides model construction, validation,
and protobuf serialization through core modules like
`onnx.helper` and `onnx.checker`.
GitHub code search across nine repositories found that the
sidecar process is the dominant inference isolation pattern,
used by Copilot, Tabnine, and Continue.
Community discourse identified silent failures as the top
risk: 33% of ONNX converter failures produce semantically
incorrect models rather than errors (ISSTA 2024).
TRIZ cross-domain analysis resolved the contradiction between
ML capability and deployment simplicity through a tiered
architecture: Tier 0 (YAML coefficients, zero deps), Tier 1
(rule-based heuristics), Tier 2 (sidecar ONNX daemon in an
isolated venv), and Tier 3 (Claude API).
The critical constraint driving the sidecar pattern is that
onnxruntime requires Python 3.11+, while the system Python
is 3.9.6.
The sidecar isolates the inference runtime in its own venv,
keeping host plugins on the system Python.

## Decision

Plugins that run sidecar processes MUST follow this pattern:

### 1. Port File Discovery

The daemon writes its bound port number to a well-known file
after startup.
Clients read this file to discover the daemon's address.

```
${CLAUDE_PLUGIN_DATA}/daemon.port
```

`CLAUDE_PLUGIN_DATA` is already per-plugin: Claude Code 2.1.78+
names `~/.claude/plugins/data/<plugin>-<marketplace>/`. A client in
another plugin finds the daemon's directory as a sibling of its own
data directory with the plugin name swapped, keeping the
`-<marketplace>` suffix. `leyline/plugin_data.py` resolves only the
calling plugin's own directory. The sibling rule is re-derived where it
is used: gauntlet swaps the `gauntlet-` prefix
(`gauntlet/ml/__init__.py`), and abstract matches the install path
(`abstract/scripts/insight_palace_bridge.py`, mirroring
`memory_palace.paths._install_layout`). A change to the host's layout
must update all three.

Fallback location when `CLAUDE_PLUGIN_DATA` is not set:

```
~/.oracle-inference/daemon.port    # oracle example
~/.<plugin-name>/daemon.port       # general pattern
```

The port file MUST contain only the decimal port number
followed by a newline.
The file MUST be deleted on daemon shutdown.

### 2. PID File

The daemon's PID is tracked in a sibling file:

```
${CLAUDE_PLUGIN_DATA}/daemon.pid
```

This enables lifecycle hooks to stop the daemon cleanly.

### 3. Localhost-Only Binding

Sidecar daemons MUST bind to `127.0.0.1`.
Binding to `0.0.0.0` or any routable address is prohibited.
No authentication is required for localhost-only daemons,
but daemons MUST NOT accept connections from other hosts.

### 4. Health Endpoint

Every sidecar MUST expose `GET /health` returning:

```json
{"status": "ok"}
```

Clients use this to verify the daemon is running and healthy
before sending requests.
The health check MUST respond within 1 second.

### 5. Opt-In Activation

Sidecar daemons MUST NOT start automatically.
Activation requires an explicit sentinel file:

```
${CLAUDE_PLUGIN_DATA}/.oracle-enabled
```

The sentinel is created by a user-facing setup command
(e.g., `/oracle:setup`).

### 6. Lifecycle Management

Daemon start and stop MUST be handled by SessionStart and SessionEnd
hooks respectively. Amended 2026-11-22: this read Stop, which fires
after every assistant turn.
The start hook MUST:

- Check the sentinel file exists
- Check any required runtime (venv, binary) is provisioned
- Launch the daemon as a detached subprocess
- Write the PID file
- Exit within the hook timeout budget (5 seconds)

The stop hook MUST:

- Send SIGTERM to the daemon PID
- Clean up PID and port files

### 7. Client Graceful Degradation

Consumer plugins that call a sidecar MUST follow ADR-0001's
isolation pattern:

- Detect the sidecar via port file existence
- Attempt a health check before first use
- Fall back to local logic when the sidecar is unavailable
- Never import code from the sidecar plugin directly

## Architecture

```
┌──────────────┐     writes      ┌──────────────┐
│  Lifecycle   │───────────────▶ │  daemon.pid  │
│    Hook      │                 │  daemon.port │
│ (SessionStart│                 │  .enabled    │
│ / SessionEnd)│                 └──────┬───────┘
└──────┬───────┘                        │
       │ launches / kills               │ reads
       ▼                                ▼
┌──────────────┐     HTTP        ┌──────────────┐
│   Sidecar    │◀────────────────│   Consumer   │
│   Daemon     │  /health        │   Plugin     │
│  (127.0.0.1) │  /infer         │              │
└──────────────┘                 └──────────────┘
```

## Consequences

This pattern extends ADR-0001 to cover process-level
interactions.
It formalizes the port-file-based discovery that oracle
introduced and prevents ad-hoc approaches in future plugins.

Benefits:

- Consistent discovery mechanism across all sidecar plugins
- Clean lifecycle tied to Claude Code session boundaries
- Explicit opt-in prevents surprise resource consumption
- Localhost binding eliminates network attack surface

Tradeoffs:

- Port files are a simple but fragile mechanism
  (stale files from crashes require cleanup)
- Each consumer reimplements the HTTP client per ADR-0001
- The 5-second hook timeout limits startup complexity

## Amendment 2026-11-22: No onnxruntime, SessionEnd, shared daemon

The constraint in Research Background no longer drives the sidecar.
`oracle/src/oracle/provision.py` creates the venv with pyyaml only,
and no ONNX model ships. The daemon serves YAML linear and sigmoid
models with `math` and `yaml`. The system Python 3.9.6 that runs hooks
has no pyyaml, and the `provision_venv` docstring defers onnxruntime
until an ONNX model ships. Without a `models` directory the start hook
logs one line and launches nothing.

The stop hook is a SessionEnd hook. A Stop hook fires after every
assistant turn and stopped the daemon after the session's first reply.

One daemon serves every session on the machine. A session ending must
not stop it while another session uses it, and the lifecycle hook
counts sessions with marker files:

- SessionStart writes `${CLAUDE_PLUGIN_DATA}/sessions/<session_id>`
  holding the pid of the session's process. That is the first
  ancestor of the hook that is not a shell, since a `sh -c` wrapper
  exits with the hook.
- SessionEnd deletes its own marker and stops the daemon only when no
  other marker is live. A marker is live while its process runs. A
  marker with no readable pid, and every marker on Windows, is live
  for 24 hours after it was written.
- A SessionEnd with reason `clear` never stops the daemon, because
  the same process starts a new session at once.

Both events hold an exclusive `flock` on
`${CLAUDE_PLUGIN_DATA}/daemon.start.lock`. SessionStart holds it across
the running check and the spawn, and two sessions starting together
launch one daemon. SessionEnd holds it across the marker check and the
stop. A daemon another session has just found running is not stopped
under it. Windows has no `fcntl`, and there the lock is skipped.

## Related

- ADR-0001: Plugin Dependency Isolation
- `plugins/oracle/` - Reference implementation
- `plugins/gauntlet/src/gauntlet/ml/scorer.py` -
  Reference consumer (`OnnxSidecarScorer`)
