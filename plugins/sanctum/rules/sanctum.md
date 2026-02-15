---
description: Git workflow and documentation standards
globs: ["**/*.md", ".git/**", "CHANGELOG.md", "README.md"]
---

# Sanctum Conventions

## Commit Messages

- Use conventional commits: `type(scope): description`
- Focus on "why" not "what"
- No AI attribution (no Co-Authored-By for AI)
- No emojis in commit messages
- Use HEREDOC for multi-line messages (always use single-quoted `<<'EOF'` delimiters — 2.1.38+ hardens delimiter parsing against command smuggling)

## Git Safety

Never use without explicit user request:
- `git commit --no-verify`
- `git push --force`
- `git reset --hard`
- `git rebase -i` (interactive)

## Documentation Standards

- Progressive disclosure: essential info first
- Audience-appropriate depth
- Link to detailed docs instead of duplicating
- Markdown for all documentation (not HTML)

## Branch Workflow

| Threshold | Metric |
|-----------|--------|
| 1000/1500/2000 | Lines changed |
| 15/25/30 | Commit count |
| 3/7/7+ | Days active |
