# Superpowers Integration Guide

This guide details the integration of skills from the superpowers marketplace into Night Market plugins. These integrations provide standardized implementations for tasks like debugging, test-driven development, and planning.

## Integration Patterns

1.  **Direct Call**: Replace redundant logic with calls to existing superpowers skills.
2.  **Quality Gates**: Add validation steps to workflows using superpowers methodologies.
3.  **Workflow Chaining**: Sequence superpower steps within plugin-specific processes.

## Superpowers Updates (v4.0.0 - v4.1.0)

### Skill Consolidations (v4.0.0)

Several standalone skills were grouped into larger modules:
- `root-cause-tracing`, `defense-in-depth`, and `condition-based-waiting` are now part of `systematic-debugging/`.
- `testing-skills-with-subagents` is now part of `writing-skills/`.
- `testing-anti-patterns` is now part of `test-driven-development/`.

### New Features (v4.0.x)

Subagent workflows now use separate stages for specification compliance and code quality reviews. Key skills define processes using executable DOT/GraphViz diagrams. v4.0.3 updated skill request handling to identify red flags in ambiguous inputs. Testing infrastructure now includes skill-triggering tests and end-to-end Claude Code integration tests.

### Breaking Changes (v4.1.0)

Version 4.1.0 switched to the native `skill` tool, which requires migration for OpenCode users. Hook execution for Claude Code 2.1.x was corrected to use LF line endings and updated `hooks.json` structures for Windows compatibility.

For full details, see the [Superpowers Release Notes](https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md).

## Current Integrations

### Abstract Plugin

The `/create-skill`, `/create-command`, and `/create-hook` commands use `superpowers:brainstorming` to generate initial drafts. Integration tests use `superpowers:systematic-debugging` for complex troubleshooting, leveraging root-cause tracing and defense-in-depth patterns.

### Spec-Kit Plugin

`task-planning` uses `superpowers:writing-plans` and `superpowers:executing-plans` for lifecycle management. The `speckit-orchestrator` integrates multiple debugging and verification skills to validate implementation against specifications.

### Pensive Plugin

The `/full-review` command includes `superpowers:systematic-debugging` and `superpowers:verification-before-completion` to analyze logic and verify fixes.

### Sanctum Plugin

`/fix-pr` uses `superpowers:receiving-code-review` to process feedback. Commit message generation uses `elements-of-style:writing-clearly-and-concisely` to enforce clarity standards.

### Parseltongue Plugin

`python-testing` integrates `superpowers:test-driven-development`. This includes references to testing anti-patterns to avoid issues like testing mock behavior or maintaining incomplete mocks.

### Minister Plugin

`issue-management` uses `superpowers:systematic-debugging` for triaging bug reports.

### Conservation Plugin

`/optimize-context` uses `superpowers:systematic-debugging`. It specifically employs the condition-based-waiting technique to replace static timeouts with event-driven polling.

## Usage Examples

### Creating a New Skill
```bash
# Abstract's create-skill command:
/create-skill "async error handling"
# Invokes superpowers:brainstorming
```

### Reviewing Code
```bash
# Pensive's full-review command:
/full-review
# Includes superpowers:verification-before-completion
```

### Fixing PR Comments
```bash
# Sanctum's fix-pr command:
/fix-pr 123
# Includes superpowers:receiving-code-review
```

## Developer Guide

Identify where a plugin requires brainstorming, debugging, or verification. Call the corresponding superpower skill directly in the workflow. Update the skill or command documentation to reflect these dependencies. Verify the integration by running the specific workflow and checking that data passes correctly between the plugin and the superpower skill.
