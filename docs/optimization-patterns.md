# Optimization Patterns: Context Reduction Methodology

**Purpose**: Systematic approaches for reducing token consumption in Claude Code projects

**Achievement**: 28-33% context reduction through 9 optimization phases

---

## Overview

This document captures proven optimization patterns from the claude-night-market bloat reduction initiative, which achieved ~70,772 tokens saved across 9 phases.

**Key Principles**:
1. **Separation of Concerns**: Data vs. logic, general vs. specific
2. **DRY (Don't Repeat Yourself)**: Shared utilities, single source of truth
3. **Progressive Disclosure**: Information at appropriate depth
4. **Maintainability**: Easy to update, clear to understand
5. **Backwards Compatibility**: Preserve all functionality

---

## Pattern 1: Archive Cleanup

**When to Use**: Project has accumulated historical artifacts

**Savings Potential**: High (33,400 tokens in our case)

### Process

1. **Identify Archives**
   ```bash
   # Find old worktrees, historical docs, obsolete reports
   find . -name ".worktree*" -type d
   find . -name "*-old.md" -o -name "*-archive.md"
   ```

2. **Categorize Content**
   - ✅ Delete: Duplicate information, outdated decisions
   - ⚠️ Review: Historical context that might be referenced
   - 🔄 Migrate: Valuable content buried in archives

3. **Execute Cleanup**
   ```bash
   # Safe deletion with git tracking
   git rm -r .worktrees/old-branch-*
   git commit -m "chore: remove archived worktrees"
   ```

### Example Results
- Deleted 15 archived files
- Removed obsolete documentation
- Cleaned historical decision records
- **Savings**: ~33,400 tokens

---

## Pattern 2: Documentation Refactoring (Hub-and-Spoke)

**When to Use**: Monolithic docs exceed recommended limits (500 lines for reference, 1000 for tutorials)

**Savings Potential**: Medium-High (10,500 tokens)

### Hub-and-Spoke Structure

```
# Before: Monolithic
complete-guide.md (2,000 lines)

# After: Hub-and-Spoke
README.md (150 lines)          ← Hub
├→ getting-started.md (300)
├→ core-concepts.md (400)
├→ advanced-topics.md (500)
└→ api-reference.md (400)
```

### Implementation

1. **Create Hub Document**
   - High-level overview
   - Navigation to sub-documents
   - Quick-start essentials
   - Cross-references

2. **Split by Concern**
   - Each sub-doc has single topic
   - Progressive depth (basic → advanced)
   - Self-contained but linked

3. **Maintain Discoverability**
   - Clear navigation in hub
   - Breadcrumbs in sub-docs
   - Cross-references where relevant

### Directory-Specific Limits

| Directory | Limit | Purpose |
|-----------|-------|---------|
| `docs/` | 500 lines | Strict reference material |
| `book/` | 1000 lines | Lenient tutorials |
| `examples/` | 800 lines | Focused examples |
| `skills/` | 300 lines | Concise instructions |

---

## Pattern 3: Data Extraction

**When to Use**: Scripts contain >100 lines of embedded data

**Savings Potential**: Very High (10,192 tokens from 4 scripts)

See [Data Extraction Pattern Guide](./guides/data-extraction-pattern.md) for comprehensive details.

### Quick Summary

```python
# Before: Embedded data (830 lines)
def _topics():
    return [Topic(...), Topic(...), ...]  # Hundreds of lines

# After: Load from YAML
def load_topics():
    with open("data/seed_topics.yaml") as f:
        return [Topic.from_dict(t) for t in yaml.safe_load(f)["topics"]]
```

**Results**: 75% average code reduction

---

## Pattern 4: Shared Utilities Abstraction

**When to Use**: Code duplication across multiple scripts/skills

**Savings Potential**: Medium (2,400 tokens)

### Process

1. **Identify Duplication**
   ```bash
   # Find similar code patterns
   grep -r "def extract_snippet" plugins/*/scripts/
   ```

2. **Create Shared Module**
   ```python
   # plugins/pensive/utils/content_parser.py
   def extract_code_snippet(file_path: str, start: int, end: int) -> str:
       """Reusable snippet extraction."""
       # Shared implementation
   ```

3. **Update Consumers**
   ```python
   # Before: Duplicated in 4 files
   def _extract_snippet(self, ...):
       # 50 lines of code

   # After: Import from utils
   from pensive.utils import extract_code_snippet
   ```

### Example: Pensive Review Skills

**Created**:
- `content_parser.py`: File parsing utilities
- `severity_mapper.py`: Issue categorization
- `report_generator.py`: Markdown report formatting

**Enhanced**: `BaseReviewSkill` with shared helper methods

**Results**:
- ~400 lines of utilities replace ~800 lines of duplicates
- 4 review skills now share common code
- Consistent behavior across all reviews

---

## Pattern 5: Examples Repository

**When to Use**: Large example files inflate plugin context

**Savings Potential**: Medium (5,540 tokens)

### Strategy

1. **Create Centralized Location**
   ```
   examples/
   └── attune/
       ├── microservices-example.md (726 lines)
       └── library-example.md (699 lines)
   ```

2. **Replace with Stubs**
   ```markdown
   # plugins/attune/examples/microservices-example.md
   # Microservices Example (Stub)

   Full example: `/examples/attune/microservices-example.md`

   **Quick Summary**: This example demonstrates...

   [View Full Example](../../../examples/attune/microservices-example.md)
   ```

3. **Keep Essential Examples**
   - Quick-start examples stay in plugin
   - Comprehensive worked examples move to `/examples/`
   - Decision: <400 lines stays, >600 lines moves

### Results
- 1,425 lines moved to `/examples/`
- 38 lines of stubs remain in plugin
- **Savings**: ~1,385 lines = ~5,540 tokens

---

## Pattern 6: Progressive Disclosure

**When to Use**: Documentation must serve both beginners and experts

**Savings Potential**: Medium (3,200 tokens from 8 files)

### Technique

```markdown
# Hub Document (200 lines)

## Quick Start
Essential information for 80% of users.

## Core Concepts
Mid-level details with links to deep dives.

See: [Advanced Topics](./advanced.md)
See: [API Reference](./api-reference.md)
See: [Migration Guide](./migration.md)
```

### Application Example

**Before**: Single `error-handling-complete.md` (1,500 lines)

**After**:
- `error-handling.md` (400 lines) - Core concepts
- `error-patterns.md` (500 lines) - Common patterns
- `error-recovery.md` (400 lines) - Advanced recovery
- `error-reference.md` (200 lines) - API reference

**Result**: Same content, better organization, easier to navigate

---

## Pattern 7: TODO Audit

**When to Use**: Periodic maintenance (quarterly recommended)

**Savings Potential**: Low-Medium (130 tokens)

### Process

```bash
# Comprehensive scan
rg "TODO|FIXME|HACK|XXX" --type py --type md

# Categorize findings
# - Remove: Completed or obsolete
# - Track: Move to issue tracker
# - Keep: Short-term reminders in code
```

### Results
- Confirmed excellent hygiene (minimal cleanup needed)
- Removed false positives
- Low savings but good maintenance practice

---

## Pattern 8: Anti-Pattern Removal

**When to Use**: Identify common anti-patterns during review

**Savings Potential**: Medium (5,410 tokens)

### Common Anti-Patterns

#### "Complete Guide" Files
**Problem**: Monolithic files that try to cover everything

**Solution**: Split into modular guides
```
❌ rust-complete-guide.md (2,500 lines)

✅ rust/
  ├── README.md (hub)
  ├── getting-started.md
  ├── ownership-guide.md
  ├── concurrency-guide.md
  └── best-practices.md
```

#### Verbose Examples
**Problem**: Examples with too much explanation

**Solution**: Show, don't tell
```markdown
❌ Before (150 lines):
This example demonstrates how to use the API. First, you need to
import the module. Then you create an instance. After that, you
configure it. Finally, you call the method...

✅ After (30 lines):
```python
# Example: Basic usage
from mylib import Client

client = Client(api_key="...")
result = client.process(data)
print(result)
```

**Explanation**: [See detailed walkthrough](./examples/basic-usage.md)

#### Redundant Documentation
**Problem**: Same content in multiple places

**Solution**: Single source of truth with references
```markdown
See: [Authentication Guide](./auth.md) for details
```

---

## Optimization Workflow

### Phase-Based Approach

#### Phase 1: Discovery
```bash
# Run bloat scan
/conserve:bloat-scan

# Identify candidates
# - Large files (>500 lines for docs, >800 for code)
# - Duplicate content
# - Archived materials
```

#### Phase 2: Analysis
```
For each candidate:
1. Measure current size
2. Identify optimization opportunity
3. Estimate savings potential
4. Assess effort required
5. Calculate ROI (savings / effort)
```

#### Phase 3: Planning
```
Prioritize by:
1. High ROI (quick wins)
2. High impact (large savings)
3. Low risk (easy to validate)
4. Strategic value (improves maintainability)
```

#### Phase 4: Execution
```
For each optimization:
1. Create backup branch
2. Apply pattern systematically
3. Validate functionality preserved
4. Document changes
5. Commit with clear message
```

#### Phase 5: Validation
```bash
# Verify no functionality lost
make test

# Measure impact
du -h plugins/*/  # Before/after comparison
wc -l **/*.{py,md}  # Line count

# Calculate token savings
# Estimate: ~4 tokens per line
```

---

## Metrics and Measurement

### Token Estimation
```
Conservative: 1 line = 3 tokens
Average: 1 line = 4 tokens
Complex: 1 line = 5 tokens
```

### Success Criteria
- ✅ 0 functionality loss
- ✅ All tests pass
- ✅ Documentation updated
- ✅ Clear git history
- ✅ Measurable token savings

### Tracking Template

```markdown
## Phase N: [Name]

**Before**:
- File X: Y lines
- File Z: W lines
- Total: N lines

**After**:
- File X: Y' lines
- File Z: W' lines
- Total: N' lines

**Savings**: (N - N') lines × 4 = ~T tokens
```

---

## Real-World Results

### Phase-by-Phase Breakdown

| Phase | Focus | Tokens Saved |
|-------|-------|--------------|
| 1: Archive Cleanup | Historical artifacts | 33,400 |
| 2: Doc Refactoring | Hub-and-spoke | 10,500 |
| 3: TODO Audit | Code hygiene | 130 |
| 4: Anti-Pattern Removal | Complete-guide files | 5,410 |
| 5: Progressive Disclosure | Documentation standards | 3,200 |
| 6: Shared Utilities | Code deduplication | 2,400 |
| 7: Tutorial Split | (Deferred) | 0 |
| 8: Examples Repo | Centralized examples | 5,540 |
| 9: Data Extraction | YAML configuration | 10,192 |
| **Total** | | **~70,772** |

### Impact Summary
- **Context Reduction**: 28-33%
- **Files Deleted**: 19
- **Files Refactored**: 19
- **Data Files Created**: 8 (YAML)
- **Utility Modules Created**: 4

---

## Best Practices

### 1. Incremental Changes
- Apply one pattern at a time
- Validate after each change
- Git commit frequently
- Easy to rollback if needed

### 2. Systematic Approach
- **Scan**: Identify all candidates
- **Analyze**: Measure and prioritize
- **Execute**: Apply pattern methodically
- **Validate**: Verify no regressions
- **Document**: Capture decisions

### 3. Preserve Functionality
- All tests must pass
- No breaking changes
- Backwards compatibility maintained
- Clear migration path if needed

### 4. Documentation
- Document each optimization
- Capture methodology
- Provide examples
- Enable future replication

### 5. Avoid Scope Creep
- Stick to optimization goals
- Resist "while I'm here" changes
- Balance perfect vs. good enough
- Know when to defer

---

## When to Apply Optimizations

### High Priority
- ✅ Project exceeding context limits
- ✅ Slow Claude Code performance
- ✅ High token costs
- ✅ Onboarding friction

### Medium Priority
- ⚠️ Files approaching size limits
- ⚠️ Accumulated technical debt
- ⚠️ Duplicate code patterns
- ⚠️ Quarterly maintenance

### Low Priority
- ℹ️ Minor inefficiencies
- ℹ️ Aesthetic improvements
- ℹ️ Nice-to-have refactoring
- ℹ️ Premature optimization

---

## Future Opportunities

### Automation
- Build tooling to detect refactoring opportunities
- Pre-commit hooks for size limits
- Automated bloat scanning in CI
- Monthly optimization reports

### Configuration Management
- Centralized configuration system
- Dynamic plugin loading
- Lazy loading for large data structures
- Environment-specific configs

### Pattern Library
- Reusable optimization templates
- Pattern detection tools
- Automated application where safe
- Community-contributed patterns

---

## See Also

- [Data Extraction Pattern](./guides/data-extraction-pattern.md)
- [Documentation Standards](./guides/documentation-standards.md)
- [Conserve Plugin](../plugins/conserve/README.md)
- [Bloat Scan Report](../bloat-scan-report-20260109.md)

---

**Methodology Status**: ✅ Battle-tested across 9 phases
**Maintained by**: claude-night-market core team
**Last Updated**: 2026-01-10
