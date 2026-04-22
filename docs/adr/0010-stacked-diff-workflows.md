# ADR-0010: Stacked Diff Workflows for Sanctum and Egregore

**Date**: 2026-04-20
**Status**: Accepted
**Deciders**: Claude Night Market maintainers

## Context

Sanctum's current workflows assume linear branches.
`/prepare-pr`, `/commit-msg`, and `/acp` each operate on
a single feature branch targeting `master`.
Egregore's parallel worktrees are independent with no
dependency chains.
Neither plugin models ordered PR stacks, cascading rebases
after a base PR merges, or dependent PR submission sequences.

As do-issue parallelism grows more coarse and plans routinely
produce 3-5 interdependent changes, agents increasingly need
to submit changes as a stack of dependent PRs rather than
one monolithic PR or a collection of unrelated PRs.

### Requirements

- Submit a series of dependent changes as ordered PRs with
  correct base-branch targeting
- Rebase the entire stack automatically when a base PR
  merges or its base changes
- Keep the workflow zero-dependency by default (no third-party
  tooling required)
- Detect and use optional accelerators (jj) when available
- Remain compatible with the existing sanctum/egregore
  skill and hook architecture

### Current Gaps

| Gap | Affected Skill / Command |
|-----|--------------------------|
| Linear branch assumption | `/prepare-pr`, `/commit-msg`, `/acp` |
| No dependency chains in worktrees | egregore parallel dispatch |
| No cascading rebase support | all PR workflows |
| Flat PR review (no stack context) | `/pr-review` |
| Flat PR fix (no stack context) | `/fix-pr` |
| Coarse do-issue parallelism | `do-issue` task planning |

### Tools Evaluated

| Tool | Model | Dependency | Status |
|------|-------|------------|--------|
| git --update-refs | Built-in (Git 2.38+) | Zero | GA |
| gh pr create --base | gh CLI | Already required | GA |
| jj (Jujutsu) | Local install, Git backend | Optional | Stable |
| gh-stack (GitHub) | GitHub native | GitHub account | Private preview |
| Graphite | Commercial SaaS | Vendor account | GA |
| ghstack (Meta) | Python CLI | pip install | GA |
| spr / stack-pr (Modular) | Python CLI | pip install | GA |

**git --update-refs** (Git 2.38+) lets a single
`git rebase --update-refs` call rewrite every branch
in the stack atomically.
Combined with `gh pr create --base <parent-branch>`,
this covers the full stacked-PR submission loop with tools
already present on any dev machine.

**jj (Jujutsu)** is a Git-compatible VCS from Google.
Its working copy is always a commit, descendants rebase
automatically, and `jj split` / `jj squash` / `jj diffedit`
reshape stacks interactively.
It requires a local install but imposes no team-wide
requirement: a developer with jj can operate alongside
teammates using standard git.

**gh-stack** (GitHub private preview) offers a stack map
UI, cascading rebase after merge, and simultaneous multi-PR
merge.
It is not GA; adoption is premature.

**Graphite** is the most feature-complete commercial
offering but adds a vendor dependency.

**ghstack** and **spr/stack-pr** each commit a Python CLI
installation requirement for no benefit over the zero-dep
foundation.

## Decision

Adopt **git --update-refs + gh pr create --base** as the
zero-dependency foundation for stacked diff workflows.
Layer **jj** as an optional accelerator when available.
Defer gh-stack adoption until GA.

### Foundation (Zero Dependency)

Every stacked-diff skill uses this sequence:

1. Create one branch per logical slice:
   `git checkout -b stack/<name>/<slice>`.
2. Commit changes on each slice branch.
3. Run `git rebase --update-refs <base>` to update all
   branch pointers after any rebase.
4. Open PRs with explicit base targeting:
   `gh pr create --base <parent-branch>`.
5. After a PR merges, run `git rebase --update-refs master`
   on the next branch to cascade the update down the stack.

### Optional Accelerator (jj)

When `jj --version` succeeds in the working directory:

- Use `jj rebase -d <dest>` instead of
  `git rebase --update-refs` for richer conflict UI.
- Use `jj split` to split a commit into two stack slices
  without interactive rebase.
- Use `jj describe` to amend commit messages without
  detaching HEAD.

Detection is runtime, non-blocking:

```bash
if command -v jj &>/dev/null && jj root &>/dev/null; then
  echo "jj available -- using jj accelerator"
else
  echo "jj not found -- using git --update-refs"
fi
```

### Deferred

- gh-stack: revisit when GA
- Graphite: not adopted (vendor dependency)
- ghstack / spr: not adopted (Python CLI dependency)

### Implementation Phases

| Phase | Scope |
|-------|-------|
| 1 | `stack-create` skill: initialize a stack from a multi-step plan |
| 2 | `stack-push` skill: push all branches, open/update dependent PRs |
| 3 | `stack-rebase` skill: cascading rebase after base PR merges |
| 4 | Update `do-issue` task-planning module with stack awareness |
| 5 | `stack-mode` skill + `--stack` flag for `/pr-review` and `/fix-pr`: review and fix every PR in a stack (rooted at a common base branch) in one invocation |
| 6 | Add gh-stack layer when GA |

**Phase 5 contract** (`stack-mode` skill):

- Shared detection, iteration, and summary contract used
  by both commands so behavior stays symmetric.
- Three detection strategies: branch-name convention,
  `## Stack` summary comment, and base-chain walk.
- Iterates base-to-tip; per-PR gates (thread resolution,
  issue tracking) are preserved unchanged.
- Posts one consolidated summary on the root PR in
  addition to the per-PR outputs.
- Halts on first per-PR failure and leaves descendants
  untouched because their context may have shifted.

## Consequences

### Positive

- Zero new tool dependencies: git 2.38+ ships on macOS
  12.3+ and all major Linux distros since 2023
- gh CLI is already required by sanctum, so
  `gh pr create --base` costs nothing to adopt
- jj opt-in means early adopters get acceleration without
  forcing team-wide migration
- Skills are documentation-only markdown; they can be
  updated independently of code changes
- gh-stack integration is additive when it reaches GA

### Negative

- `git --update-refs` is manual: the developer must
  remember to pass the flag; a forgotten rebase leaves
  branches inconsistent
- jj detection adds a shell exec on every stack operation
  (negligible, but present)
- gh-stack deferral means no automatic post-merge cascade
  UI until it is GA

### Risks

- Git 2.38 may not be present on all CI runners
  (mitigated: skills check `git version` and warn)
- jj's Git backend compatibility is high but not 100%:
  shallow clones and some submodule configs can fail
  (mitigated: jj is optional, git is the fallback)

## Related

- ADR-0001: Plugin Dependency Isolation
- Issue #405: Investigate stacked diff workflows
- `plugins/sanctum/skills/stack-create/SKILL.md`
- `plugins/sanctum/skills/stack-mode/SKILL.md`
- `plugins/sanctum/skills/stack-push/SKILL.md`
- `plugins/sanctum/skills/stack-rebase/SKILL.md`
- `plugins/sanctum/commands/pr-review.md` (`--stack`)
- `plugins/sanctum/commands/fix-pr.md` (`--stack`)
- [git --update-refs docs](https://git-scm.com/docs/git-rebase#Documentation/git-rebase.txt---update-refs)
- [jj book](https://martinvonz.github.io/jj/latest/)
- [gh-stack announcement](https://github.blog/changelog/2024-04-25-github-stacks-public-beta/)
