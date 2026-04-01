---
description: Install and activate the oracle ONNX inference daemon
model_hint: standard
---

# Oracle Setup

Invoke `Skill(oracle:setup)` to install the oracle daemon.

This provisions a Python 3.11+ venv with onnxruntime and writes
the `.oracle-enabled` opt-in sentinel so the daemon starts
automatically on future sessions.

## Arguments

- No args: run full setup from scratch
- `--check`: report current provisioning status without changes
- `--reprovision`: tear down and rebuild the venv
