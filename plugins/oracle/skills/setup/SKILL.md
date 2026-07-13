---
name: setup
description: Provisions the oracle ML inference daemon with onnxruntime via uv. Use when setting up local ONNX model inference for skill quality evaluation.
---

# Oracle Setup

Provision the ML inference environment.

## When NOT To Use

- The daemon is already provisioned and only needs to be used
- Evaluating skill quality itself (use `abstract:skills-eval`)

## What This Does

1. Creates a Python 3.11+ virtual environment using uv
2. Installs onnxruntime into the venv
3. Verifies the installation

## Prerequisites

- uv must be installed
- Internet connection for initial download

## Steps

1. Run provisioning:

```bash
cd plugins/oracle && uv run python -c "
from oracle.provision import provision_venv, get_venv_path
result = provision_venv(get_venv_path())
print(result.message)
"
```

2. Report result to the user.
3. If successful, tell the user the daemon will start on next session.
4. If failed, show the error and suggest checking uv and network.

## Exit Criteria

- [ ] `provision_venv()` returns a result with a non-error `message`
  and the venv path exists on disk under `plugins/oracle/`
- [ ] `onnxruntime` is importable inside the provisioned venv;
  verified by `uv run python -c "import onnxruntime"` exiting 0
- [ ] User receives a clear success message stating the daemon will
  start on next session, or a clear failure message citing the
  specific error and whether it is a uv or network issue
- [ ] On failure, no partial venv left in a broken state that would
  prevent a clean retry
