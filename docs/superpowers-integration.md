# Superpowers Integration Guide

Documentation for integrating superpowers marketplace skills with night-market plugins.

## Overview

The superpowers marketplace provides specialized skills for methodologies like RED-GREEN-REFACTOR, debugging, and evidence-based operations. This guide explains how to integrate these skills into plugins.

## Integration Principles

1.  **Enhancement**: Superpowers skills add capability to existing workflows.
2.  **Evidence-Based**: Prioritize verification and evidence.
3.  **Methodology**: Focus on structured approaches to tasks.

## Integration Patterns

1.  **Direct Call**: Replace duplicate logic with superpowers skill calls.
2.  **Enhancement**: Add quality gates to existing workflows.
3.  **Workflow Integration**: Insert methodology steps into existing processes.

## Current Integrations

### Abstract Plugin

*   `/create-skill`: Uses `superpowers:brainstorming`.
*   `/create-command`: Uses `superpowers:brainstorming`.
*   `/create-hook`: Uses `superpowers:brainstorming`.

### Spec-Kit Plugin

*   `task-planning`: Uses `superpowers:writing-plans` and `superpowers:executing-plans`.
*   `speckit-orchestrator`: Integrates multiple superpowers skills for debugging and verification.

### Pensive Plugin

*   `/full-review`: Includes `superpowers:systematic-debugging` and `superpowers:verification-before-completion`.

### Sanctum Plugin

*   `/fix-pr`: Uses `superpowers:receiving-code-review`.
*   Commit messages: Uses `elements-of-style:writing-clearly-and-concisely`.

### Parseltongue Plugin

*   `python-testing`: Integrates `superpowers:test-driven-development` and `superpowers:testing-anti-patterns`.

### Minister Plugin

*   `issue-management`: Uses `superpowers:systematic-debugging` for bug reports.

### Conservation Plugin

*   `/optimize-context`: Uses `superpowers:condition-based-waiting`.

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

## Conclusion

Integrating superpowers skills standardizes methodologies across the plugin ecosystem, ensuring consistent and rigorous approaches to development tasks.
