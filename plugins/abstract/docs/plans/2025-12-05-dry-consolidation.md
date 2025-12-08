# DRY Consolidation Plan for Abstract Plugin

**Date**: 2025-12-05
**Goal**: Eliminate redundant code following DRY principles without adding complexity

## Overview

The abstract plugin has accumulated duplicate implementations of:
1. Token estimation (3+ implementations)
2. Frontmatter parsing (5+ implementations)
3. `find_skill_files()` (3 identical copies)
4. Skill analysis classes with overlapping responsibilities

## Tasks

### Task 1: Create tokens.py - Consolidate Token Logic

**Files to create:**
- `src/abstract/tokens.py`

**Actions:**
1. Move `TokenAnalyzer` class from `utils.py` to new `tokens.py`
2. Add module-level convenience functions that delegate to `TokenAnalyzer`
3. Use consistent formula: `len(text) // 4` as base (matches Claude's ~4 chars/token)
4. Export: `TokenAnalyzer`, `estimate_tokens()`, `analyze_content()`, `check_efficiency()`

**Code template:**
```python
#!/usr/bin/env python3
"""Consolidated token estimation for Abstract.

Single source of truth for all token-related calculations.
Uses ~4 characters per token as the base estimation ratio.
"""

from dataclasses import dataclass

# Move TokenAnalyzer class here from utils.py
# Add module-level functions for convenience
```

**Tests:** Existing tests should pass after imports are updated.

### Task 2: Refactor skills_eval.py - Remove Duplicates

**Files to modify:**
- `src/abstract/skills_eval.py`

**Actions:**
1. Import `TokenAnalyzer` from new `tokens.py`
2. Remove inline token calculation in `TokenUsageTracker` - use `TokenAnalyzer`
3. Remove `_parse_frontmatter()` from `SkillsAuditor` - use `FrontmatterProcessor`
4. Remove inline frontmatter parsing in `ComplianceChecker` - use `FrontmatterProcessor`
5. Keep the high-level classes but have them delegate to centralized utilities

**Key changes:**
- `TokenUsageTracker._calculate_frontmatter_tokens()` → use `FrontmatterProcessor.extract_raw()` + `TokenAnalyzer`
- `SkillsAuditor._parse_frontmatter()` → use `FrontmatterProcessor.parse()`
- `ComplianceChecker.check_compliance()` frontmatter section → use `FrontmatterProcessor`

### Task 3: Clean up utils.py - Remove Wrappers

**Files to modify:**
- `src/abstract/utils.py`

**Actions:**
1. Remove `estimate_tokens()` (line 99) - replaced by `tokens.py`
2. Remove `count_tokens_detailed()` (line 283) - replaced by `tokens.py`
3. Remove `TokenAnalyzer` class (line 377-527) - moved to `tokens.py`
4. Remove `extract_frontmatter()` (line 58) - use `FrontmatterProcessor.extract_raw()` directly
5. Remove `parse_frontmatter_fields()` (line 73) - use `FrontmatterProcessor.parse()` directly
6. Remove `parse_yaml_frontmatter()` (line 201) - use `FrontmatterProcessor.parse()` directly
7. Remove `analyze_token_components()` (line 298) - moved to `tokens.py`
8. Keep utility functions that don't duplicate elsewhere:
   - `find_project_root()`
   - `load_config_with_fallback()`
   - `validate_skill_frontmatter()`
   - `check_meta_skill_indicators()`
   - `find_skill_files()` (keep ONE copy here, remove from base.py)
   - `load_skill_file()`
   - `get_skill_name()`
   - `format_score()`
   - `extract_code_blocks()`
   - `count_sections()`
   - `extract_dependencies()`
   - `find_dependency_file()`

### Task 4: Clean up base.py - Remove Duplicates

**Files to modify:**
- `src/abstract/base.py`

**Actions:**
1. Remove module-level `find_skill_files()` (line 82-94) - keep in utils.py only
2. Remove `AbstractScript.find_skill_files()` method (line 152-166) - use utils version
3. Update `AbstractScript` to import `find_skill_files` from utils
4. Keep:
   - `setup_imports()` (compatibility)
   - `has_frontmatter_file()` (delegates to FrontmatterProcessor)
   - `find_markdown_files()` (module-level)
   - `AbstractScript` class with remaining methods

### Task 5: Run Tests and Verify

**Commands:**
```bash
cd plugins/abstract
uv run pytest tests/ -v
```

**Expected:** All existing tests pass without modification (or with minimal import updates).

## File Change Summary

| File | Action | Est. Lines Changed |
|------|--------|-------------------|
| `src/abstract/tokens.py` | CREATE | +150 |
| `src/abstract/skills_eval.py` | MODIFY | -200, +50 |
| `src/abstract/utils.py` | MODIFY | -250 |
| `src/abstract/base.py` | MODIFY | -30 |
| `src/abstract/__init__.py` | MODIFY | +5 (exports) |

**Net reduction:** ~275 lines of duplicate code

## Dependencies

- Task 2 depends on Task 1 (needs tokens.py)
- Task 3 depends on Task 1 (needs tokens.py)
- Task 4 depends on Task 3 (needs utils.py cleaned first)
- Task 5 depends on Tasks 1-4
