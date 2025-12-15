---
name: hooks-eval
description: Comprehensive hook evaluation framework for Claude Code and Agent SDK hooks. Covers security scanning, performance analysis, compliance checking, and SDK hook types. Use when auditing hooks, understanding hook architecture, or implementing hooks programmatically.
version: 1.0.0
category: hook-management
tags: [hooks, evaluation, security, performance, claude-sdk, agent-sdk]
dependencies: [hook-scope-guide]
provides:
  infrastructure: ["hook-evaluation", "security-scanning", "performance-analysis"]
  patterns: ["hook-auditing", "sdk-integration", "compliance-checking"]
  sdk_features:
    - "python-sdk-hooks"
    - "hook-callbacks"
    - "hook-matchers"
estimated_tokens: 1200
---

# Hooks Evaluation Framework

## Overview

This skill provides a comprehensive framework for evaluating, auditing, and implementing Claude Code hooks across all scopes (plugin, project, global) and both JSON-based and programmatic (Python SDK) hooks.

### Key Capabilities

- **Security Analysis**: Vulnerability scanning, dangerous pattern detection, injection prevention
- **Performance Analysis**: Execution time benchmarking, resource usage, optimization
- **Compliance Checking**: Structure validation, documentation requirements, best practices
- **SDK Integration**: Python SDK hook types, callbacks, matchers, and patterns

### Core Components

| Component | Purpose |
|-----------|---------|
| **Hook Types Reference** | Complete SDK hook event types and signatures |
| **Evaluation Criteria** | Scoring system and quality gates |
| **Security Patterns** | Common vulnerabilities and mitigations |
| **Performance Benchmarks** | Thresholds and optimization guidance |

## When to Use

**Use this skill when:**
- Auditing existing hooks for security vulnerabilities
- Benchmarking hook performance
- Implementing hooks using the Python SDK
- Understanding hook callback signatures and return values
- Validating hooks against compliance standards

**Don't use when:**
- Deciding where to place hooks (use `hook-scope-guide` instead)
- Writing hook rules from scratch (use `hookify:writing-rules`)
- Validating plugin structure (use `validate-plugin`)

## Quick Reference

### Hook Event Types

```python
HookEvent = Literal[
    "PreToolUse",       # Before tool execution
    "PostToolUse",      # After tool execution
    "UserPromptSubmit", # When user submits prompt
    "Stop",             # When stopping execution
    "SubagentStop",     # When a subagent stops
    "PreCompact"        # Before message compaction
]
```

**Note**: Python SDK does not support `SessionStart`, `SessionEnd`, or `Notification` hooks due to setup limitations.

### Hook Callback Signature

```python
async def my_hook(
    input_data: dict[str, Any],    # Hook-specific input
    tool_use_id: str | None,       # Tool ID (for tool hooks)
    context: HookContext           # Additional context
) -> dict[str, Any]:               # Return decision/messages
    ...
```

### Return Values

```python
return {
    "decision": "block",           # Optional: block the action
    "systemMessage": "...",        # Optional: add to transcript
    "hookSpecificOutput": {...}    # Optional: hook-specific data
}
```

### Quality Scoring (100 points)

| Category | Points | Focus |
|----------|--------|-------|
| Security | 30 | Vulnerabilities, injection, validation |
| Performance | 25 | Execution time, memory, I/O |
| Compliance | 20 | Structure, documentation, error handling |
| Reliability | 15 | Timeouts, idempotency, degradation |
| Maintainability | 10 | Code structure, modularity |

## Detailed Resources

- **SDK Hook Types**: See `modules/sdk-hook-types.md` for complete Python SDK type definitions, patterns, and examples
- **Evaluation Criteria**: See `modules/evaluation-criteria.md` for detailed scoring rubric and quality gates
- **Security Patterns**: See `modules/security-patterns.md` for vulnerability detection and mitigation
- **Performance Guide**: See `modules/performance-guide.md` for benchmarking and optimization

## Basic Evaluation Workflow

```bash
# 1. Run comprehensive evaluation
/hooks-eval --comprehensive

# 2. Focus on security issues
/hooks-eval --security-only --format sarif

# 3. Benchmark performance
/hooks-eval --performance-baseline

# 4. Check compliance
/hooks-eval --compliance-report
```

## Integration with Other Tools

```bash
# Complete plugin evaluation pipeline
/hooks-eval --comprehensive          # Evaluate all hooks
/analyze-hook hooks/specific.py      # Deep-dive on one hook
/validate-plugin .                   # Validate overall structure
```

## Related Skills

- `hook-scope-guide` - Decide where to place hooks (plugin/project/global)
- `hookify:writing-rules` - Write hook rules and patterns
- `validate-plugin` - Validate complete plugin structure
