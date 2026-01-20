# Capabilities Reference Details

Full flag and option documentation for commands, skills, agents, and hooks, with working examples.

**Quick lookup**: [Capabilities Reference](capabilities-reference.md)

---

## Documentation Pages

| Page | Description |
|------|-------------|
| [Commands](capabilities-commands.md) | Slash-command reference with all flags and options |
| [Skills](capabilities-skills.md) | Methodology guides and invocation patterns |
| [Agents](capabilities-agents.md) | Subagent configuration and dispatch patterns |
| [Hooks](capabilities-hooks.md) | Lifecycle event handlers and implementation patterns |
| [Workflows](capabilities-workflows.md) | Complete workflow examples you can copy directly |

---

## Quick Navigation

### By Plugin

| Plugin | Commands | Skills | Agents |
|--------|----------|--------|--------|
| [abstract](capabilities-commands.md#abstract-plugin) | validate-plugin, create-skill, create-command | skill-authoring, hook-authoring | plugin-validator, meta-architect |
| [attune](capabilities-commands.md#attune-plugin) | init, brainstorm, plan, execute | - | project-architect |
| [conserve](capabilities-commands.md#conserve-plugin) | bloat-scan, unbloat, optimize-context | context-optimization, bloat-detector | bloat-auditor, context-optimizer |
| [imbue](capabilities-commands.md#imbue-plugin) | catchup, review, structured-review | scope-guard, proof-of-work | review-analyst |
| [memory-palace](capabilities-commands.md#memory-palace-plugin) | garden, navigate, palace | knowledge-intake, digital-garden | palace-architect, garden-curator |
| [parseltongue](capabilities-commands.md#parseltongue-plugin) | analyze-tests, run-profiler | python-async, python-packaging | python-pro, python-tester |
| [pensive](capabilities-commands.md#pensive-plugin) | full-review, code-review, architecture-review | bug-review, api-review | code-reviewer, architecture-reviewer |
| [sanctum](capabilities-commands.md#sanctum-plugin) | prepare-pr, commit-msg, do-issue | pr-prep, commit-messages | commit-agent, pr-agent |
| [scribe](capabilities-commands.md#scribe-plugin) | slop-scan, doc-polish, doc-verify | slop-detector, doc-generator | doc-editor, slop-hunter |
| [spec-kit](capabilities-commands.md#spec-kit-plugin) | speckit-startup, speckit-implement | speckit-orchestrator | spec-analyzer |

### By Task

| Task | Start Here |
|------|------------|
| New project setup | [/attune:init](capabilities-commands.md#attuneinit) |
| Code review | [/pensive:full-review](capabilities-commands.md#pensivefull-review) |
| PR preparation | [/sanctum:prepare-pr](capabilities-commands.md#sanctumprepare-pr-alias-pr) |
| Context optimization | [/conserve:bloat-scan](capabilities-commands.md#conservebloat-scan) |
| Feature development | [Workflow: Complete Feature](capabilities-workflows.md#complete-feature-development) |
| Bug fix | [Workflow: Quick Bug Fix](capabilities-workflows.md#quick-bug-fix) |
| Documentation cleanup | [/scribe:slop-scan](capabilities-commands.md#slop-scan) |
| Knowledge management | [/memory-palace:garden](capabilities-commands.md#memory-palacegarden) |

---

## See Also

- [Getting Started](../getting-started/README.md)
- [Tutorials](../tutorials/README.md)
