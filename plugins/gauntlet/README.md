# gauntlet

Codebase learning through knowledge extraction, challenges, and
spaced repetition.

## Quick Start

```bash
# 1. Extract knowledge from your codebase
/gauntlet-extract

# 2. Run a challenge session
/gauntlet

# 3. Check your progress
/gauntlet-progress
```

## How It Works

1. **Extract**: the extractor walks your Python source tree, pulls
   out functions and classes via AST analysis, and stores them in
   `.gauntlet/knowledge.json`.

2. **Challenge**: the challenge engine picks an entry using adaptive
   weighting (weak categories and unseen entries get higher weight),
   generates a question, and evaluates your answer.

3. **Progress**: every answer is recorded. Difficulty adapts. A
   streak of correct answers raises the target difficulty; wrong
   answers bring it back down.

4. **Curate**: tribal knowledge that cannot be inferred from code
   goes into `.gauntlet/annotations/*.yaml` and feeds future
   challenges.

## Commands

| Command | Description |
|---------|-------------|
| `/gauntlet` | 5-question challenge session |
| `/gauntlet-extract` | Rebuild knowledge base |
| `/gauntlet-progress` | Show accuracy stats and streak |
| `/gauntlet-onboard` | Guided 5-stage onboarding path |
| `/gauntlet-curate` | Add a knowledge annotation |

## Challenge Types

| Type | Description |
|------|-------------|
| `multiple_choice` | Pick the best description (A-D) |
| `explain_why` | Explain how a concept works |
| `trace` | Trace data flow step by step |
| `spot_bug` | Identify what breaks if a rule is violated |
| `dependency_map` | List affected modules |
| `code_completion` | Describe or write the key logic |

## Configuration

The plugin stores all state under `.gauntlet/` in your project root:

```
.gauntlet/
  knowledge.json        # extracted entries
  annotations/          # curated YAML annotations
  progress/             # per-developer answer history
  state/                # transient state (pending challenges)
```

No configuration file is required. The pre-commit hook activates
automatically when `.gauntlet/knowledge.json` exists.

## ML Scoring

Answer evaluation uses a pluggable `Scorer` protocol:

- **YamlScorer** (default): heuristic scoring from YAML
  rule files. No dependencies beyond the plugin itself.
- **OnnxSidecarScorer**: calls the oracle daemon for ONNX
  model inference. Activates automatically when oracle
  is running (detected via port file).

Selection is automatic. The sidecar scorer takes over
when oracle's port file exists and its `/health` endpoint
responds. Otherwise gauntlet falls back to YamlScorer.
Blend weights between heuristic and model scores are
configurable.

## CLI Scripts

For scripted or CI use, four scripts are available under
`plugins/gauntlet/scripts/`:

```bash
# Extract knowledge
python3 scripts/extractor.py src/ --output .gauntlet/

# Generate a challenge (JSON output)
python3 scripts/challenge_engine.py .gauntlet/ --developer you@example.com

# Score an answer
python3 scripts/answer_evaluator.py challenge.json "my answer"

# Show progress stats
python3 scripts/progress_tracker.py .gauntlet/ --developer you@example.com
```
