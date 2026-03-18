---
area_name: plugins/sanctum
ownership_globs:
  - "plugins/sanctum/**"
tags:
  - git-workflows
  - commit-messages
  - pull-requests
  - documentation
---

# plugins/sanctum Area Guide

Git workflows and documentation management -- handles
commits, PRs, docs, and issue processing.

## Patterns

- Commit agent generates conventional commit messages
  with semantic versioning awareness
- PR agent runs quality gates before creating PRs
- Do-issue agent processes GitHub issues through a
  full implementation pipeline
- Doc updates and consolidation keep documentation
  current with code changes
- Workflow improvement agents analyze and optimize
  command/session workflows

## Pitfalls

- Never use git commit --no-verify or --force push
  without explicit user request
- Commit messages must not contain AI attribution
  (no Co-Authored-By for Claude)
- PR descriptions use HEREDOC format for proper
  markdown rendering
- The do-issue parallel execution module has specific
  agent dispatch patterns

## Testing

```bash
cd plugins/sanctum && uv run python -m pytest tests/ -v --tb=short
```

## Review Focus

- Git safety (no destructive operations without consent)
- Conventional commit format compliance
- PR quality gate completeness
- Documentation accuracy vs code state
