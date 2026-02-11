---
parent_skill: sanctum:shared
name: output-templates
description: Standardized output formats for sanctum-generated artifacts
category: templates
tags: [templates, output, formatting, conventional-commits]
estimated_tokens: 180
---

# Output Templates for Sanctum

## Conventional Commit Message

### Format
```
<type>(<scope>): <imperative summary>

<body paragraph explaining what and why>

<optional footer with BREAKING CHANGE or issue refs>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code restructuring without behavior change
- `test`: Adding or updating tests
- `chore`: Build, tooling, dependencies
- `style`: Formatting, whitespace
- `perf`: Performance improvement
- `ci`: CI/CD pipeline changes

### Example
```
feat(cli): add status command for workspace overview

Adds a new `status` subcommand that displays current branch,
staged changes, and recent commits. This provides quick context
without running multiple git commands manually.

Closes #123
```

## Pull Request Description

### Template
```markdown
## Summary
<1-2 concise sentences describing the PR>

## Changes
- Bullet 1 (what/why)
- Bullet 2 (what/why)
- Bullet 3 (what/why)

## Testing
- <command/output>
- <manual verification steps>

## Checklist
- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated if needed
- [ ] Breaking changes documented (if applicable)
```

### Example
```markdown
## Summary
Adds workspace status command to CLI for quick repository overview.

## Changes
- Added `status` subcommand to display branch, staged changes, and commits
- Updated README with new command documentation
- Added integration tests for status command output

## Testing
- `make test` - all tests pass
- Verified status output in test repository with staged/unstaged changes
- Confirmed error handling for non-git directories

## Checklist
- [x] Code follows project style guidelines
- [x] Tests pass locally
- [x] Documentation updated if needed
- [ ] Breaking changes documented (if applicable)
```

## Documentation Update Format

### Changelog Entry
```markdown
## [Version] - YYYY-MM-DD

### Added
- Feature description

### Changed
- Change description

### Fixed
- Bug fix description
```

### README Section Update
Use clear headings and grounded language:
```markdown
## New Feature

The `command` now supports `--option` for <specific use case>.

Example:
\`\`\`bash
command --option value
\`\`\`

This enables <concrete outcome>.
```

## Version Update Summary

### Format
```
Updated project version to X.Y.Z

Files updated:
- path/to/config.toml
- path/to/package.json
- CHANGELOG.md
- README.md

Next steps:
- Create git tag: git tag vX.Y.Z
- Push tag: git push origin vX.Y.Z
- Publish release (if applicable)
```

## Best Practices

### Conventional Commits
- Subject line: 50 characters max, imperative mood
- Body: Wrap at 72 characters per line
- Footer: Use for breaking changes and issue references
- Never mention AI tools or assistants

### Pull Requests
- Summary: Focus on "why" not just "what"
- Changes: Group related items, use bullets
- Testing: Show actual commands and results
- Checklist: Update based on project requirements

### Documentation
- Use grounded language (specific commands, file paths)
- Avoid filler phrases ("simply", "just", "easily")
- Include concrete examples
- No emojis or decorative elements
