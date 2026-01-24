# Hookify Plugin

**Zero-config behavioral rules - 10 safety rules active immediately upon installation.**

## Overview

Hookify includes **bundled rules that work out of the box**. Just install the plugin and you're protected.

## Zero-Touch Experience

```bash
# Install the plugin
claude install hookify@claude-night-market

# 10 rules are now active:
# - Block force push to main/master
# - Block destructive git operations (reset --hard, clean -fd, etc.)
# - Warn about risky git operations (rebase -i, soft reset, etc.)
# - Warn about large binary files in git
# - Block dangerous dynamic code execution
# - Warn about print statements in Python
# - Require security review for auth code changes
# - Enforce scope-guard for new features
# - Block code without specs (disabled by default)
# - Warn about large file operations
```

## Bundled Rules

Hookify comes with a suite of pre-configured rules designed to enhance safety and workflow consistency. Git operations are protected by blocking force pushes to main branches and destructive commands like hard resets, while risky actions such as interactive rebases trigger warnings. Python development is safeguarded by blocking dynamic code execution and warning about print statements. Additionally, the plugin enforces security reviews for authentication changes, warns about large file operations and commits, and monitors workflow compliance through scope guards.

## Architecture

The plugin architecture centers on a `ConfigLoader` that manages rule definitions. It prioritizes user-defined rules located in the `.claude/` directory, allowing them to override the default bundled rules by name. This configuration is then fed into the `RuleEngine`, which evaluates tool usage against the active rule set during execution. Bundled rules use `Path(__file__)` for portable location resolution, requiring no manual installation.

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
