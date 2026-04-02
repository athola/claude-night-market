# oracle

Local ONNX Runtime inference daemon for ML-enhanced plugin
capabilities.

## Overview

Oracle runs a sidecar HTTP daemon that serves ONNX model inference
on localhost. Plugins opt in explicitly by writing a sentinel file.
It uses a dedicated Python 3.11+ venv managed by `uv` and does not
touch the system Python environment.

## Installation

```bash
/plugin install oracle@claude-night-market
```

## Skills

- `setup` - Install and configure the oracle ONNX inference daemon

## Commands

- `/oracle-setup` - Install and configure the oracle ONNX inference
  daemon, including venv creation and model placement
