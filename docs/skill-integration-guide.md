# Skill Integration Guide

Integrating skills allows specialized tools to pass data
and state between one another.
This guide details patterns for chaining skills into functional workflows.

## Workflow Chaining

Chaining skills in sequence creates a pipeline where the output of one stage
feeds the next. For example,
an API development workflow typically moves from `skill-authoring` to scaffold
the project structure, to `api-design` for endpoint definition,
and finally to `testing-patterns` for coverage analysis.
The process finishes with `doc-updates` and `commit-messages`.

Security reviews follow a similar sequence:
`security-scanning` identifies potential vulnerabilities,
`bug-review` and `architecture-review` analyze those findings for
exploitability, and `test-review` verifies remediation before `pr-prep` stages
the fixes.

## State and Knowledge Management

Knowledge-focused skills capture and structure project information.
In a learning or onboarding workflow,
`memory-palace-architect` defines a spatial structure for core concepts,
while `knowledge-intake` processes raw materials.
`digital-garden-cultivator` then stores these concepts for long-term reference,
and `session-palace-builder` generates recall exercises.

Research workflows use `knowledge-locator` to identify sources,
`proof-of-work` for maintaining citations,
and `structured-output` to format data.
The `imbue-review` skill then synthesizes these components into a report.

## Performance and Resource Optimization

Large-scale operations require active context management and concurrency.
`context-optimization` filters files to keep the working set within the context
window, while `subagent-dispatching` delegates modules to parallel workers.
`systematic-debugging` then isolates root causes before
`verification-before-completion` executes regression tests.

For Python-specific performance, `python-async` manages blocking I/O,
`python-performance` identifies hotspots,
and `condition-based-waiting` uses event triggers instead of static sleeps to
reduce idle time.

## Implementation Examples

### API Development Pipeline

The following example shows how to coordinate a user management microservice
setup using skill calls:

```python
# Design API and data models
api_design_skill = load_skill('api-design')
endpoint_design = api_design_skill.design_rest_api(
    resource='users',
    operations=['create', 'read', 'update', 'delete', 'list']
)

# Add unit and integration tests
testing_skill = load_skill('testing-patterns')
test_suite = testing_skill.generate_api_tests(endpoints=endpoint_design)

# Generate OpenAPI documentation
doc_skill = load_skill('doc-updates')
api_docs = doc_skill.generate_api_documentation(endpoints=endpoint_design)
```

Generating tests and documentation directly from the design output prevents
drift. This pipeline ensures that endpoints, validation logic,
and documentation remain synchronized throughout the cycle.

### Security Review Automation

Security audits use `security-scanning` for SAST and DAST analysis.
`bug-review` evaluates findings for exploitability,
and `architecture-review` validates the design against threats like injection.
`test-review` then identifies coverage gaps,
while `pr-prep` assembles the remediation plan.
This produces an auditable trail,
packaging fixes and tests into a single unit for review.

### Learning Acceleration

To learn a new framework, `memory-palace-architect` scaffolds core concepts,
such as Rust's ownership model. `knowledge-intake` filters documentation
and examples into a progressive path, which `digital-garden-cultivator` stores.
`session-palace-builder` builds temporary recall exercises for immediate
application.

## Integration Patterns

Skills combine through sequential chaining, parallel execution,
or conditional routing. Sequential chaining passes output from one skill as
input to the next. Parallel execution uses `asyncio.gather` for independent
tasks. Conditional routing selects a skill based on input characteristics
and uses a default if no specific rules match.

Composite skills wrap specialized tools into a single workflow.
This allows for complex coordination while keeping individual skills focused on
single tasks.

## Technical Standards

Integration relies on standardized interfaces
and error handling to prevent chain failures.
Loading skills dynamically helps conserve tokens,
and caching results for expensive steps improves performance in frequently used
workflows. Configuration should be passed at runtime to support different
environments. Logging both inputs
and outputs simplifies debugging when a link in the chain fails.

## Verification

Testing complete skill chains verifies that data flows correctly between steps
and that performance remains within limits.
propagation tests confirm the system handles failures across skill boundaries.
Documentation should reflect the final integrated state,
and tests must cover typical use cases to prevent regression.

---

## Skill Role Taxonomy

A 2026-04-25 audit found that 85 of 195 skills (~43%) had
**zero inbound `Skill()` references**. That sounds alarming
until you separate two distinct populations:

1. Skills users invoke directly via slash commands or
   agent prompts -- they SHOULD have low Skill() inbound
   counts because the user is the caller.
2. Skills that exist solely to be loaded by other skills
   -- they SHOULD have high Skill() inbound counts because
   that is their entire purpose.

Without this distinction, "orphan" is a meaningless flag.
This section defines three formal roles and uses them to
classify skills the audit flagged.

### The three roles

| Role | Inbound Skill() | User-facing | Examples |
|------|----------------|-------------|----------|
| `entrypoint` | low (0-3) | yes | `attune:mission-orchestrator`, `sanctum:do-issue` |
| `library` | high (4+) | rarely | `scribe:slop-detector`, `imbue:proof-of-work` |
| `hook-target` | varies | no | `imbue:vow-enforcement`, hook-implemented checks |

#### Entrypoint skills

Invoked directly by users (via `/<plugin>:<skill>` slash
commands or by agents acting on user prompts). Their
value is end-to-end orchestration; they typically call
several library skills internally.

Signature: corresponds to a `commands/<name>.md` file,
registered in `plugin.json` under `commands` (not just
`skills`), description follows the "Verb + domain. Use
when..." trigger pattern, often a long SKILL.md with
multiple modules. Examples:
`attune:mission-orchestrator` (12 modules, user-invoked
via `/attune:mission`), `sanctum:do-issue`,
`spec-kit:speckit-orchestrator`, `egregore:summon`.

#### Library skills

Loaded by other skills via `Skill(<plugin>:<name>)`
during execution. Their value is reusable building
blocks; they do not ship a slash command of their own.

Signature: no corresponding `commands/<name>.md`,
registered in `plugin.json` only under `skills`,
description focuses on what the skill DOES rather than
on user triggers, high inbound Skill() reference count.
Examples: `scribe:slop-detector` (17+ inbound;
sanctum, scribe, abstract, memory-palace, hookify),
`imbue:proof-of-work` (17+ inbound; quality-gate
sequences), `sanctum:git-workspace-review` (13+ inbound;
preflight for commit / PR / review),
`leyline:git-platform`, the
`archetypes:architecture-paradigm-*` family.

#### Hook-target skills

Invoked by hooks (PreToolUse / PostToolUse /
SessionStart / Stop) rather than by other skills or
users. Their value is enforcement; the hook system
reads the SKILL.md to shape its own behaviour.

Signature: plugin has hooks registered in
`hooks/hooks.json` that reference the skill by name or
read its body, description often mentions enforcement,
validation, or classification, low or zero Skill()
inbound count in skill prose but active in hook
execution paths. Examples: `imbue:vow-enforcement`
(read by `imbue/hooks/vow_*.py`),
`imbue:karpathy-principles` (referenced by
`imbue/hooks/proof_enforcement.py`),
`conserve:clear-context` (triggered by SessionStart
context-overflow detection).

### Re-classifying audit "orphans"

A spot-check of 10 of the previously-flagged orphans
exposed the audit's measurement bug:

| Skill | Audit verdict | Real role |
|-------|---------------|-----------|
| `archetypes:architecture-paradigm-hexagonal` | orphan | library (loaded by paradigms hub) |
| `archetypes:architecture-paradigm-microservices` | orphan | library (paradigms hub) |
| `pensive:api-review` | orphan | library (loaded via unified-review module) |
| `pensive:bug-review` | orphan | library (unified-review) |
| `pensive:blast-radius` | orphan | entrypoint (`/pensive:blast-radius`) |
| `tome:code-search` | orphan | library (loaded by `tome:research`) |
| `tome:discourse` | orphan | library (loaded by `tome:research`) |
| `leyline:supply-chain-advisory` | orphan | hook-target (read by dependency hooks) |
| `conserve:agent-expenditure` | orphan | library (loaded by parallel-dispatch) |
| `cartograph:call-chain` | orphan | library (loaded by visualize) |

Verdict: 8 of 10 were correctly populated libraries that
the `Skill()` regex could not see because their callers
load them via `dependencies:` arrays in frontmatter, not
inline `Skill(...)` invocations. The remaining two were
a genuine entrypoint (`pensive:blast-radius`) and a real
hook-target (`leyline:supply-chain-advisory`).

This is a measurement bug in the audit, not a coverage
problem in the marketplace. The taxonomy is now the
basis for orphan detection: only skills with **no entry
path of any kind** (Skill() callers, slash command, hook
handle, or `dependencies:` declaration) qualify as
isolates.

### Frontmatter convention

The `role:` field is part of the SKILL.md frontmatter
schema and is honored by `abstract:skill-graph-audit`.
Recommended for every new skill:

```yaml
---
name: <kebab-case>
description: '...'
role: entrypoint  # or library, or hook-target
...
---
```

Field semantics in the audit (`plugins/abstract/scripts/skill_graph.py`):

- `role: entrypoint` skills are user-invoked; zero inbound
  is the normal case and never flags as an isolate.
- `role: library` skills exist to be loaded by other
  skills. Zero inbound is reported in a separate
  `uncalled_libraries` bin -- a softer "potentially
  dead" signal that does not conflate with genuine
  orphans.
- `role: hook-target` skills are invoked by hooks; the
  audit cannot trace that path, so zero inbound is
  expected and never flags as an isolate.
- Skills without `role:` fall back to legacy zero-degree
  isolate detection. Backfill is opportunistic.

The audit also recognises `dependencies:` arrays as a
valid entry path. Bare names resolve to same-plugin
sibling skills (the canonical hub-loads-paradigm
pattern); fully-qualified `plugin:name` entries cross
plugin boundaries. `modules:` arrays are NOT treated
as skill references for bare names -- those refer to
local module files within the skill's own directory.

### Audit impact

After applying the schema, a full audit of the 185
skills in this marketplace produced:

- **Isolates: 104 -> 45** (-59 false positives eliminated).
- **Edges visible: 134 -> 298** (+164 previously-hidden
  declarative dependencies now traced).
- **Roles assigned**: 15 entrypoint, 24 library, 3
  hook-target, 143 unset (legacy).
- **Genuine dangling references surfaced**: 32 deps to
  skills that do not exist (e.g. multiple plugins
  reference a `<plugin>:shared` skill that is not in
  the tree). These were always present but invisible
  to the regex-only extractor.

---

## See Also

- [Superpowers Integration](../book/src/reference/superpowers-integration.md)
- [Plugin Development Guide](./plugin-development-guide.md)
- [Quality Gates](./quality-gates.md) - Gate orchestration map and
  composition order
