---
description: Update pre-commit hooks and CI/CD workflows based on recent project changes
usage: /update-ci [--since <ref>] [--scope hooks|workflows|all] [--dry-run]
---

# Update CI/CD Configuration

Reconcile pre-commit hooks and GitHub Actions workflows with recent project changes. This command is designed for intermittent use — it inspects the git log to determine what changed since the last run.

## Arguments

- `--since <ref>` - Git ref or time range to inspect (default: last tag, or `30 days ago` if no tags)
- `--scope hooks|workflows|makefiles|all` - Limit to pre-commit hooks, GitHub workflows, Makefile CI targets, or all (default: `all`)
- `--dry-run` - Show proposed changes without applying them

## What This Command Does

### Phase 1: Determine Change Window

Identify what changed since the last CI update:

```bash
# Find the last CI-related commit as baseline
git log --oneline --all --grep="ci\|pre-commit\|workflow\|hook" -1 --format="%H %ar"

# If --since not provided, use last tag or 30 days
git describe --tags --abbrev=0 2>/dev/null || echo "no tags, using 30 days"

# Gather recent changes within the window
git log --oneline --since="${since}" --stat
```

### Phase 2: Analyze Impact on CI

Review changes and identify what needs CI/CD updates:

| Change Type | CI Impact |
|------------|-----------|
| New/renamed Python scripts | Pre-commit hook paths, lint targets |
| New plugins or skills | Workflow test matrix, validation targets |
| Dependency changes (pyproject.toml) | Workflow install steps, cached deps |
| New test files | Workflow test commands, coverage config |
| Makefile changes | Workflow make targets |
| New workflow-triggering paths | Workflow `paths:` filters |
| Renamed files (kebab → snake) | Pre-commit hook configs, script refs |

Read each CI-related file and cross-reference with the change log:

```bash
# Files to inspect
ls .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null
ls .pre-commit-config.yaml 2>/dev/null
ls .claude/hooks/ 2>/dev/null
cat Makefile | head -50  # Check make targets referenced by CI
```

### Phase 3: Update Pre-Commit Hooks (if --scope includes hooks)

For each hook configuration found:

1. **Verify hook targets exist** — Check that all referenced scripts/files still exist at their configured paths
2. **Add hooks for new patterns** — If new lintable file types or directories were added, suggest hook additions
3. **Update file patterns** — If files were renamed (e.g., kebab-case to snake_case), update hook path globs
4. **Validate hook tool versions** — Check if pinned tool versions have newer releases

### Phase 3.5: Reconcile Makefile CI Targets (if --scope includes makefiles)

Verify that Makefile targets referenced by workflows and hooks actually exist, and that new targets are wired up:

1. **Extract workflow references** — Parse `.github/workflows/*.yml` for `make <target>` and `$(MAKE) <target>` invocations
2. **Extract hook references** — Parse pre-commit configs and Claude hooks for `make` calls
3. **Diff against actual targets** — Run `make -qp | grep '^[a-zA-Z]' | cut -d: -f1` to list real targets
4. **Flag orphaned references** — Workflow/hook calls a target that no longer exists (renamed or removed)
5. **Flag unwired targets** — New Makefile targets (added in change window) that look CI-relevant (`test-*`, `lint-*`, `check-*`, `validate-*`) but aren't referenced by any workflow
6. **Check per-plugin Makefiles** — If plugins have their own Makefiles, verify those targets are included in the root workflow matrix or composite targets

```bash
# List all make targets in root Makefile
make -qp 2>/dev/null | awk -F: '/^[a-zA-Z]/ && !/Makefile/ {print $1}' | sort

# Find make invocations in workflows
grep -rn 'make ' .github/workflows/ 2>/dev/null

# Find new Makefile targets in change window
git diff "${since}"..HEAD -- '**/Makefile' | grep '^+[a-zA-Z].*:' | sed 's/^+//'
```

### Phase 4: Update GitHub Workflows (if --scope includes workflows)

For each workflow in `.github/workflows/`:

1. **Verify referenced paths** — Ensure all paths in `paths:`, `paths-ignore:`, and script steps exist
2. **Update test commands** — If Makefile targets changed, update workflow steps
3. **Check action versions** — Flag outdated `uses:` action versions (e.g., `actions/checkout@v3` → `@v4`)
4. **Sync trigger branches** — Verify branch names in `on.push.branches` match actual branches
5. **Update matrix strategies** — If new plugins were added, update any matrix-based test jobs
6. **Validate secrets/permissions** — Ensure `permissions:` blocks match what steps actually need

### Phase 5: Update Claude Hooks (if present)

If `.claude/hooks/` exists:

1. **Verify hook scripts exist** at referenced paths
2. **Update any hardcoded paths** that were renamed
3. **Check hook configuration** in `.claude/settings.json` matches available hooks

### Phase 6: Review and Apply

Present a summary table of all proposed changes:

```markdown
## Proposed CI/CD Updates

| File | Change | Reason |
|------|--------|--------|
| .github/workflows/security.yml | Update checkout to v4 | Outdated action |
| .pre-commit-config.yaml | Fix script path | File renamed in abc123 |

### Files Modified in Change Window
(list of key changes that drove these updates)
```

If `--dry-run`: stop here and show the summary.
Otherwise: apply changes and show the diff.

## Examples

```bash
# Standard update — auto-detect change window
/update-ci

# Only update GitHub workflows
/update-ci --scope workflows

# Check what would change since a specific commit
/update-ci --since abc1234 --dry-run

# Update based on last 2 weeks of changes
/update-ci --since "14 days ago"

# Only update pre-commit hooks
/update-ci --scope hooks
```

## See Also

- `/fix-workflow` - Retrospective analysis of workflow efficiency
- `/update-docs` - Update project documentation
- `/update-dependencies` - Update project dependencies
