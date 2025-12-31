---
name: review-chamber
description: Capture and retrieve PR review knowledge in project memory palaces
version: 1.0.0
triggers:
  - pr review completed
  - knowledge capture requested
  - review patterns query
  - past decisions lookup
usage_patterns:
  - capture-review: After PR review completion, capture significant findings
  - search-decisions: Find past architectural decisions
  - pattern-lookup: Retrieve recurring issues and solutions
  - standards-reference: Access quality standards from past reviews
dependencies:
  - memory-palace:knowledge-intake
  - sanctum:pr-review
modules:
  - capture-workflow.md
  - evaluation-criteria.md
  - search-patterns.md
---

# PR Review Chamber Skill

Capture, organize, and retrieve knowledge from PR reviews within project memory palaces.

## Overview

The Review Chamber is a dedicated room within each project palace that stores valuable knowledge extracted from PR reviews. It transforms ephemeral PR discussions into persistent, searchable institutional memory.

## Room Structure

```
review-chamber/
├── decisions/      # Architectural choices from PR discussions
├── patterns/       # Recurring issues and their solutions
├── standards/      # Quality bar examples and coding conventions
└── lessons/        # Post-mortems and learnings
```

## Workflow Phases

### Phase 1: Knowledge Detection

After a PR review completes, evaluate findings for knowledge capture:

```markdown
## Knowledge Detection Checklist

For each finding from sanctum:pr-review, evaluate:

- [ ] **Novelty**: Is this a new pattern or first occurrence?
- [ ] **Applicability**: Will this affect future PRs in this area?
- [ ] **Durability**: Is this architectural (capture) or tactical (skip)?
- [ ] **Connectivity**: Does it link to existing palace rooms?
```

### Phase 2: Classification

Route findings to appropriate subrooms:

| Finding Type | Target Room | Criteria |
|-------------|-------------|----------|
| Architectural choice | `decisions/` | BLOCKING + architectural context |
| Recurring issue | `patterns/` | Seen before or likely to recur |
| Quality example | `standards/` | Exemplifies coding standards |
| Learning/insight | `lessons/` | Retrospective or post-mortem |

### Phase 3: Capture

Create structured entry with:

```yaml
---
source_pr: "#42 - Add authentication"
date: 2025-01-15
participants: [author, reviewer1, reviewer2]
palace_location: review-chamber/decisions
related_rooms: [workshop/auth-patterns, library/security-adr]
tags: [authentication, jwt, security]
---

## Decision Title

### Decision
Chose JWT tokens over server-side sessions.

### Context (from PR discussion)
- Reviewer asked: "Why not use sessions?"
- Author explained: stateless scaling requirements
- Discussion refined: added refresh token rotation

### Captured Knowledge
- **Pattern**: JWT + refresh tokens for stateless auth
- **Tradeoff**: Complexity vs. horizontal scaling
- **Application**: Use for all API authentication

### Connected Concepts
- [[auth-patterns]] - Updated with JWT best practices
- [[security-adr-003]] - Referenced this decision
```

### Phase 4: Integration

After capture, update related palace rooms:

1. Add bidirectional links to related entries
2. Update tags in project palace index
3. Notify if this contradicts existing entries

## Usage Examples

### Capture After PR Review

```bash
# Automatic: sanctum:pr-review triggers capture
/pr-review 42
# → Review posted to GitHub
# → Knowledge capture evaluates findings
# → Significant decisions stored in review-chamber

# Manual: Explicitly capture from PR
/review-room capture 42 --room decisions
```

### Search Past Decisions

```bash
# Find authentication decisions
/review-room search "authentication" --room decisions

# Find patterns in a specific area
/review-room search "error handling" --room patterns --tags api

# List recent entries
/review-room list --limit 10 --room standards
```

### Surface Relevant Knowledge

When starting work in a code area:

```markdown
## Relevant Review Knowledge

Starting work in `auth/` directory...

**Past Decisions:**
- [#42] JWT token decision → decisions/jwt-over-sessions
- [#67] Rate limiting pattern → patterns/api-throttling

**Quality Standards:**
- [#55] Error response format → standards/api-errors

**Known Patterns:**
- [#38] Token refresh edge case → patterns/token-refresh-race
```

## Integration Points

### With sanctum:pr-review

The review-chamber integrates after Phase 6 (Generate Report):

```
Phase 6: Generate Report
    ↓
[HOOK] Evaluate findings for knowledge capture
    ↓
    For each significant finding:
    ├── Classify into room type
    ├── Create ReviewEntry
    ├── Add to project palace
    └── Update connections
    ↓
Phase 7: Post to GitHub
```

### With knowledge-intake

Uses the same evaluation framework:

| Criterion | Weight | PR Review Application |
|-----------|--------|----------------------|
| Novelty | 25% | New pattern or first occurrence |
| Applicability | 30% | Affects future PRs in this area |
| Durability | 20% | Architectural vs tactical |
| Connectivity | 15% | Links to existing rooms |
| Authority | 10% | Senior reviewer or domain expert |

### With knowledge-locator

Extends search to include review-chamber:

```bash
python scripts/palace_manager.py search "authentication" \
  --palace project-name \
  --room review-chamber \
  --type semantic
```

## Evaluation Rubric

### Worth Capturing (Score ≥ 60)

- **Architectural decisions** with documented rationale
- **Recurring patterns** seen in 2+ PRs
- **Security/performance** critical findings
- **Domain knowledge** that explains business logic
- **Convention changes** that affect future code

### Skip (Score < 60)

- One-off tactical fixes
- Style preferences without rationale
- Obvious bugs without pattern
- External dependency issues
- Temporary workarounds

## CLI Reference

```bash
# Capture knowledge from PR
/review-room capture <pr_number> [--room <room_type>] [--tags <tags>]

# Search review chamber
/review-room search "<query>" [--room <room_type>] [--tags <tags>]

# List entries
/review-room list [--room <room_type>] [--limit N]

# View entry details
/review-room view <entry_id>

# Export for documentation
/review-room export [--format markdown|json] [--room <room_type>]

# Statistics
/review-room stats [--palace <palace_id>]
```

## Best Practices

1. **Capture decisions immediately** - Context is freshest right after review
2. **Link related entries** - Build the knowledge graph
3. **Use consistent tags** - Enable cross-project discovery
4. **Review periodically** - Prune outdated entries
5. **Surface proactively** - Show relevant knowledge when starting related work
