# gauntlet

Codebase learning through knowledge extraction, code knowledge
graph, challenges, and spaced repetition.

## Problem

When developers rely on AI-assisted coding tools, they stop
writing code directly and their codebase knowledge atrophies.
Understanding of business logic, data flow, and architecture
fades because the developer is no longer actively reasoning
about the code.
New developers face the same gap from the opposite direction:
AI tools can short-circuit learning by providing answers
without requiring understanding.
The gauntlet reintegrates developers into the codebase through
active recall and spaced repetition.

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

2. **Graph**: Tree-sitter parses multi-language codebases to build
   a SQLite knowledge graph with functions, classes, imports, and
   call relationships. Supports incremental updates and FTS5 search.

3. **Challenge**: the challenge engine picks an entry using adaptive
   weighting (weak categories and unseen entries get higher weight),
   generates a question, and evaluates your answer.

4. **Progress**: every answer is recorded. Difficulty adapts. A
   streak of correct answers raises the target difficulty; wrong
   answers bring it back down.

5. **Curate**: tribal knowledge that cannot be inferred from code
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
| `/gauntlet-graph` | Build, search, and query the code knowledge graph |

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

## Architecture

The plugin uses a three-layer design:

1. **Knowledge extraction** (foundation): AST analysis and AI
   summarization walk the source tree and produce a queryable
   knowledge base stored in `.gauntlet/knowledge.json`.
   A curation layer lets developers add context that cannot
   be inferred from code alone.
2. **Code knowledge graph**: Tree-sitter parses multi-language
   codebases to build a SQLite graph with functions, classes,
   imports, and call relationships. Community detection groups
   related nodes, and blast radius analysis scores change risk
   using security keyword matching from `constants.py`.
3. **Problem bank**: curated algorithm problems stored as YAML
   in `data/problems/`. Categories cover arrays, graphs, trees,
   dynamic programming, and more. Each problem has difficulty
   and pattern metadata for targeted practice.
4. **Challenge engine** (active recall): generates six exercise
   types (multiple choice, code completion, trace, explain-why,
   spot-the-bug, dependency map) from the knowledge base.
   Adaptive weighting targets weak categories and unseen entries.
5. **Integration points** (habit formation): a pre-commit hook
   gates commits behind a challenge, slash commands run on-demand
   sessions, skills support guided onboarding, and an agent query
   API exposes the knowledge base to other plugins.

## ML Scoring

Open-ended challenge scoring originally used word-overlap
(`|intersection| / |reference|`), which fails when a correct
answer uses synonyms or restructures the explanation.
The `Scorer` protocol enables backend swapping so scoring
can improve without changing consumer code.

**YamlScorer** (default, zero dependencies) loads logistic
regression coefficients from a YAML file and performs a
pure-Python dot product with sigmoid activation.
It extracts 7 numeric features from each challenge-answer
pair: word overlap ratio, length ratio, keyword coverage,
structural depth, unique word ratio, negation density, and
numeric match.
The final score blends word-overlap (40%) with ML (60%)
at configurable weights, falling back to word-overlap alone
when the model file is missing or corrupt.

**OnnxSidecarScorer** calls the oracle daemon for ONNX
model inference.
It activates automatically when oracle's port file exists
and its `/health` endpoint responds.
Both scorers implement the same `Scorer` protocol, so
consumer code never changes.

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
