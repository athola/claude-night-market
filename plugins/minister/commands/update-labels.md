---
name: update-labels
description: Reorganize GitHub issue labels with professional taxonomy - creates type, priority, and effort labels
usage: /update-labels [--repo <owner/repo>] [--dry-run] [--preserve <label>...]
---

# Update Labels

Reorganizes GitHub issue labels into a professional taxonomy. Creates distinct labels for issue types (feature, bugfix, test, docs, etc.), priorities, and effort estimates, then re-labels all issues accordingly.

**Custom Labels**: The taxonomy below serves as a foundation. **You should create custom labels** for project-specific needs:

**When to Add Custom Labels:**
- **Component areas** (e.g., `frontend`, `backend`, `api`, `database`)
- **Plugin/module names** (e.g., `sanctum`, `minister`, `pensive`)
- **Workflow states** (e.g., `blocked`, `ready-for-review`, `needs-investigation`)
- **Team ownership** (e.g., `team-platform`, `team-product`)
- **Technology-specific** (e.g., `python`, `typescript`, `rust`)

**Good Custom Label Examples:**
```bash
# Component-based
gh label create "frontend" --color "#C5DEF5" --description "Frontend/UI changes"
gh label create "api" --color "#006B75" --description "API and backend services"

# Project-specific
gh label create "sanctum" --color "#9B59B6" --description "Sanctum plugin work"
gh label create "hooks" --color "#E67E22" --description "Hook development"

# Workflow-specific
gh label create "blocked" --color "#B60205" --description "Blocked by external dependency"
gh label create "ready-for-review" --color "#0E8A16" --description "Ready for code review"
```

Custom labels should complement (not replace) the standard taxonomy. Keep them focused on project-specific classification that adds value beyond type/priority/effort.

## Arguments

- `--repo <owner/repo>` - Target repository (default: current)
- `--dry-run` - Preview changes without applying them
- `--preserve <label>...` - Labels to keep unchanged (e.g., plugin-specific labels)
- `--skip-relabel` - Only create labels, don't update issues
- `--interactive` - Confirm each issue update

## Label Taxonomy

### Type Labels (Mutually Exclusive)

| Label | Color | Description |
|-------|-------|-------------|
| `feature` | `#1D76DB` | New functionality |
| `bugfix` | `#D73A4A` | Bug fixes |
| `test` | `#0E8A16` | Testing improvements |
| `docs` | `#0075CA` | Documentation improvements |
| `refactor` | `#FBCA04` | Code restructuring without behavior change |
| `performance` | `#5319E7` | Optimization and efficiency |
| `ci-cd` | `#006B75` | CI/CD and automation |
| `research` | `#C5DEF5` | Investigation and exploration |

### Priority Labels

| Label | Color | Description |
|-------|-------|-------------|
| `high-priority` | `#B60205` | Urgent or blocking |
| `medium-priority` | `#FBCA04` | Normal priority |
| `low-priority` | `#0E8A16` | Nice-to-have |

### Effort Labels

| Label | Color | Description |
|-------|-------|-------------|
| `small-effort` | `#C2E0C6` | < 2 hours |
| `medium-effort` | `#FEF2C0` | 2-8 hours |
| `large-effort` | `#F9D0C4` | > 1 day |

### Standard Labels (Preserved)

- `good first issue` - Good for newcomers
- `help wanted` - Extra attention is needed
- `duplicate`, `invalid`, `wontfix`, `question` - Status labels

## Workflow

### Phase 1: Analyze Current State

```bash
# List existing labels
gh label list --json name,description,color

# List all open issues with labels
gh issue list --state open --json number,title,labels
```

Identify:
- Labels to create (from taxonomy above)
- Labels to rename (e.g., `bug` -> `bugfix`, `documentation` -> `docs`)
- Labels to delete (e.g., `enhancement` catch-all)
- Labels to preserve (plugin-specific, user-specified)

### Phase 2: Create/Update Labels

For each label in the taxonomy:

```bash
# Create if doesn't exist
gh label create "<name>" --description "<desc>" --color "<color>"

# Or update if exists with wrong attributes
gh label edit "<old-name>" --name "<new-name>" --description "<desc>" --color "<color>"
```

### Phase 3: Classify Issues

For each open issue, analyze and determine appropriate labels:

**Type Classification Rules:**

| Issue Pattern | Type Label |
|---------------|------------|
| Title contains: `feat`, `add`, `implement`, `create` | `feature` |
| Title contains: `fix`, `bug`, `broken`, `error` | `bugfix` |
| Title contains: `test`, `coverage`, `spec` | `test` |
| Title contains: `doc`, `readme`, `guide` | `docs` |
| Title contains: `refactor`, `cleanup`, `rename` | `refactor` |
| Title contains: `perf`, `optim`, `speed`, `slow` | `performance` |
| Title contains: `ci`, `cd`, `pipeline`, `deploy` | `ci-cd` |
| Title contains: `research`, `investigate`, `explore`, `discuss` | `research` |

**Effort Classification Rules:**

| Indicator | Effort Label |
|-----------|--------------|
| Has `good first issue` label | `small-effort` |
| Body mentions "quick", "simple", "trivial" | `small-effort` |
| Body mentions "complex", "significant", "major" | `large-effort` |
| Default for features | `medium-effort` |

### Phase 4: Apply Labels

```bash
# For each issue
gh issue edit <number> \
  --add-label "<type-label>" \
  --add-label "<effort-label>" \
  --remove-label "enhancement"  # Remove catch-all
```

### Phase 5: Cleanup Obsolete Labels

```bash
# Delete labels that are now redundant
gh label delete "enhancement" --yes
gh label delete "suggestion" --yes
```

### Phase 6: Report Results

Display summary:

```markdown
## Label Taxonomy Update Complete

### Labels Created
| Label | Description |
|-------|-------------|
| feature | New functionality |
| ... | ... |

### Labels Renamed
| Old | New |
|-----|-----|
| documentation | docs |
| bug | bugfix |

### Labels Deleted
- enhancement (replaced by specific types)
- suggestion (redundant)

### Issues Updated
| Type | Count |
|------|-------|
| feature | 26 |
| test | 15 |
| docs | 8 |
| ... | ... |

**Total**: 60 issues updated
```

## Examples

### Example 1: Default Usage

```bash
/update-labels

Analyzing labels in athola/claude-night-market...

Current State:
- 12 existing labels
- 60 open issues
- 45 issues using 'enhancement' catch-all

Creating Labels:
  OK feature - New functionality
  OK bugfix - Bug fixes
  OK test - Testing improvements
  ...

Renaming Labels:
  OK documentation -> docs

Deleting Labels:
  OK enhancement (45 issues migrated)

Classifying Issues:
  #99 wrapper_generator.py -> feature, medium-effort
  #108 mutation testing -> test, large-effort
  ...

Summary:
| Type | Count |
|------|-------|
| feature | 26 |
| test | 15 |
| docs | 8 |
```

### Example 2: Dry Run

```bash
/update-labels --dry-run

[DRY RUN] Would create labels:
  - feature (#1D76DB)
  - bugfix (#D73A4A)
  ...

[DRY RUN] Would update issues:
  #99: +feature, +medium-effort, -enhancement
  #108: +test, +large-effort, -enhancement
  ...

No changes made.
```

### Example 3: Preserve Plugin Labels

```bash
/update-labels --preserve sanctum minister

Preserving labels: sanctum, minister

Creating/updating standard taxonomy...
Skipping: sanctum (preserved)
Skipping: minister (preserved)
...
```

### Example 4: Specific Repository

```bash
/update-labels --repo athola/other-repo

Targeting: athola/other-repo
...
```

## Classification Heuristics

### Title Pattern Matching

```python
TYPE_PATTERNS = {
    'feature': r'(feat|add|implement|create|enable|support)',
    'bugfix': r'(fix|bug|broken|error|crash|fail)',
    'test': r'(test|coverage|spec|mock|assert)',
    'docs': r'(doc|readme|guide|example|tutorial)',
    'refactor': r'(refactor|cleanup|rename|reorganize|simplify)',
    'performance': r'(perf|optim|speed|slow|fast|memory|cache)',
    'ci-cd': r'(ci|cd|pipeline|deploy|workflow|action)',
    'research': r'(research|investigate|explore|discuss|question)',
}
```

### Effort Estimation

```python
EFFORT_INDICATORS = {
    'small': ['quick', 'simple', 'trivial', 'typo', 'minor'],
    'large': ['complex', 'significant', 'major', 'rewrite', 'architecture'],
}

# Default effort by type
DEFAULT_EFFORT = {
    'feature': 'medium',
    'bugfix': 'small',
    'test': 'medium',
    'docs': 'small',
    'refactor': 'medium',
    'performance': 'medium',
    'ci-cd': 'medium',
    'research': 'large',
}
```

## Error Handling

### Insufficient Permissions

```markdown
Error: Insufficient permissions for athola/repo

Required: Write access to issues and labels
Current: Read-only

Request access or use a different repository.
```

### Label Conflict

```markdown
Warning: Label 'test' already exists with different color

Existing: #FF0000
Taxonomy: #0E8A16

Options:
1. Update to taxonomy color (recommended)
2. Keep existing color
3. Skip this label

Choice [1/2/3]:
```

### Rate Limiting

```markdown
Warning: GitHub API rate limit approaching

Remaining: 50 requests
Issues to process: 100

Options:
1. Continue (may hit limit)
2. Process first 40 issues now, continue later
3. Abort

Choice [1/2/3]:
```

## Best Practices

### DO:
- Run with `--dry-run` first to preview changes
- Preserve plugin-specific labels with `--preserve`
- Review classification results before confirming
- Update documentation after major taxonomy changes

### DON'T:
- Delete labels that are actively used without migration
- Create too many labels (keep taxonomy focused)
- Mix classification schemes (pick one and stick with it)
- Run on repositories you don't own without permission

## Integration

### With Other Minister Commands

- Use after `/create-issue` to ensure new issues follow taxonomy
- Run before `github-initiative-pulse` for consistent reporting

### With CI/CD

```yaml
# .github/workflows/label-audit.yml
name: Label Audit
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - run: |
          # Check for unlabeled issues
          gh issue list --label "" --json number | jq length
```

## See Also

- `/create-issue` - Create issues with proper labels
- `/close-issue` - Analyze and close completed issues
- `minister:github-initiative-pulse` - Initiative status tracking
- GitHub CLI documentation: https://cli.github.com/manual/gh_label
