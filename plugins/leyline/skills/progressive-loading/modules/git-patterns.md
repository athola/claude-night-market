# Git Patterns

This module covers progressive-loading for skills that work with
git repositories: workspace inspection, branch operations, commit
analysis, and history rewrites. The driving question is which
git tooling modules to load based on the operation, not on the
file extension.

## When This Module Applies

Load this module when the task involves:

- Inspecting working-tree state before a commit or PR.
- Branch operations: create, rebase, switch, delete.
- Commit-message generation or conventional-commit checks.
- Reading history with `git log`, `git blame`, or `git bisect`.

For catchup-style summaries of recent work, load
`git-catchup-patterns.md`. This module covers general git
operations beyond summarization.

## Three Operation Buckets

Git operations split into three buckets that map to separate
modules. Mixing them in one mega-module wastes tokens.

| Bucket | Examples | Module |
|--------|----------|--------|
| Inspection | `status`, `diff`, `log`, `blame` | `git-inspection.md` |
| Mutation | `commit`, `rebase`, `merge`, `reset` | `git-mutation.md` |
| Plumbing | `cat-file`, `rev-parse`, `update-ref` | `git-plumbing.md` |

Plumbing commands are rarely needed. Defer their module unless
the task explicitly calls for low-level git inspection.

## Always Load: Workspace Sanity Check

A small inspection module is worth keeping always-loaded so the
skill can verify state before any mutation.

```bash
# Are we in a git repo?
git rev-parse --is-inside-work-tree

# Current branch and tracking status
git status -sb | head -1

# Upstream tracking
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null \
  || echo "no upstream"

# Are there local changes?
git diff --quiet || echo "modified"
git diff --cached --quiet || echo "staged"
```

The `--quiet` flag returns nonzero on differences without
producing output. This is the cheapest way to gate later work on
a clean tree.

## Mutation Module: Load Only When Needed

The mutation module covers operations that change repository
state: commits, rebases, branch deletions. Loading it carries
the risk that the model uses dangerous commands without intent.
Gate it on explicit user request.

```bash
# Safe commit pattern: stage explicit files, never -A
git add path/to/file.py path/to/test.py
git commit -m "fix: explicit fix description"

# Branch creation from current HEAD
git switch -c feat/short-name

# Rebase onto remote main, preserving local commits
git fetch origin main
git rebase origin/main
```

The mutation module documents safe defaults. The hub should
declare in its frontmatter that this module is `mutation: true`
so callers know loading it permits destructive commands.

## Inspection Patterns the Module Should Cover

The inspection module documents the read-only patterns most
analysis skills need. Examples:

```bash
# What changed in the last commit?
git show --stat HEAD

# Who last touched this line?
git blame -L 42,42 path/to/file.py

# Find the commit that introduced a string
git log -S 'function_name' -- path/to/file.py

# Show ancestors common to two branches
git merge-base feature-branch main
```

`git log -S` (the "pickaxe") finds commits that added or
removed an exact string. `git log -G` accepts a regex but is
slower. Use the pickaxe by default.

## Pitfalls

1. **Loading mutation by default**: Read-only analysis does not
   need destructive commands available. Keep mutation behind an
   explicit gate.
2. **Skipping the sanity check**: Running `git rebase` in a
   non-git directory or on the wrong branch is a recoverable
   but expensive mistake. Always verify the workspace first.
3. **Using `-A` or `.` for staging**: `git add -A` and `git add
   .` capture untracked files that may include secrets or
   build artifacts. Stage explicit paths.
4. **Treating force-push as safe**: `git push --force` rewrites
   shared history. The mutation module should document
   `--force-with-lease` as the default, not `--force`.
5. **Reading raw plumbing output as content**: `git cat-file`
   returns blob content with no path context. Load the plumbing
   module only when the task is debugging git internals, not
   reading source.

## Cross-Reference

See `git-catchup-patterns.md` for summarization workflows and
the parent `SKILL.md` for how git modules plug into the
hub-and-spoke pattern.
