---
name: setup
description: >
  Install and configure the oracle ONNX inference daemon,
  including venv creation, model placement, and activation.
model_hint: standard
---

# Oracle Setup

Guides the user through installing and activating the oracle
daemon for local ONNX model inference.

## Steps

1. Check Python 3.11+ availability for the daemon venv.
2. Create `plugins/oracle/.oracle-venv` with onnxruntime and
   aiohttp installed.
3. Verify or place ONNX model files under
   `plugins/oracle/models/`.
4. Write `plugins/oracle/.oracle-enabled` sentinel to opt in.
5. Confirm the daemon responds on `http://localhost:18080`.
