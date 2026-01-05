# GitHub Issue Integration

**MANDATORY:** When deferring features due to scope-guard (Worthiness < 1.0 or branch budget exceeded), you MUST create a GitHub issue to preserve context. This is NON-NEGOTIABLE.

## Why This Is Required

1. **Context Preservation** - Deferred items lose context over time
2. **Accountability** - Issues create audit trail of decisions
3. **Discoverability** - Future work can find and prioritize deferred items
4. **No Lost Work** - Every idea is captured, nothing falls through cracks

## Deferral Process

### Step 1: Create GitHub Issue (MANDATORY)

When deferring an item, you MUST run this command:

```bash
gh issue create \
  --title "[Deferred] <Brief feature description>" \
  --body "$(cat <<'EOF'
## Deferred by scope-guard

**Worthiness Score:** X.XX (threshold: 1.0)
**Branch:** <current-branch-name>
**Date:** <YYYY-MM-DD>
**Reason:** <Why score was low OR branch budget exceeded>

### Feature Description

<Full description of the proposed feature>

### Scoring Breakdown

| Factor | Score | Rationale |
|--------|-------|-----------|
| Business Value | X | <reason> |
| Time Criticality | X | <reason> |
| Risk Reduction | X | <reason> |
| Complexity | X | <reason> |
| Token Cost | X | <reason> |
| Scope Drift | X | <reason> |

**Formula:** (X + X + X) / (X + X + X) = X.XX

### Context

<Any additional context, alternatives considered, or notes for future implementation>

### When to Revisit

- [ ] When branch budget frees up
- [ ] When related work is scheduled
- [ ] During next planning cycle
EOF
)" \
  --label "scope-guard-deferred"
```

### Step 2: Record Issue Number

After creating the issue, note the issue number (e.g., #123) for cross-referencing.

### Step 3: Update queue.md (Optional - Issue is primary record)

If maintaining `docs/backlog/queue.md`, add with issue reference:

```markdown
| Rank | Item | Worthiness | Added | Branch | Category | Issue |
|------|------|------------|-------|--------|----------|-------|
| X | Feature name | 0.85 | 2026-01-03 | branch-name | idea | #123 |
```

## Non-GitHub Repositories

If `gh` CLI is unavailable or repository is not on GitHub:

1. **Check availability:**
   ```bash
   command -v gh && gh auth status
   ```

2. **If unavailable, document in queue.md with prominent notice:**
   ```markdown
   ## DEFERRED ITEMS (No GitHub - Manual Tracking Required)

   | Item | Worthiness | Added | Context |
   |------|------------|-------|---------|
   | Feature X | 0.85 | 2026-01-03 | Full context here since no issue... |
   ```

3. **Create issue when GitHub becomes available** - This is technical debt.

## TodoWrite Integration

The deferral workflow requires this todo item:

- `scope-guard:github-issue-created` - Mark complete ONLY after issue URL is confirmed

This todo is MANDATORY and blocks marking `scope-guard:decision-documented` as complete.

## Labels

Use consistent labels for filtering:

| Label | Purpose |
|-------|---------|
| `scope-guard-deferred` | All scope-guard deferrals (required) |
| `priority/low` | Low worthiness score (< 0.8) |
| `priority/medium` | Medium worthiness (0.8 - 1.0) |
| `enhancement` | New features |
| `refactor` | Code improvements |
| `architecture` | Structural changes |

## Validation

After creating the issue, verify:

```bash
# Confirm issue exists
gh issue view <issue-number>

# List all deferred items
gh issue list --label scope-guard-deferred
```

## Failure Handling

If issue creation fails:

1. **Retry once** with simplified body
2. **If still fails**, document in queue.md with full context
3. **Create issue manually** as soon as possible
4. **Never proceed** without documenting the deferral somewhere persistent
