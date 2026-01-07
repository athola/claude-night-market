# Changelog

All notable changes to the hookify plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-06

### Added
- Initial release of hookify plugin for claude-night-market
- Core rule engine with pattern matching
- Configuration loader for markdown-based rules
- Advanced pattern matcher with predefined patterns
- Commands: hookify, list, configure, help
- Skill: writing-rules for comprehensive rule documentation
- Example rules: dangerous-rm, warn-console-log, require-tests, protect-env-files
- Full test suite for core functionality
- Type-safe Python implementation with dataclasses
- Integration with claude-night-market ecosystem

### Features
- **Zero-code rule authoring** - Create rules from natural language
- **Immediate effect** - No restart required for rule changes
- **Rich pattern library** - Predefined patterns for common scenarios
- **Flexible conditions** - Multiple field matching with logical operators
- **Two action modes** - Warn (allow) or block (prevent) operations
- **Event targeting** - Match bash, file, stop, prompt, or all events
- **Markdown-based** - Simple YAML frontmatter + markdown message format

### Enhancements over Anthropic Original
- Night-market plugin patterns and conventions
- Enhanced pattern matching with predefined library
- Pattern suggestion engine
- Comprehensive type safety with Python typing
- Better error messages and validation
- More extensive examples and documentation
- Integration with abstract:hook-* skills
- Full test coverage

### Credits
Inspired by the original [hookify plugin](https://github.com/anthropics/claude-code/tree/main/plugins/hookify)
by Daisy Hollman at Anthropic. Enhanced for the claude-night-market ecosystem.

[1.0.0]: https://github.com/athola/claude-night-market/releases/tag/hookify-v1.0.0
