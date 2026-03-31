# Gauntlet Plugin Design

**Date**: 2026-03-30
**Issue**: #192
**Status**: Approved

## Problem

When developers use AI-assisted coding tools, they become removed
from writing code directly.
This causes codebase knowledge to atrophy: understanding of business
logic, data flow, architecture, and engineering patterns fades
because the developer is no longer actively constructing and
reasoning about the code.

New developers face the same gap from the opposite direction:
they need to build codebase fluency from scratch, and AI tools
can short-circuit the learning process by providing answers
without requiring understanding.

## Solution

A Claude Code plugin that reintegrates developers into the
codebase through active recall and spaced repetition.
The gauntlet extracts knowledge from the codebase, generates
challenges from that knowledge, and integrates into the
development workflow via pre-commit gates and on-demand sessions.

The knowledge base also serves AI agents, creating a closed
learning loop with the existing LEARNINGS.md improvement framework.

## Architecture

Three layers:

1. **Knowledge extraction** (foundation): AST analysis and AI
   summarization produce a queryable knowledge base.
   A curation layer lets developers add context that cannot be
   inferred from code alone.
2. **Challenge engine** (active recall): generates six challenge
   types from the knowledge base with adaptive difficulty.
3. **Integration points** (habit formation): pre-commit gate,
   slash commands, onboarding paths, and agent query API.

## Plugin Structure

```
plugins/gauntlet/
├── .claude-plugin/
│   └── plugin.json
├── scripts/
│   ├── extractor.py          # AST + AI knowledge extraction
│   ├── challenge_engine.py   # Generate challenges from knowledge base
│   ├── answer_evaluator.py   # Score answers (exact + AI-evaluated)
│   └── progress_tracker.py   # Developer answer history + adaptive weighting
├── hooks/
│   ├── hooks.json
│   └── precommit_gate.py     # Pre-commit challenge gate
├── skills/
│   ├── extract/SKILL.md      # Analyze codebase, build knowledge base
│   ├── challenge/SKILL.md    # Run a gauntlet session
│   ├── onboard/SKILL.md      # Guided onboarding path
│   └── curate/SKILL.md       # Add/edit knowledge annotations
├── agents/
│   └── extractor.md          # Autonomous knowledge extraction agent
├── commands/
│   ├── gauntlet.md           # /gauntlet - run a challenge session
│   ├── extract.md            # /gauntlet-extract - rebuild knowledge base
│   ├── progress.md           # /gauntlet-progress - show stats
│   ├── onboard.md            # /gauntlet-onboard - guided onboarding
│   └── curate.md             # /gauntlet-curate - annotate knowledge
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_extraction.py
│   ├── test_challenges.py
│   ├── test_scoring.py
│   ├── test_progress.py
│   └── test_precommit.py
├── src/gauntlet/
│   ├── __init__.py
│   ├── models.py             # Data models
│   ├── extraction.py         # Knowledge extraction logic
│   ├── challenges.py         # Challenge generation logic
│   ├── scoring.py            # Answer evaluation logic
│   └── query.py              # Agent-facing query API
├── pyproject.toml
├── Makefile
└── README.md
```

### Per-repo artifacts

The gauntlet stores its data in the target repository:

```
.gauntlet/
├── knowledge.json            # Extracted knowledge base
├── config.yaml               # Per-repo configuration
├── annotations/              # Developer-authored curation
│   └── *.yaml
├── progress/                 # Per-developer answer history
│   └── <developer-id>.json
└── state/
    └── pending_challenge.json  # In-flight challenge for pre-commit
```

## Knowledge Base

### Knowledge entry model

```python
@dataclass
class KnowledgeEntry:
    id: str                      # Stable hash of module + concept
    category: str                # See categories below
    module: str                  # File or module path
    concept: str                 # Short description
    detail: str                  # Full explanation
    related_files: list[str]     # Files involved
    difficulty: int              # 1-5 scale
    tags: list[str]              # Searchable tags
    extracted_at: str            # ISO timestamp
    source: str                  # "automated" | "curated" | "learnings"
    consumers: list[str]         # "human" | "agent" | "both"
```

### Categories (priority order)

1. `business_logic` (weight 7): domain rules, constraints, why
   decisions were made
2. `architecture` (weight 6): module boundaries, responsibilities,
   component relationships
3. `data_flow` (weight 5): how data moves through the system
4. `api_contract` (weight 4): public interfaces, function
   signatures, expected inputs/outputs
5. `pattern` (weight 3): recurring design patterns, conventions,
   idioms
6. `dependency` (weight 2): import chains, module coupling,
   circular risks
7. `error_handling` (weight 1): failure handling, boundary
   conditions, defensive patterns

### Extraction process

The extractor agent performs:

1. **AST analysis**: parse source files, extract function
   signatures, class hierarchies, import graphs, control flow
2. **AI summarization**: for each module, generate natural
   language descriptions of business logic, data flow, and
   architectural role
3. **Cross-reference**: link related entries across modules
   (e.g., data flow from input validation through processing
   to storage)
4. **Difficulty assignment**: rate each entry 1-5 based on
   conceptual complexity and number of related modules
5. **Deduplication**: merge entries that describe the same
   concept from different angles

### Curation layer

Developers add annotations as YAML files in
`.gauntlet/annotations/`:

```yaml
# .gauntlet/annotations/auth-token-expiry.yaml
module: src/auth/token_manager.py
concept: "Token refresh happens before validation, not after"
why: >
  Historical incident: users were getting logged out mid-session
  when tokens expired during long API calls.
  The refresh-first pattern prevents this.
related_files:
  - src/auth/middleware.py
  - src/api/session.py
difficulty: 3
tags: [auth, tokens, business-rule]
```

Curated entries merge with automated entries in the knowledge
base. On re-extraction, automated entries are regenerated but
curated entries are preserved.

## Challenge Engine

### Challenge model

```python
@dataclass
class Challenge:
    id: str
    type: str                    # See types below
    knowledge_entry_id: str      # Links to knowledge base
    difficulty: int              # 1-5
    prompt: str                  # Question text
    context: str                 # Code snippet shown alongside
    answer: str                  # Correct answer or rubric
    options: list[str] | None    # For multiple choice
    hints: list[str]             # Progressive hints (onboarding)
    scope_files: list[str]       # Related files
```

### Challenge types

| Type | Generation Source | Evaluation |
|------|------------------|------------|
| Multiple choice | Knowledge entry + AI distractors | Exact match |
| Code completion | Real function with key logic blanked (AST) | AI comparison against original |
| Trace exercise | Data flow entries spanning 2-3 modules | AI evaluation against expected chain |
| Explain-the-why | Business logic + curated annotations | AI rubric (must hit key concepts) |
| Spot-the-bug | AI-generated plausible mutation | Location + description match |
| Dependency map | Dependency graph entries | Set comparison of affected modules |

Challenge type is selected randomly, weighted toward types
the developer struggles with.

### Scoring

Exact-match types: binary pass/fail.

AI-evaluated types: 3-point scale:

- **Pass**: demonstrates understanding of the core concept
- **Partial**: right direction, missing key elements
  (counts as 0.5 for adaptive weighting)
- **Fail**: incorrect or superficial

On fail at the pre-commit gate, the developer sees the correct
answer with explanation before being presented a new question.

### Adaptive weighting

```python
@dataclass
class AnswerRecord:
    challenge_id: str
    knowledge_entry_id: str
    challenge_type: str
    category: str
    difficulty: int
    result: str               # "pass" | "partial" | "fail"
    answered_at: str           # ISO timestamp

@dataclass
class DeveloperProgress:
    developer_id: str          # Derived from git config user.email
    history: list[AnswerRecord]
    category_scores: dict[str, float]   # Rolling accuracy per category
    type_scores: dict[str, float]       # Rolling accuracy per type
    last_seen: dict[str, str]           # entry_id -> last tested
    streak: int                         # Consecutive correct
```

Weighting logic:

- Categories with lower accuracy get asked more often
- Entries not seen recently get priority (spaced repetition)
- Types the developer struggles with appear more frequently
- Difficulty scales with streak (3 correct bumps difficulty up)

## Pre-commit Hook

### Behavior

The hook fires on `PreToolUse` matching `Bash(git commit*)`.
Default mode is **gate** (commit blocked until correct answer).

The hook itself cannot capture conversational answers, so the
gate uses a **pass-token mechanism**:

Flow:

1. Hook fires on `git commit`, checks
   `.gauntlet/state/pass_token.json` for a valid token
   (matching staged file hash, not expired)
2. No valid token: hook returns `permissionDecision: "deny"`
   with `additionalContext` containing a generated challenge
   scoped to the staged files
3. Claude presents the challenge to the developer
4. Developer answers in natural language in the conversation
5. Claude evaluates the answer using the challenge engine
   (via the `gauntlet:challenge` skill)
6. On pass: skill writes a pass token to
   `.gauntlet/state/pass_token.json` (valid for 5 minutes,
   bound to the current staged file hash)
7. Claude re-runs the commit
8. Hook finds valid token, allows the commit, deletes the token
9. On fail: Claude shows explanation and presents a new
   challenge (no token written, next commit attempt is
   also blocked)

### Configuration

`.gauntlet/config.yaml`:

```yaml
precommit:
  mode: gate              # gate | nudge | session | off
  questions_per_commit: 1
  scope: commit           # commit | full
  skip_patterns:
    - "*.md"
    - "*.json"
    - "CHANGELOG.md"
  cooldown_minutes: 0

difficulty:
  default: 3
  adaptive: true
  max: 5

onboarding:
  guided_path: true
  hints_enabled: true
  lenient_scoring: true

extraction:
  auto_refresh: true
  priorities:
    business_logic: 7
    architecture: 6
    data_flow: 5
    api_contract: 4
    pattern: 3
    dependency: 2
    error_handling: 1
```

## Onboarding Guided Path

### Five-stage progression

| Stage | Focus | Categories | Difficulty |
|-------|-------|-----------|------------|
| 1. Big picture | System purpose, module map, high-level flow | architecture, data_flow | 1-2 |
| 2. Core domain | Business rules, domain concepts, rationale | business_logic | 2-3 |
| 3. Interfaces | API contracts, how modules communicate | api_contract, data_flow | 3 |
| 4. Patterns | Engineering idioms, conventions, dependencies | pattern, dependency | 3-4 |
| 5. Hardening | Error handling, failure modes, edge cases | error_handling, business_logic | 4-5 |

### Progression tracking

```python
@dataclass
class OnboardingProgress:
    developer_id: str
    current_stage: int
    stage_scores: dict[int, float]
    entries_mastered: set[str]
    entries_remaining: dict[int, list[str]]
    started_at: str
    last_session_at: str
```

**Stage advancement**: 80% accuracy across at least 10 challenges
in the current stage. Developers can skip ahead with
`/gauntlet-onboard --stage N`.

### Session flow

1. Load current stage and remaining entries
2. Present 5 challenges from the current stage
3. Progressive hints on first attempt
4. On fail with lenient scoring, explain and mark for re-test
5. Report: "Stage 2: Core Domain, 7/15 concepts mastered, 73%"

### Graduation

After completing all 5 stages, the developer enters the regular
gauntlet. Answer history carries over for adaptive weighting.
Pre-commit gate activates (or earlier if configured).

## Agent Integration

### Query API

```python
def query_knowledge(
    files: list[str] | None = None,
    categories: list[str] | None = None,
    tags: list[str] | None = None,
    min_difficulty: int = 1,
    max_difficulty: int = 5,
) -> list[KnowledgeEntry]:
    """Query the knowledge base."""

def get_context_for_files(
    files: list[str],
) -> str:
    """Markdown summary of knowledge entries for these files.
    For injection into agent context before code modification."""

def validate_understanding(
    files: list[str],
    claim: str,
) -> dict:
    """Score a claim about files against the knowledge base.
    Returns {score: float, gaps: list[str]}."""
```

### Plugin integrations

| Plugin | Integration |
|--------|-------------|
| abstract (skill-improver) | `get_context_for_files()` before modifying skills |
| abstract (skill-auditor) | `validate_understanding()` to verify comprehension |
| imbue (LEARNINGS.md) | Bidirectional: learnings feed extraction, wrong answers feed learnings |
| pensive (code review) | Query knowledge base to check PR against business rules |
| sanctum (do-issue) | Query context on affected modules before implementing |

### LEARNINGS.md bidirectional flow

```
LEARNINGS.md (failure patterns)
    → gauntlet:extract reads learnings
    → generates entries tagged source: "learnings"
    → creates challenges: "This module previously failed
      because X. What guard prevents it now?"
    → wrong answers → new LEARNINGS.md improvement candidates
    → correct answers → confirm fix is understood
```

## Constraints

- Python 3.9 compatible (system Python is 3.9.6)
- Use `from __future__ import annotations` throughout
- Pre-commit hook must complete within 2 second timeout
  (challenge generation is fast; AI evaluation happens
  on the next tool call)
- Knowledge base JSON must remain under 5 MB per repo
  (prune low-value entries on extraction)
- All challenge generation and evaluation uses the
  currently active Claude model in-session
