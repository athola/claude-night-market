# Imbue Plugin Modularization Roadmap

**Status**: Planning
**Priority**: High (for catchup), Medium (for diff-analysis)
**Expected Impact**: 30% overall token reduction

## Quick Reference

### Current State
```
imbue/skills/
├── catchup/SKILL.md                 [146 lines, 1,539 tokens] ⚠️ MODULARIZE
├── diff-analysis/SKILL.md           [128 lines, 1,527 tokens] ⚠️ MODULARIZE
├── evidence-logging/SKILL.md        [ 90 lines,   988 tokens] ✅ OPTIMAL
├── review-core/SKILL.md             [ 68 lines,   880 tokens] ✅ OPTIMAL
└── structured-output/SKILL.md       [101 lines,   946 tokens] ✅ OPTIMAL
```

### Target State
```
imbue/skills/
├── catchup/
│   ├── SKILL.md                     [~50 lines,   ~700 tokens] Hub
│   └── modules/
│       ├── git-catchup-patterns.md  [~30 lines,   ~400 tokens]
│       ├── document-analysis.md     [~25 lines,   ~300 tokens]
│       └── log-analysis.md          [~25 lines,   ~300 tokens]
├── diff-analysis/
│   ├── SKILL.md                     [~60 lines,   ~800 tokens] Hub
│   └── modules/
│       ├── semantic-categorization.md [~25 lines, ~300 tokens]
│       ├── risk-assessment.md         [~30 lines, ~400 tokens]
│       └── git-diff-patterns.md       [~15 lines, ~200 tokens]
├── evidence-logging/SKILL.md        [ 90 lines,   988 tokens] No change
├── review-core/SKILL.md             [ 68 lines,   880 tokens] No change
└── structured-output/SKILL.md       [101 lines,   946 tokens] No change
```

## Phase 1: Catchup Modularization (HIGH PRIORITY)

### Objective
Reduce catchup baseline from 1,539 tokens to ~700 tokens (54% reduction)

### Tasks

#### 1. Create Module Directory Structure
```bash
cd /home/alext/claude-night-market/plugins/imbue/skills/catchup
mkdir -p modules
```

#### 2. Extract Git Patterns Module
**File**: `modules/git-catchup-patterns.md`

**Content**:
- Git context establishment commands
- Delta capture with git diff
- Git-specific insights extraction
- Integration with sanctum:git-workspace-review

**Estimated**: ~30 lines, ~400 tokens

#### 3. Extract Document Analysis Module
**File**: `modules/document-analysis-patterns.md`

**Content**:
- Meeting notes analysis
- Document revision tracking
- Sprint/ticket catchup
- Generic document delta patterns

**Estimated**: ~25 lines, ~300 tokens

#### 4. Extract Log Analysis Module
**File**: `modules/log-analysis-patterns.md`

**Content**:
- System log patterns
- Event stream analysis
- Metric-based catchup
- Time-window analysis

**Estimated**: ~25 lines, ~300 tokens

#### 5. Refactor Hub (SKILL.md)
**Keep**:
- Overview and philosophy
- High-level 4-step methodology
- When to use
- Activation patterns
- Exit criteria
- Module loading guidance

**Remove**:
- Detailed git examples → move to modules/git-catchup-patterns.md
- Generic application details → move to appropriate modules
- Redundant integration notes

**Add**:
```yaml
progressive_loading: true
module_strategy: context-based
```

**Update estimated_tokens**: 1600 → 700

#### 6. Add Module Loading Logic

In hub SKILL.md, add:
```markdown
## Progressive Loading

This skill uses context-based module loading:

### Git Context
If working with git repositories:
- Load `modules/git-catchup-patterns.md` for git-specific commands
- Consider using `sanctum:git-workspace-review` for initial context

### Document Context
If analyzing documents, notes, or tickets:
- Load `modules/document-analysis-patterns.md` for document-specific patterns

### Log/Event Context
If analyzing logs or event streams:
- Load `modules/log-analysis-patterns.md` for time-series patterns

### All Contexts
Always available: evidence-logging integration, TodoWrite workflow
```

### Validation

**Before merge**:
```bash
# Check structure
python /home/alext/claude-night-market/plugins/abstract/scripts/abstract_validator.py \
  --scan catchup/

# Estimate tokens
python /home/alext/claude-night-market/plugins/abstract/scripts/token_estimator.py \
  --file catchup/SKILL.md --format json

# Verify <800 tokens for hub
# Run tests
pytest tests/unit/skills/test_catchup.py -v
```

### Success Criteria
- [ ] Hub SKILL.md < 800 tokens
- [ ] All modules created with proper frontmatter
- [ ] Tests pass
- [ ] No functionality lost
- [ ] Clear module loading guidance
- [ ] Integration with sanctum documented

## Phase 2: Diff-Analysis Modularization (MEDIUM PRIORITY)

### Objective
Reduce diff-analysis baseline from 1,527 tokens to ~800 tokens (48% reduction)

### Tasks

#### 1. Create Module Directory Structure
```bash
cd /home/alext/claude-night-market/plugins/imbue/skills/diff-analysis
mkdir -p modules
```

#### 2. Extract Semantic Categorization Module
**File**: `modules/semantic-categorization.md`

**Content**:
- Change categories (additions, modifications, deletions, renames)
- Semantic categories (features, fixes, refactors, tests, docs, config)
- Cross-cutting change detection
- Categorization workflow

**Estimated**: ~25 lines, ~300 tokens

#### 3. Extract Risk Assessment Module
**File**: `modules/risk-assessment-framework.md`

**Content**:
- Risk indicators (breaking changes, security, data integrity, etc.)
- Risk levels (low, medium, high)
- Test coverage assessment
- Risk scoring methodology

**Estimated**: ~30 lines, ~400 tokens

**Note**: This module may be referenced by pensive review skills

#### 4. Extract Git Diff Patterns Module
**File**: `modules/git-diff-patterns.md`

**Content**:
- Git diff commands (--name-only, --diff-filter, --stat)
- Git-specific categorization
- Integration with sanctum:git-workspace-review

**Estimated**: ~15 lines, ~200 tokens

#### 5. Refactor Hub (SKILL.md)
**Keep**:
- Overview and philosophy
- High-level 4-step methodology
- When to use
- Activation patterns
- Exit criteria
- Module references

**Remove**:
- Detailed categorization tables → move to modules/semantic-categorization.md
- Risk assessment details → move to modules/risk-assessment-framework.md
- Git commands → move to modules/git-diff-patterns.md

**Add**:
```yaml
progressive_loading: true
module_strategy: workflow-based
```

**Update estimated_tokens**: 1800 → 800

#### 6. Add Module Loading Logic

In hub SKILL.md:
```markdown
## Progressive Loading

Load modules based on workflow stage:

### Always Load
- `modules/semantic-categorization.md` for change categorization

### Conditional Loading
- `modules/risk-assessment-framework.md` when risk assessment is needed
- `modules/git-diff-patterns.md` when working with git repositories

### Integration
- Use `sanctum:git-workspace-review` for git data gathering
- Use `imbue:evidence-logging` for capturing analysis evidence
```

### Validation

**Before merge**:
```bash
# Check structure
python /home/alext/claude-night-market/plugins/abstract/scripts/abstract_validator.py \
  --scan diff-analysis/

# Estimate tokens
python /home/alext/claude-night-market/plugins/abstract/scripts/token_estimator.py \
  --file diff-analysis/SKILL.md --format json

# Verify <900 tokens for hub
# Run tests
pytest tests/unit/skills/test_diff_analysis.py -v
```

### Success Criteria
- [ ] Hub SKILL.md < 900 tokens
- [ ] All modules created
- [ ] Risk framework reusable by pensive
- [ ] Tests pass
- [ ] Clear loading strategy
- [ ] Integration documented

## Phase 3: Cross-Plugin Integration (MEDIUM PRIORITY)

### Objective
Eliminate duplication and establish clear integration patterns

### Tasks

#### 1. Reference Sanctum from Imbue
Update catchup and diff-analysis to reference sanctum:git-workspace-review:

```markdown
## Git Context Gathering

Before running catchup analysis on git repositories, use
`sanctum:git-workspace-review` to gather repository context:
- Repository confirmation (pwd, branch)
- Status overview (staged vs unstaged)
- Diff statistics
- Diff details

Then proceed with catchup-specific insight extraction.
```

**Files to update**:
- `catchup/modules/git-catchup-patterns.md`
- `diff-analysis/modules/git-diff-patterns.md`

#### 2. Establish Risk Framework as Shared Resource
Document that `diff-analysis/modules/risk-assessment-framework.md` is
authoritative for risk assessment.

Update pensive review skills to reference:
```markdown
## Risk Assessment

Use `imbue:diff-analysis` risk assessment framework:
- Risk indicators
- Risk levels
- Scoring methodology
```

**Affected pensive skills**:
- rust-review
- api-review
- architecture-review
- bug-review

#### 3. Standardize Finding Format
Update pensive skills to use imbue:structured-output format:

```markdown
## Output Format

Format findings using `imbue:structured-output` standards:

### [SEVERITY] Finding Title
**Location**: file.rs:123
**Category**: Security | Performance | Correctness | Style
**Description**: Brief explanation
**Evidence**: [E1, E2]
**Recommendation**: Specific steps
```

#### 4. Document Evidence Logging Dependencies
Add `imbue:evidence-logging` as declared dependency where used:

**Update frontmatter in**:
- catchup/SKILL.md
- diff-analysis/SKILL.md
- review-core/SKILL.md

```yaml
dependencies: [imbue:evidence-logging]
```

### Success Criteria
- [ ] No git command duplication between imbue and sanctum
- [ ] Risk framework referenced consistently
- [ ] Finding format standardized across plugins
- [ ] Dependencies declared properly

## Phase 4: Testing and Validation (ONGOING)

### Unit Tests

**Add modularization tests**:
```python
# tests/unit/skills/test_catchup_modular.py

def test_catchup_hub_loads_under_800_tokens():
    """Verify hub loads under token budget."""
    tokens = estimate_tokens("catchup/SKILL.md")
    assert tokens < 800

def test_catchup_modules_exist():
    """Verify all modules are present."""
    assert Path("catchup/modules/git-catchup-patterns.md").exists()
    assert Path("catchup/modules/document-analysis-patterns.md").exists()
    assert Path("catchup/modules/log-analysis-patterns.md").exists()

def test_catchup_progressive_loading_flag():
    """Verify progressive loading is enabled."""
    frontmatter = parse_frontmatter("catchup/SKILL.md")
    assert frontmatter.get("progressive_loading") is True
```

### Integration Tests

**Add cross-plugin tests**:
```python
# tests/integration/test_imbue_sanctum_integration.py

def test_catchup_references_sanctum_git_review():
    """Verify catchup references sanctum for git operations."""
    content = Path("catchup/modules/git-catchup-patterns.md").read_text()
    assert "sanctum:git-workspace-review" in content

def test_no_git_command_duplication():
    """Ensure imbue doesn't duplicate sanctum git commands."""
    # Check that git commands are references, not implementations
```

### Performance Tests

**Add token consumption validation**:
```python
# tests/performance/test_token_reduction.py

def test_modular_catchup_reduces_tokens():
    """Verify modularization achieves expected reduction."""
    baseline = 1539  # Original
    hub_tokens = estimate_tokens("catchup/SKILL.md")
    reduction = (baseline - hub_tokens) / baseline
    assert reduction > 0.50  # >50% reduction

def test_all_skills_under_budget():
    """Ensure all skill hubs under 1000 tokens."""
    for skill in ["catchup", "diff-analysis"]:
        tokens = estimate_tokens(f"{skill}/SKILL.md")
        assert tokens < 1000
```

## Timeline

### Week 1: Catchup Modularization
- Day 1: Create modules, extract content
- Day 2: Refactor hub, add loading logic
- Day 3: Update tests, validate

### Week 2: Diff-Analysis Modularization
- Day 1: Create modules, extract content
- Day 2: Refactor hub, add loading logic
- Day 3: Update tests, validate

### Week 3: Cross-Plugin Integration
- Day 1-2: Update references, standardize patterns
- Day 3: Integration testing

### Week 4: Validation and Refinement
- Day 1-2: Performance testing, token validation
- Day 3: Documentation updates

## Rollback Plan

If modularization causes issues:

1. **Immediate rollback**:
   ```bash
   git checkout HEAD~1 -- plugins/imbue/skills/catchup
   git checkout HEAD~1 -- plugins/imbue/skills/diff-analysis
   ```

2. **Preserve modules**:
   - Keep modules for reference
   - Merge back into monolithic if needed

3. **Test coverage**:
   - Ensure tests still pass with monolithic version
   - Document what failed

## Success Metrics

### Token Reduction
- [ ] Catchup hub: <800 tokens (from 1,539)
- [ ] Diff-analysis hub: <900 tokens (from 1,527)
- [ ] Overall baseline: <4,100 tokens (from 5,880)
- [ ] 30%+ reduction in total baseline tokens

### Quality Maintenance
- [ ] All tests pass
- [ ] No functionality lost
- [ ] Activation patterns still work
- [ ] Integration with other plugins intact

### Reusability
- [ ] Risk framework used by pensive
- [ ] Finding format standardized
- [ ] Git patterns reference sanctum
- [ ] Evidence logging declared as dependency

## Notes

- Keep evidence-logging, review-core, and structured-output monolithic
- These are already at optimal size (68-101 lines, 880-988 tokens)
- Modularization would add overhead without benefit

## References

- Full analysis: `/home/alext/claude-night-market/plugins/imbue/skills-analysis-report-2025-12-05.md`
- Modular-skills guide: `/home/alext/claude-night-market/plugins/abstract/skills/modular-skills/SKILL.md`
- Token estimator: `/home/alext/claude-night-market/plugins/abstract/scripts/token_estimator.py`
- Skill analyzer: `/home/alext/claude-night-market/plugins/abstract/scripts/skill_analyzer.py`
