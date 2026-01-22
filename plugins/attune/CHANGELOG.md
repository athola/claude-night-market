# Changelog

All notable changes to the `attune` plugin are documented in the main [CHANGELOG.md](../../CHANGELOG.md) at the repository root.

## Plugin-Specific Notes

For detailed attune-specific changes, see the main CHANGELOG under the following sections:
- **v1.3.1** (2026-01-21): War Room multi-LLM deliberation framework
- **v1.2.0** (2026-01-02): Full-cycle workflow (brainstorm-plan-execute)
- **v0.1.0** (2026-01-01): Core project initialization

## Migration Guide

### Upgrading from 0.1.0 to 1.0.0+

**No Breaking Changes**: All existing functionality remains unchanged. New workflow commands are additive.

**New Capabilities Available**:

1. **For new projects** - Use full workflow:
   ```bash
   /attune:brainstorm
   /attune:specify
   /attune:plan
   /attune:init
   /attune:execute
   ```

2. **For existing projects** - Continue using as before:
   ```bash
   /attune:init
   /attune:upgrade-project
   /attune:validate
   ```

---

**Note**: This file has been simplified to avoid duplication. All release notes are maintained in the main CHANGELOG.md for consistency across the plugin ecosystem.
