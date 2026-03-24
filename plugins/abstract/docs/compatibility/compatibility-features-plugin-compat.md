# Claude Code Compatibility Features: Plugin-Specific Compatibility

Minimum version requirements and version-specific feature notes for
each plugin in the claude-night-market ecosystem.

> **See Also**:
> [Features Index](compatibility-features.md) |
> [March 2026](compatibility-features-march2026-recent.md) |
> [February 2026 Early](compatibility-features-feb2026-early.md) |
> [February 2026 Late](compatibility-features-feb2026-late.md) |
> [January 2026](compatibility-features-jan2026.md) |
> [Reference](compatibility-reference.md) |
> [2025 Archive](compatibility-features-2025.md)

## Plugin-Specific Compatibility

### Abstract Plugin

**Minimum Version**: 2.0.65+ (recommended 2.0.71+)

**Version-Specific Features**:
- Hook authoring documentation references 2.0.70+ wildcard permissions
- Hook authoring documentation includes 2.0.71+ glob pattern fixes
- Security patterns updated for 2.0.71+ glob validation

**Testing**: All hooks tested with 2.0.71+

### Conservation Plugin

**Minimum Version**: 2.0.65+ (recommended 2.0.74+)

**Version-Specific Features**:
- Context monitoring uses 2.0.65+ status line visibility
- Token tracking uses 2.0.70+ improved accuracy
- 2.0.74+ improved /context visualization
  - Skills/agents grouped by source plugin
  - Better visibility into context consumption
  - Sorted token counts for optimization
- 2.0.74+ LSP integration for token efficiency
  - ~90% token reduction for reference finding
  - Semantic queries vs. broad grep searches
  - Targeted reads vs. bulk file loading

**Recommendations**:
- Use 2.0.70+ for accurate context percentage calculations
- Use 2.0.74+ /context visualization for plugin-level optimization
- use LSP for token-efficient code navigation
- Native visibility replaces manual context estimation

### Sanctum Plugin

**Minimum Version**: 2.0.70+ (recommended 2.0.74+)

**Version-Specific Features**:
- CI/CD workflows benefit from 2.0.71+ MCP server loading fix
- Git operations use glob patterns fixed in 2.0.71+
- 2.0.74+ LSP integration for documentation workflows
  - Reference finding: Locate all usages of documented items
  - API completeness: Verify all public APIs are documented
  - Signature verification: Check docs match actual code
  - Cross-reference validation: validate doc links are accurate

**Recommendations**:
- Use 2.0.71+ for automated PR workflows with MCP
- Use 2.0.74+ with LSP for detailed documentation updates
- GitHub Actions integration requires 2.0.71+ for reliable MCP
- use LSP to validate documentation completeness and accuracy

### Leyline Plugin

**Minimum Version**: 2.0.65+

**Version-Specific Features**:
- MECW patterns reference 2.0.70+ context accuracy
- Error patterns benefit from improved context tracking

### Scry Plugin

**Minimum Version**: 2.0.65+

**Version-Specific Features**:
- Browser recording uses Playwright for automated workflows
- 2.0.72+ adds complementary native Chrome integration
- 2.0.73+ adds image viewing for generated media assets

**Recommendations**:
- Use 2.0.72+ Chrome integration for interactive debugging and live testing
- Use Playwright (scry:browser-recording) for automated recording, CI/CD, and cross-browser
- Both approaches can be combined: develop with Chrome, automate with Playwright
- Use 2.0.73+ image viewing to preview generated GIFs and screenshots

### Imbue Plugin

**Minimum Version**: 2.0.65+

**Version-Specific Features**:
- 2.0.73+ session forking enables parallel evidence analysis
- 2.0.73+ image viewing supports visual evidence artifacts

**Recommendations**:
- Use 2.0.73+ session forking for multi-perspective reviews
- Fork sessions to analyze different evidence paths without context pollution

### Pensive Plugin

**Minimum Version**: 2.0.65+ (recommended 2.0.74+)

**Version-Specific Features**:
- 2.0.73+ session forking enables multi-perspective code reviews
- 2.0.74+ LSP integration for semantic code analysis
  - Impact analysis: Find all references to changed functions
  - Unused code detection: Identify unreferenced exports
  - API consistency: Verify usage patterns
  - Type safety: Validate type usage across codebase

**Recommendations**:
- Use 2.0.74+ with `ENABLE_LSP_TOOL=1` for semantic code review
- Fork sessions for specialized reviews (security, performance, maintainability)
- Combine LSP-powered analysis with traditional pattern matching
- use LSP for accurate impact assessments during refactoring reviews

### Memory-Palace Plugin

**Minimum Version**: 2.0.65+

**Version-Specific Features**:
- 2.0.73+ session forking enables exploratory knowledge intake

**Recommendations**:
- Fork sessions to experiment with different categorization strategies
- Test alternative tagging approaches in forked sessions
