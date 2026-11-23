---
name: setup
description: Provisions the oracle daemon's venv via uv. Use when setting up local model scoring for skill quality evaluation.
---

# Oracle Setup

Provision the ML inference environment.

## When NOT To Use

- The daemon is already provisioned and only needs to be used
- Evaluating skill quality itself (use `abstract:skills-eval`)

## What This Does

1. Creates a Python 3.11+ virtual environment using uv
2. Installs pyyaml into the venv (onnxruntime waits for an ONNX model)
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
3. If successful, tell the user the daemon starts on the next
   session once a `models/` directory exists in the plugin. None
   ships yet, so until then the hook logs "models directory
   missing" to `daemon.log` and consumers use local scoring.
4. If failed, show the error and suggest checking uv and network.

## Exit Criteria

- [ ] `provision_venv()` returns a result with a non-error `message`
  and the venv path exists on disk under `plugins/oracle/`
- [ ] `yaml` is importable inside the provisioned venv; verified by
  running the venv's python with `-c "import yaml"` and exit code 0
- [ ] User receives a success message that states the daemon needs a
  `models/` directory to start, or a failure message citing the
  specific error and whether it is a uv or network issue
- [ ] On failure, no partial venv left in a broken state that would
  prevent a clean retry
