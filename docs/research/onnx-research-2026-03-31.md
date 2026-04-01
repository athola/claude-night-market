# ONNX Integration Research Report

**Date:** 2026-03-31
**Channels:** 5 (ONNX API, GitHub code, community discourse,
academic literature, TRIZ cross-domain)
**Purpose:** Inform integration of ONNX ML inference into the
claude-night-market plugin ecosystem

## Channel 1: ONNX Python API

Source: https://onnx.ai/onnx/intro/python.html

Core modules: `onnx.helper` (model construction),
`onnx.checker` (validation), `onnx.shape_inference`,
`onnx.version_converter`, `onnx.numpy_helper`,
`onnx.parser`.

Model creation via `make_tensor_value_info()`,
`make_node()`, `make_graph()`, `make_model()`.
Serialization via protobuf. Alternative: ir-py project
for more ergonomic APIs.

## Channel 2: GitHub Code Search (9 repositories)

**Highest relevance:**

- **microsoft/onnxruntime-genai** (992 stars): LLM
  inference with tool-calling grammar on ONNX Runtime.
  Strongest bridge between ONNX and agentic patterns.
- **microsoft/onnxruntime-extensions** (454 stars):
  Plugin architecture for custom operators via shared
  library registration.
- **ruvnet/onnx-agent** (17 stars): End-to-end agent
  pipeline (DSPy training to ONNX export to inference).
  Only project explicitly building an "agent" around ONNX.

**Key patterns:**

- Optional extras (`pip install pkg[onnx]`) is the
  dominant packaging pattern
- Sidecar process is the dominant inference isolation
  pattern (Copilot, Tabnine, Continue)
- No existing LLM agent framework has native ONNX
  integration

## Channel 3: Community Discourse (15 findings)

**Top pain point:** Silent failures. Multiple independent
sources converge: ONNX models that convert without errors
but produce wrong outputs are the most dangerous bug class.

**Performance:** Not guaranteed. Best case: 96% latency
reduction, 84% memory reduction, 28x throughput. Worst
case: 2-3x slower than PyTorch (GitHub issue #12880).

**Quantization:** TFLite's is "most polished"; ONNX
quantization "still feels a step behind." QUINT8 can
produce unusable artifacts for visual tasks.

**Contrarian view:** For single-platform deployments,
ONNX adds an unnecessary conversion step. Its value is
strongest for cross-platform or PyTorch-to-production-CPU
pipelines.

## Channel 4: Academic Literature (10 papers)

**ISSTA 2024 (Jajal et al.):** Surveyed 92 engineers,
analyzed 200 GitHub issues. 75% of defects are node
conversion. 33% of failures produce semantically incorrect
models. Real models: 75% success rate.

**DiTOX (2025):** 9.2% crash rate in ONNX optimizer.
30% of classification models diverge after optimization.
15 previously unknown bugs found.

**PickleBall (CCS 2025):** ONNX is inherently more
secure than pickle (no arbitrary code execution). But
CVE-2026-28500 shows onnx.hub.load() has a trust bypass.

**Benchmarks (Electronics 2025):** TensorRT consistently
faster than ONNX Runtime on NVIDIA. ONNX Runtime's
strength is cross-platform portability, not raw speed.

## Channel 5: TRIZ Cross-Domain Analysis

**Contradiction:** Improving local ML inference worsens
deployment simplicity (dependencies, startup, config).

**Fields explored:** Browser extensions, IDE plugins,
mobile on-device ML, game engines, security tools.

**Resolution:** Tiered architecture from security domain
(confidence 0.92):

- Tier 0: Config-as-model (YAML coefficients, pure
  Python dot product). Zero dependencies.
- Tier 1: Rule-based heuristics (existing hooks).
- Tier 2: Sidecar ONNX daemon (isolated Python 3.11+
  venv). Lazy init, background warm-up.
- Tier 3: Claude API (existing).

**Critical constraint:** System Python 3.9.6. Current
onnxruntime requires Python >= 3.11. Sidecar pattern
isolates onnxruntime in its own venv.

**Strongest analogy:** Security tools (YARA + ML hybrid).
For classifiers on 10-20 features, exported coefficients
in YAML give ML capability at zero cost.

## Key Sources

- Jajal et al. (ISSTA 2024): https://arxiv.org/abs/2303.17708
- DiTOX (2025): https://arxiv.org/abs/2505.01892
- SeQTO (2025): https://arxiv.org/abs/2507.12196
- PickleBall (CCS 2025): https://arxiv.org/abs/2508.15987
- microsoft/onnxruntime-genai: https://github.com/microsoft/onnxruntime-genai
- microsoft/onnxruntime-extensions: https://github.com/microsoft/onnxruntime-extensions
- ruvnet/onnx-agent: https://github.com/ruvnet/onnx-agent
- CVE-2026-28500: onnx.hub.load() silent trust bypass
