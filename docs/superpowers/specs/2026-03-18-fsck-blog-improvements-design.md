# fsck Blog Improvements - Design Spec v0.1.0

**Author**: Claude
**Date**: 2026-03-18
**Status**: Draft
**Branch**: minor-improvements-1.6.7

## Overview

Implement 8 improvements to the night-market plugin ecosystem
derived from 5 fsck blog posts (January-March 2026).
Organized as Approach C: skill updates first (low risk),
new skills second (higher risk, need tests).

**Source Posts**:

- Superpowers 5 (2026-03-09): spec review loop, unit
  decomposition, file structure in plans, cost optimization
- Dorodango (2026-02-10): iterative polishing workflow
- Prompt Injection (2026-02-05): invisible text injection
- Managing Agents (2026-02-03): token waste, Brooks's Law
- Latent Space Engineering (2026-01-30): emotional framing,
  style gene transfer, competitive review

## Phase 1: Skill Updates

### 1A. Spec Review Loop

**Plugin**: attune
**Asset**: `skills/project-brainstorming/modules/spec-review-loop.md`
**Also modifies**: `skills/project-brainstorming/SKILL.md`

Add a post-brainstorming quality gate. After producing a
project brief or specification, dispatch a haiku-model
review subagent that checks for:

- TBD/TODO/placeholder sections
- Missing acceptance criteria
- Vague requirements ("should handle errors appropriately")
- Inconsistent terminology
- Missing edge cases referenced elsewhere

**Mechanism**: Dispatch subagent with spec content (not
session history). If issues found, fix and re-dispatch.
Max 3 iterations, then surface to human.

**Acceptance Criteria**:

- [ ] Module contains the review prompt template
- [ ] SKILL.md references module after workflow continuation
- [ ] Dispatch uses `model: "haiku"` for cost efficiency
- [ ] Loop terminates after 3 iterations maximum
- [ ] Issues surfaced as a numbered list with severity

### 1B. Unit Decomposition Teaching

**Plugin**: attune
**Modifies**: `skills/project-brainstorming/SKILL.md`

Add "Design for Isolation" guidance to the approach
generation phase. When proposing approaches, teach two
tests:

1. "Can someone understand what this unit does without
   reading its internals?"
2. "Can you change internals without breaking consumers?"

Flag large files as "design smell, not just style issue."

**Acceptance Criteria**:

- [ ] Two isolation tests appear in approach generation phase
- [ ] Large file signal documented as design smell
- [ ] Guidance is concise (under 30 lines added)

### 1C. File Structure in Plans

**Plugin**: attune
**Modifies**: `skills/project-planning/SKILL.md`

Add a mandatory **File Structure** section that must appear
before task decomposition. The plan declares which files
will be created or modified, with a one-line purpose each.

**Template**:

```markdown
## File Structure

| File | Action | Purpose |
|------|--------|---------|
| src/foo.py | Create | Handle foo logic |
| src/bar.py | Modify | Add baz interface |
```

**Acceptance Criteria**:

- [ ] File Structure section template added to planning skill
- [ ] Section is marked as required before task breakdown
- [ ] Template includes Action column (Create/Modify/Delete)

### 1D. Subagent Model Cost Optimization

**Plugin**: conjure
**Modifies**: `skills/delegation-core/modules/cost-estimation.md`

Add "cheapest-capable model" selection heuristic:

| Task Type | Has Detailed Plan? | Recommended Model |
|-----------|-------------------|-------------------|
| Implementation | Yes | haiku |
| Implementation | No | sonnet |
| Planning/reasoning | Any | sonnet/opus |
| Security/safety review | Any | never downgrade |
| Code review | Any | sonnet minimum |

**Acceptance Criteria**:

- [ ] Selection matrix added to cost-estimation module
- [ ] Security/safety tasks explicitly excluded from downgrade
- [ ] Heuristic framed as recommendation, not mandate

## Phase 2: New Skills

### 2A. Invisible Text Injection Detection

**Plugin**: leyline
**Modifies**: `hooks/sanitize_external_content.py`,
  `skills/content-sanitization/SKILL.md`

#### Hook Changes

Add high-severity (fail-closed) detection patterns:

**CSS/HTML hiding**:
- `display:\s*none`
- `visibility:\s*hidden`
- `color:\s*white` (or `#fff`, `#ffffff`, `rgb(255`)
- `font-size:\s*0`
- `opacity:\s*0`
- `height:\s*0.*overflow:\s*hidden`

**Unicode tricks**:
- Zero-width characters: U+200B, U+200C, U+200D, U+FEFF
- Strip these from content entirely

**Markdown hiding**:
- HTML comments containing instruction-like patterns:
  `<!--.*(?:ignore|override|forget|you are).*-->`

#### Skill Changes

Add "Formatting-Based Injection" section to the
sanitization checklist documenting all patterns above.

**Acceptance Criteria**:

- [ ] Hook detects and strips CSS/HTML hiding patterns
- [ ] Hook strips zero-width Unicode characters
- [ ] Hook detects instruction-bearing HTML comments
- [ ] All new patterns classified as high severity
- [ ] Skill checklist updated with new section
- [ ] Existing tests still pass
- [ ] New test cases cover each pattern category
- [ ] Python 3.9 compatible (no walrus operators, no
  match/case, no union type syntax)

### 2B. Latent Space Engineering

**Plugin**: imbue
**New asset**: `skills/latent-space-engineering/SKILL.md`
**Modules**:
- `modules/emotional-framing.md`
- `modules/style-gene-transfer.md`
- `modules/competitive-review.md`

#### Hub Skill

Reference skill consulted by other skills when writing
agent dispatch prompts or framing instructions. Progressive
loading: hub loads first, modules on demand.

#### Module: Emotional Framing

Guidelines for instruction tone in skills and agent prompts.

**Anti-patterns** (replace these):
- "You MUST do X or the system will fail"
- "CRITICAL: failure to comply will..."
- "WARNING: do NOT deviate from..."

**Preferred patterns** (use these):
- "You've got this. Take your time with X."
- "Focus on getting X right. The details matter here."
- "This is important work. Here's what good looks like..."

**Checklist for skill authors**:
1. Read your prompt aloud. Does it sound threatening?
2. Replace threat language with confidence language.
3. Keep urgency markers (IMPORTANT, MUST) for genuine
   safety constraints only.

#### Module: Style Gene Transfer

Pattern for injecting exemplar code or prose before
requesting output. Template:

```
Review this prior work for style and conventions:
---
[exemplar snippet, 50-200 lines]
---
Now apply the same style to your output for: [task]
```

**When to use**: Skill generates code or documentation
that must match an existing codebase style. Load a
representative sample first.

**When NOT to use**: Task is greenfield with no style
precedent. Exemplar is too large (>200 lines wastes
tokens for diminishing returns).

#### Module: Competitive Review

When dispatching 3+ review subagents in parallel, frame
with competitive incentive:

```
You are one of N independent reviewers analyzing this code.
Each reviewer's findings will be compared. The most thorough
and well-evidenced findings will be prioritized for action.
Focus on depth over breadth.
```

**Where to apply**: pensive review agents, pr-review-toolkit
agents, attune war-room expert panels.

**Acceptance Criteria**:

- [ ] Hub skill with progressive loading frontmatter
- [ ] Three modules with clear boundaries
- [ ] Emotional framing has anti-pattern/preferred-pattern
  pairs
- [ ] Style gene transfer has template and size guidance
- [ ] Competitive review has dispatch framing template
- [ ] Skill registered in imbue plugin.json

### 2C. Agent Token Waste Monitoring

**Plugin**: conserve
**New asset**: `skills/agent-expenditure/SKILL.md`
**Module**: `modules/waste-signals.md`

Reference skill defining token waste signals for agent
dispatch workflows.

#### Waste Signals

1. **Ghost agent**: Produces no actionable output
   (empty findings, "everything looks good")
2. **Redundant reader**: Re-reads files already loaded
   by another agent in the same dispatch
3. **Duplicate worker**: Overlaps >50% with another
   agent's findings
4. **Token hog**: Exceeds 3x the median token count
   for its task type without proportional output
5. **Coordination overhead**: When N > 5 agents and
   shared-file conflicts exceed 20% of agent time

#### Brooks's Law Threshold

Dispatching more agents does not always help. Diminishing
returns threshold:

| Agent Count | Expected Coordination Overhead |
|-------------|-------------------------------|
| 1-3 | Negligible |
| 4-5 | 10-15% (acceptable) |
| 6-8 | 20-30% (monitor closely) |
| 9+ | 30%+ (likely counterproductive) |

#### Post-Dispatch Review Checklist

After parallel agent runs, evaluate:

1. Did each agent produce unique findings?
2. Was total token expenditure proportional to value?
3. Did any agent duplicate another's work?
4. Would fewer agents have produced the same result?

**Acceptance Criteria**:

- [ ] Skill defines 5 waste signal categories
- [ ] Brooks's Law threshold table included
- [ ] Post-dispatch review checklist provided
- [ ] Skill registered in conserve plugin.json
- [ ] Cross-references plan-before-large-dispatch rule

### 2D. Dorodango Polishing Workflow

**Plugin**: attune
**New asset**: `skills/dorodango/SKILL.md`
**Module**: `modules/pass-definitions.md`

Iterative refinement skill that runs successive quality
passes over implemented code, each focused on one
dimension.

#### Pass Sequence

1. **Correctness**: Run tests, fix failures
2. **Clarity**: Dispatch code-refinement (pensive),
   fix readability
3. **Consistency**: Check naming, patterns, codebase
   style alignment
4. **Polish**: Documentation, error messages, edge cases

#### Properties

- Each pass dispatches a self-contained subagent
  (prevents context accumulation)
- State tracked in `.attune/dorodango-state.json`:
  ```json
  {
    "target": "plugins/foo",
    "pass_count": 3,
    "passes": [
      {"type": "correctness", "issues_found": 2,
       "issues_fixed": 2},
      {"type": "clarity", "issues_found": 5,
       "issues_fixed": 5},
      {"type": "consistency", "issues_found": 0}
    ],
    "converged": true
  }
  ```
- A pass that finds zero issues means convergence for
  that dimension
- When all 4 dimensions converge, polishing is complete
- Maximum 10 total passes before surfacing to human
- State file enables resume across sessions (persistence
  for long polishing runs)

**Acceptance Criteria**:

- [ ] Skill defines 4 pass types with clear scope
- [ ] State persistence via dorodango-state.json
- [ ] Convergence detection (zero-issue pass terminates)
- [ ] Maximum 10 passes safety valve
- [ ] Each pass uses subagent isolation
- [ ] Skill registered in attune plugin.json

## File Inventory

### Phase 1 (Modify)

| File | Action |
|------|--------|
| `plugins/attune/skills/project-brainstorming/SKILL.md` | Modify |
| `plugins/attune/skills/project-brainstorming/modules/spec-review-loop.md` | Create |
| `plugins/attune/skills/project-planning/SKILL.md` | Modify |
| `plugins/conjure/skills/delegation-core/modules/cost-estimation.md` | Modify |

### Phase 2 (Create)

| File | Action |
|------|--------|
| `plugins/leyline/hooks/sanitize_external_content.py` | Modify |
| `plugins/leyline/skills/content-sanitization/SKILL.md` | Modify |
| `plugins/leyline/tests/hooks/test_sanitize_external_content.py` | Modify |
| `plugins/imbue/skills/latent-space-engineering/SKILL.md` | Create |
| `plugins/imbue/skills/latent-space-engineering/modules/emotional-framing.md` | Create |
| `plugins/imbue/skills/latent-space-engineering/modules/style-gene-transfer.md` | Create |
| `plugins/imbue/skills/latent-space-engineering/modules/competitive-review.md` | Create |
| `plugins/imbue/.claude-plugin/plugin.json` | Modify |
| `plugins/conserve/skills/agent-expenditure/SKILL.md` | Create |
| `plugins/conserve/skills/agent-expenditure/modules/waste-signals.md` | Create |
| `plugins/conserve/.claude-plugin/plugin.json` | Modify |
| `plugins/attune/skills/dorodango/SKILL.md` | Create |
| `plugins/attune/skills/dorodango/modules/pass-definitions.md` | Create |
| `plugins/attune/.claude-plugin/plugin.json` | Modify |

**Total**: 18 files (6 modify, 12 create)

## Out of Scope

- Visual brainstorming (HTML server) -- platform-dependent,
  high complexity, low immediate value for this ecosystem
- AskUserQuestion ASCII-art diagrams -- Claude Code tool
  limitation, not plugin-controllable
- Reflective processing / feelings journal MCP -- requires
  MCP server infrastructure beyond plugin scope
- Agent swarm coordination -- egregore already handles this
