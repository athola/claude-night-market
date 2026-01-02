# Your First Plugin: sanctum

This hands-on tutorial walks you through using the **sanctum** plugin for git and workspace operations.

## What You'll Build

By the end of this tutorial, you'll:
- Review your git workspace state
- Generate a conventional commit message
- Prepare a pull request description

## Prerequisites

- sanctum plugin installed: `/plugin install sanctum@claude-night-market`
- A git repository with some uncommitted changes

## Part 1: Workspace Review

Before any git operation, understand your current state.

### Invoke the Skill

```bash
Skill(sanctum:git-workspace-review)
```

This skill runs a preflight checklist:
- Current branch and remote tracking
- Staged vs unstaged changes
- Recent commit history
- Untracked files

### What to Expect

Claude will analyze your repository and report:

```
Repository: my-project
Branch: feature/add-login
Tracking: origin/feature/add-login (up to date)

Staged Changes:
  M src/auth/login.ts
  A src/auth/types.ts

Unstaged Changes:
  M README.md

Untracked:
  src/auth/tests/login.test.ts
```

<div class="achievement-unlock" data-achievement="first-skill">
Achievement Unlocked: Skill Apprentice
</div>

## Part 2: Commit Message Generation

Now generate a conventional commit message for your staged changes.

### Using the Command

```bash
/commit-msg
```

Or invoke the skills directly:

```bash
Skill(sanctum:git-workspace-review)
Skill(sanctum:commit-messages)
```

### Understanding the Output

Claude analyzes staged changes and generates:

```
feat(auth): add login form with validation

- Implement LoginForm component with email/password fields
- Add form validation using zod schema
- Create auth types for login request/response

Closes #42
```

The commit follows [Conventional Commits](https://www.conventionalcommits.org/) format:
- **Type**: feat, fix, docs, style, refactor, test, chore
- **Scope**: Optional context (auth, api, ui)
- **Description**: Imperative mood, present tense
- **Body**: Bullet points explaining what changed
- **Footer**: Issue references

## Part 3: PR Preparation

Finally, prepare a pull request description.

### Using the Command

```bash
/pr
```

This runs the full PR preparation workflow:
1. Workspace review
2. Quality gates check
3. Change summarization
4. PR description generation

### Quality Gates

Before generating the PR, Claude checks:

```
Quality Gates:
  [x] Code compiles
  [x] Tests pass
  [x] Linting clean
  [x] No console.log statements
  [x] Documentation updated
```

### Generated PR Description

```markdown
## Summary

Add user authentication with login form validation.

## Changes

- **New Feature**: Login form component with email/password validation
- **Types**: Auth request/response type definitions
- **Tests**: Unit tests for login validation logic

## Testing

- [x] Manual testing of form submission
- [x] Unit tests pass (15 new tests)
- [x] Integration tests pass

## Screenshots

[Add screenshots if UI changes]

## Checklist

- [x] Tests added
- [x] Documentation updated
- [x] No breaking changes
```

<div class="achievement-unlock" data-achievement="first-pr">
Achievement Unlocked: PR Pioneer
</div>

## Workflow Chaining

These skills work together. The recommended flow:

```
git-workspace-review (foundation)
├── commit-messages (depends on workspace state)
├── pr-prep (depends on workspace state)
├── doc-updates (depends on workspace state)
└── version-updates (depends on workspace state)
```

Always run `git-workspace-review` first to establish context.

## Common Patterns

### Pre-Commit Workflow

```bash
# Stage your changes
git add -p

# Review and commit
Skill(sanctum:git-workspace-review)
Skill(sanctum:commit-messages)

# Apply the message
git commit -m "<generated message>"
```

### Pre-PR Workflow

```bash
# Run quality checks
make fmt && make lint && make test

# Prepare PR
/pr

# Create on GitHub
gh pr create --title "<title>" --body "<generated body>"
```

## Next Steps

- Read the [Quick Start Guide](quick-start.md) for more workflow patterns
- Explore other plugins in the [Plugin Overview](../plugins/index.html)
- Check the [Capabilities Reference](../reference/capabilities-reference.md) for all available skills

## Achievements Earned

- Skill Apprentice: Used your first skill
- PR Pioneer: Prepared your first PR

<div class="progress-tracker" data-section="getting-started">
Section Progress: 3/3 complete
</div>
