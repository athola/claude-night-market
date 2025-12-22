# Enforcement Language Templates

## Tiered Intensity Levels

Match language intensity to skill category. Discipline-enforcing skills need maximum intensity; reference skills need minimal.

## Level 1: Maximum (Discipline-Enforcing Skills)

Use for: TDD, security, compliance, verification workflows

**Characteristics:**
- Imperative commands ("YOU MUST", "NEVER")
- Explicit consequences
- No exceptions without user permission
- Anti-rationalization references

**Template:**
```yaml
description: |
  [Capability statement].

  YOU MUST use this skill when [conditions]. This is NON-NEGOTIABLE.

  NEVER skip this skill when [critical conditions].

  No exceptions without explicit user permission.
```

**Example:**
```yaml
description: |
  Enforce RED-GREEN-REFACTOR discipline for test-driven development.

  YOU MUST use this skill when writing new code. This is NON-NEGOTIABLE.

  NEVER write production code before a failing test exists.

  No exceptions without explicit user permission.
```

## Level 2: High (Workflow Skills)

Use for: Brainstorming, planning, code review, debugging

**Characteristics:**
- Strong recommendations ("Use BEFORE", "Check even if")
- Doubt-resolving guidance
- Process-focused

**Template:**
```yaml
description: |
  [Capability statement].

  Use this skill BEFORE starting [task type]. Check even if you're unsure.

  If you think this doesn't apply, reconsider - it probably does.
```

**Example:**
```yaml
description: |
  Structure creative exploration before implementation decisions.

  Use this skill BEFORE starting any feature implementation. Check even if you're unsure.

  If you think this doesn't apply, reconsider - it probably does.
```

## Level 3: Medium (Technique Skills)

Use for: Patterns, best practices, optimization techniques

**Characteristics:**
- Conditional recommendations ("Use when", "Consider for")
- Symptom-based triggers
- Situational guidance

**Template:**
```yaml
description: |
  [Capability statement].

  Use when encountering [specific symptoms]. Recommended for [scenarios].

  Consider this skill when [conditions].
```

**Example:**
```yaml
description: |
  Apply caching strategies to reduce latency and resource usage.

  Use when encountering slow API responses or repeated computations.

  Consider this skill when profiling reveals redundant work.
```

## Level 4: Low (Reference Skills)

Use for: API documentation, examples, reference materials

**Characteristics:**
- Availability statements ("Available for", "Consult when")
- No pressure or urgency
- Optional consultation

**Template:**
```yaml
description: |
  [Capability statement].

  Available for [use cases]. Consult when needed.
```

**Example:**
```yaml
description: |
  Reference documentation for Claude Code plugin.json schema.

  Available for plugin configuration questions. Consult when needed.
```

## Intensity Selection Guide

| Skill Type | Intensity | Key Indicators |
|------------|-----------|----------------|
| TDD/Testing | Maximum | Correctness depends on process |
| Security | Maximum | Mistakes have serious consequences |
| Compliance | Maximum | External requirements mandate process |
| Debugging | High | Systematic approach prevents thrashing |
| Planning | High | Upfront investment saves rework |
| Code Review | High | Quality gates before merge |
| Patterns | Medium | Best practices, not requirements |
| Optimization | Medium | Situational improvements |
| Reference | Low | Information retrieval only |

## Usage

Reference this module when calibrating skill language:

**From SKILL.md** (in `skills/<skill-name>/SKILL.md`):
```markdown
## Language Intensity

This skill uses [Level X: Name] enforcement language.
See [enforcement language guide](../../shared-modules/enforcement-language.md).
```

**From a module** (in `skills/<skill-name>/modules/*.md`):
```markdown
See [enforcement language guide](../../../shared-modules/enforcement-language.md).
```
