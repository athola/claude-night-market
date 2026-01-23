# Superpowers Integration Guide

Documentation for integrating superpowers marketplace skills with night-market plugins.

## Overview

The superpowers marketplace provides specialized skills for methodologies like RED-GREEN-REFACTOR, debugging, and evidence-based operations. This guide explains how to integrate these skills into your plugins.

## Integration Principles

We integrate these skills to reuse proven methodologies instead of reinventing them. This allows plugins to focus on their specific domain while relying on standard approaches for tasks like debugging or brainstorming.

## Integration Patterns

1.  **Direct Call**: Replace duplicate logic with superpowers skill calls.
2.  **Enhancement**: Add quality gates to existing workflows.
3.  **Workflow Integration**: Insert methodology steps into existing processes.

## Recent Superpowers Updates (v4.0.0 - v4.1.0)

### Skill Consolidations (v4.0.0)

Several standalone skills were bundled into comprehensive skills:
- `root-cause-tracing`, `defense-in-depth`, `condition-based-waiting` → bundled in `systematic-debugging/`
- `testing-skills-with-subagents` → bundled in `writing-skills/`
- `testing-anti-patterns` → bundled in `test-driven-development/`

### New Features (v4.0.x)

1. **Two-Stage Code Review** - Subagent workflows now use separate spec compliance and code quality reviews
2. **DOT Flowcharts** - Key skills now use executable DOT/GraphViz diagrams as authoritative process definitions
3. **Strengthened Skill Invocation** - v4.0.3 improved explicit skill request handling with new red flags
4. **Test Infrastructure** - New skill-triggering tests, Claude Code integration tests, and end-to-end workflow tests

### Breaking Changes (v4.1.0)

1. **OpenCode Native Skills** - Switched to native `skill` tool (migration required for OpenCode users)
2. **Windows Compatibility** - Fixed hook execution for Claude Code 2.1.x (hooks.json changes, LF line endings)

For full details, see the [Superpowers Release Notes](https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md).

## Current Integrations

### Abstract Plugin

*   `/create-skill`: Uses `superpowers:brainstorming`.
*   `/create-command`: Uses `superpowers:brainstorming`.
*   `/create-hook`: Uses `superpowers:brainstorming`.
*   Integration tests: Use `superpowers:systematic-debugging` for complex troubleshooting (includes root-cause-tracing, defense-in-depth, condition-based-waiting).

### Spec-Kit Plugin

*   `task-planning`: Uses `superpowers:writing-plans` and `superpowers:executing-plans`.
*   `speckit-orchestrator`: Integrates multiple superpowers skills for debugging and verification.

### Pensive Plugin

*   `/full-review`: Includes `superpowers:systematic-debugging` and `superpowers:verification-before-completion`.

### Sanctum Plugin

*   `/fix-pr`: Uses `superpowers:receiving-code-review`.
*   Commit messages: Uses `elements-of-style:writing-clearly-and-concisely`.
*   Future enhancements: Will use `superpowers:systematic-debugging` for complex issue resolution and security-focused reviews.

### Parseltongue Plugin

*   `python-testing`: Integrates `superpowers:test-driven-development` (includes testing-anti-patterns reference for common pitfalls like testing mock behavior, test-only methods, and incomplete mocks).

### Minister Plugin

*   `issue-management`: Uses `superpowers:systematic-debugging` for bug reports.

### Conservation Plugin

*   `/optimize-context`: Uses `superpowers:systematic-debugging` (includes condition-based-waiting technique for replacing arbitrary timeouts with condition polling).

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

### Writing Tests
```bash
# Parseltongue's python-testing skill:
# Uses superpowers:test-driven-development
```

## Developer Guide

1.  **Identify Patterns**: Find where your plugin uses brainstorming, debugging, or verification.
2.  **Document**: Add integration details to skill/command documentation.
3.  **Implement**: Call superpowers skills in your workflows.
4.  **Test**: Verify the integration works as expected.

## Summary

These integrations ensure we solve problems consistently, whether debugging or planning. By leveraging the superpowers marketplace, we maintain high standards across the entire ecosystem.
