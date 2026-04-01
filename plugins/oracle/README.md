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

- `hooks/daemon_lifecycle.py` -- starts/stops the HTTP daemon
- `src/oracle/provision.py` -- venv provisioning logic
- `skills/setup/` -- guided setup skill
- `commands/oracle-setup.md` -- `/oracle:setup` slash command
