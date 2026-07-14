---
name: stack-create
description: Initializes a stacked branch set from an ordered plan, one branch per slice with parent-child links. Use when a plan has 2+ sequentially dependent changes.
alwaysApply: false
category: workflow-automation
tags:
- git
- stacked-diffs
- pr
- branches
- planning
tools: []
complexity: medium
model_hint: standard
estimated_tokens: 800
dependencies:
- sanctum:git-workspace-review
- sanctum:do-issue
---

# Stack Create

Initialize a stacked branch set from a multi-step plan.
Each logical slice of the plan becomes one branch targeting
the previous slice's branch as its base.

## When To Use

Use `stack-create` when a plan produces 2 or more ordered
changes where each change depends on the previous one
completing (and merging) before it can land.
For independent changes, use parallel worktrees instead
(see `egregore`).

## When NOT To Use

- A single independent change, which should branch normally instead
- The stack exists and needs publishing (use `sanctum:stack-push`)

## Prerequisites

- Git 2.38+ (`git version | awk '{print $3}'` to check)
- `gh` CLI authenticated
- A written plan with ordered slices (from `do-issue` or
  `attune:blueprint`)
- Clean working tree on the base branch (`git status`)

## Required Progress Tracking

Create `TodoWrite` items before starting:

1. `stack-create:git-version-checked`
2. `stack-create:slices-identified`
3. `stack-create:branches-created`
4. `stack-create:stack-verified`

## Step 1: Verify Git Version (`git-version-checked`)

```bash
git version
```

Confirm the output is `2.38.0` or higher.
If not, the `--update-refs` flag is unavailable.
Warn the user and fall back to manual branch tracking.

Check for optional jj accelerator:

```bash
if command -v jj &>/dev/null && jj root &>/dev/null 2>&1; then
  echo "jj available"
else
  echo "using git --update-refs"
fi
```

## Step 2: Identify Slices (`slices-identified`)

Read the plan and extract ordered slices.
Each slice must satisfy:

- A single logical concern (one PR worth of change)
- A clear dependency on the slice before it (if any)
- A short name suitable for a branch suffix

Example slices for a plan with three parts:

```
Slice 1: add-schema     -- database schema changes
Slice 2: add-api        -- API layer (depends on schema)
Slice 3: add-ui         -- frontend (depends on API)
```

Record the slice list before creating branches.

## Step 3: Create Branches (`branches-created`)

Starting from the base branch (usually `master` or `main`):

```bash
BASE=master
STACK=stack/my-feature

# Slice 1 branches from master
git checkout -b ${STACK}/add-schema ${BASE}

# Slice 2 branches from slice 1
git checkout -b ${STACK}/add-api ${STACK}/add-schema

# Slice 3 branches from slice 2
git checkout -b ${STACK}/add-ui ${STACK}/add-api
```

Convention: `stack/<feature-name>/<slice-name>`

Return to the first slice branch to begin work:

```bash
git checkout ${STACK}/add-schema
```

### jj Accelerator (if available)

```bash
# jj creates an empty commit on each branch automatically
# Use jj new to move to a new change
jj new -m "stack: add-schema" --no-edit
```

## Step 4: Verify Stack (`stack-verified`)

Confirm the branch topology is correct:

```bash
git log --oneline --graph \
  ${BASE}..${STACK}/add-ui
```

Each slice branch should appear as a linear chain above
the base.

If jj is available:

```bash
jj log --revisions \
  "ancestors(${STACK}/add-ui, 10) & !ancestors(${BASE})"
```

## Notes

- Never push branches until at least one commit exists on
  each slice (empty branches produce confusing PRs)
- The slice name in the branch becomes the PR title prefix
  by convention; keep it short and descriptive
- After creating the stack, proceed to `stack-push` to
  open PRs, or work slice-by-slice and push when ready
- If the plan changes, add or remove branches manually and
  re-verify the topology in Step 4

## Exit Criteria

- [ ] All 4 TodoWrite items (`stack-create:git-version-checked`
      through `stack-create:stack-verified`) are created before branch
      creation starts and marked complete in order
- [ ] Git version confirmed ≥ 2.38.0; if not, fallback to manual
      branch tracking is documented and the user is warned
- [ ] All slice branches created with the naming convention
      `stack/<feature-name>/<slice-name>`
- [ ] `git log --oneline --graph <base>..<tip>` shows a linear chain
      with each slice branch appearing in dependency order
- [ ] Working tree returned to the first slice branch after topology
      is verified
