# Changelog

All notable changes to the `attune` plugin are documented in the main [CHANGELOG.md](../../CHANGELOG.md) at the repository root.

## Plugin-Specific Notes

For detailed attune-specific changes, see the main CHANGELOG under the following sections:
- **v1.4.0** (2026-02-05): Enhanced discoverability for all skills, commands, and agents
- **v1.3.1** (2026-01-21): War Room multi-LLM deliberation framework
- **v1.2.0** (2026-01-02): Full-cycle workflow (brainstorm-plan-execute)
- **v0.1.0** (2026-01-01): Core project initialization

## [1.4.0] - 2026-02-05

### Added
- **Discoverability Enhancement**: All 20 components (9 skills, 9 commands, 2 agents) now feature enhanced automatic discovery
- Description pattern: WHAT + "Use when:" + "Do not use when:" for improved Claude matching
- "When To Use" and "When NOT To Use" sections in all components
- Trigger keyword optimization in all descriptions (5-10 keywords per component)
- Discoverability templates for contributors (`plugins/attune/templates/`)
- Template guide with before/after examples and validation checklist

### Changed
- Enhanced descriptions for all skills following proven discoverability pattern
- Enhanced descriptions for all commands with action-oriented language
- Enhanced agent descriptions with capability focus and invocation context
- Frontmatter updated to distinguish official fields (name, description) from custom metadata
- Standardized section naming: "When To Use" / "When NOT To Use" (title case)

### Improved
- Auto-discovery of skills from natural language user prompts
- Reduced false positives through explicit usage boundaries
- Clear workflow positioning (brainstorm → specify → plan → execute)
- Consistent cross-references to guide users to appropriate alternatives
- Token budget management (3,920 chars for 20 components, avg 196 chars/component)

## Migration Guide

### Upgrading from 0.1.0 to 1.0.0+

**No Breaking Changes**: All existing functionality remains unchanged. New workflow commands are additive.

**New Capabilities Available**:

1. **For new projects** - Use full workflow:
   ```bash
   /attune:brainstorm
   /attune:specify
   /attune:plan
   /attune:project-init
   /attune:execute
   ```

2. **For existing projects** - Continue using as before:
   ```bash
   /attune:project-init
   /attune:upgrade-project
   /attune:validate
   ```

---

**Note**: This file has been simplified to avoid duplication. All release notes are maintained in the main CHANGELOG.md for consistency across the plugin ecosystem.
