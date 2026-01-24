# Hookify

Behavioral rules and safety hooks for Claude Code.

## Overview

Hookify provides a suite of pre-configured rules that are active immediately upon installation. These rules protect critical git branches, prevent destructive operations, and enforce security and workflow standards without requiring manual configuration.

### Active Rules

The following rules are enabled by default:
- **Git Safety**: Blocks force pushes to `main`/`master` and destructive operations like `reset --hard` or `clean -fd`. Warnings are issued for risky actions such as interactive rebases or soft resets.
- **File Management**: Monitors for large binary files or large file operations that could bloat the repository or context.
- **Code Standards**: Blocks dangerous dynamic code execution and warns about print statements in Python. Authentication changes require a security review, and new features must comply with `scope-guard` policies.

## Architecture

Hookify uses a `ConfigLoader` to manage behavioral rules. It automatically searches for user-defined rules in the `.claude/` directory, which can override any of the default bundled rules. These configurations are processed by the `RuleEngine` to evaluate tool usage against the active rule set during execution. Bundled rules resolve their locations relative to the plugin's installation path to ensure portability across different environments.

## Installation

```bash
claude install hookify@claude-night-market
```

Or from source:

```bash
git clone https://github.com/athola/claude-night-market
cd claude-night-market
claude install ./plugins/hookify
```

## Documentation

- **Rule Catalog**: `Skill(hookify:rule-catalog)`
- **Rule Writing**: `Skill(hookify:writing-rules)`
- **Hook Scope**: `Skill(abstract:hook-scope-guide)` (requires abstract plugin)

## Optional Dependencies

| Dependency | Purpose | Fallback |
|------------|---------|----------|
| abstract plugin | `hook-scope-guide` skill for advanced hook patterns | Hookify works fully without it; skill unavailable |

Hookify is fully functional without optional dependencies. The abstract plugin provides additional guidance for advanced hook development patterns.

## Credits

Inspired by the original [hookify plugin](https://github.com/anthropics/claude-code/tree/main/plugins/hookify) by Daisy Hollman at Anthropic.

Enhanced for claude-night-market with:
- Zero-config bundled rules
- Portable path resolution via `__file__`
- User override support
- Night-market plugin integration
