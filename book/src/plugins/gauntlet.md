# gauntlet

Codebase learning through knowledge extraction, challenges, and spaced repetition.

## Overview

Gauntlet prevents knowledge atrophy for experienced developers and accelerates
onboarding for new ones. It extracts knowledge from the codebase and tests
understanding through adaptive challenges.

## Installation

```bash
/plugin install gauntlet@claude-night-market
```

## Skills

- `extract` - Analyze codebase and build a knowledge base
- `challenge` - Adaptive difficulty challenge session
- `onboard` - Guided five-stage onboarding path
- `curate` - Add or edit knowledge annotations

## Commands

- `/gauntlet` - Run an ad-hoc challenge session
- `/gauntlet-extract` - Rebuild the knowledge base
- `/gauntlet-progress` - Show accuracy stats and streak
- `/gauntlet-onboard` - Start or resume onboarding
- `/gauntlet-curate` - Add or edit a knowledge annotation

## ML Scoring

Gauntlet uses a pluggable `Scorer` protocol to evaluate answers.
Two implementations ship by default:

- **YamlScorer** (default): heuristic scoring based on YAML
  rule files. Always available, no external dependencies.
- **OnnxSidecarScorer**: upgrades scoring quality by calling
  the oracle sidecar daemon for ONNX model inference.
  Activates automatically when oracle is running.

The scorer selection is automatic. When oracle's port file
exists and the health check passes, gauntlet uses the
sidecar scorer with configurable blend weights. When
the sidecar is unavailable, it falls back to YamlScorer
with no user intervention.

See [oracle](oracle.md) for daemon setup and
[ADR-0009](../../docs/adr/0009-sidecar-service-discovery.md)
for the discovery pattern.

## Agents

- `extractor` - Autonomous knowledge extraction agent
