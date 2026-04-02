# oracle

ONNX Runtime inference daemon for ML-enhanced plugin capabilities.

Provides local model inference over HTTP with explicit opt-in
activation. The daemon runs in an isolated Python 3.11+ venv so
the inference stack (onnxruntime, aiohttp) does not affect the
system Python 3.9 environment used by hooks.

## Activation

Opt in by running the setup command:

```
/oracle:setup
```

This creates a venv, installs onnxruntime, and writes an
`.oracle-enabled` sentinel. The `SessionStart` hook starts the
daemon only when that sentinel is present.

## Architecture

Oracle is a marketplace-installable plugin with explicit
opt-in activation.
Installing the plugin does nothing until the user runs
`/oracle:setup`, which provisions a Python 3.11+ venv via
`uv` and installs `onnxruntime` into it.
The daemon runs as an HTTP server bound to `127.0.0.1` and
writes its port number to a file that consumer plugins read
for discovery (`$CLAUDE_PLUGIN_DATA/oracle/daemon.port`).
`SessionStart` and `SessionEnd` hooks manage the daemon
lifecycle so no background processes outlive a session.
Uninstalling oracle causes zero errors in consumer plugins;
they detect the missing port file and fall back to local
scoring.

Key files:

- `hooks/daemon_lifecycle.py` -- starts/stops the HTTP daemon
- `src/oracle/provision.py` -- venv provisioning logic
- `skills/setup/` -- guided setup skill
- `commands/oracle-setup.md` -- `/oracle:setup` slash command
