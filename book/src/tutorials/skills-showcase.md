# Your First Session

You've just installed Claude Night Market. This tutorial walks through your first real session: discovering what's available, running your first skill, and seeing how plugins work together.

---

## Scenario

You've followed the [installation guide](../getting-started/installation.md) and have Night Market plugins installed. You open Claude Code in a project and want to explore what you can do.

## Step 1: See What's Available

Start by asking Claude Code what skills are available:

```
What skills do I have installed?
```

Claude reads the installed plugins and lists available skills. You'll see entries like:

```
- sanctum:commit-msg - Draft a conventional commit message
- sanctum:prepare-pr - Complete PR preparation
- pensive:code-reviewer - Code review agent
- imbue:catchup - Quickly understand recent changes
- abstract:validate-plugin - Validate plugin structure
```

Each skill is identified by `plugin:skill-name`. The plugin tells you which domain it belongs to, and the skill name tells you what it does.

## Step 2: Explore a Plugin

Pick a plugin to understand what it offers. For example, sanctum handles git workflows:

```
What commands does the sanctum plugin provide?
```

You'll see commands like:

| Command | What it does |
|---------|-------------|
| `/commit-msg` | Generate a conventional commit message from staged changes |
| `/prepare-pr` | Run quality gates and prepare a PR description |
| `/do-issue` | Implement a GitHub issue end-to-end |
| `/fix-pr` | Address PR review feedback |
| `/git-catchup` | Catch up on repository changes |

Commands (prefixed with `/`) are the main way you interact with skills. They're shorthand: `/commit-msg` invokes the `sanctum:commit-msg` skill behind the scenes.

## Step 3: Run Your First Skill

Let's use `/catchup` to understand the current state of the repository:

```
/catchup
```

This invokes the `imbue:catchup` skill, which:

1. Reads recent git history
2. Analyzes what changed and why
3. Summarizes the current state of the project

The output gives you a summary of recent commits, active branches, what areas of the code changed, and what work is in progress.

## Step 4: Try a Review

If you have uncommitted changes or a branch with work on it, try a code review:

```
/code-review
```

This invokes the `pensive` plugin's review system. It analyzes your changes and reports findings by category: bugs, style issues, architecture concerns, test coverage gaps.

For a more targeted review, you can use specific variants:

```
/bug-review          # Focus on potential bugs
/architecture-review # Focus on design patterns
/test-review         # Focus on test quality
```

## Step 5: Understand How Skills Compose

Skills often work together. For example, preparing a PR typically involves:

1. `/commit-msg` - generate a commit message for staged changes
2. `/prepare-pr` - run quality gates and create the PR description

The PR preparation skill runs workspace analysis, checks for scope drift, and produces a PR description, all by composing underlying skills.

This composition happens on its own. You don't need to orchestrate it. Just invoke the top-level command and the skill handles the rest.

## What You've Learned

- **Skills** are the building blocks. Each does one thing well.
- **Commands** (`/command`) are the main interface for invoking skills.
- **Plugins** group related skills by domain (git, review, analysis, etc.).
- **Composition** lets skills chain together into workflows without manual orchestration.

## Next Steps

| Tutorial | When to read it |
|----------|----------------|
| [Feature Development Lifecycle](feature-lifecycle.md) | You want to build a feature from spec to PR |
| [Code Review and PR Workflow](code-review-pr-workflow.md) | You're ready to review code and submit PRs |
| [Debugging and Issue Resolution](debugging-issues.md) | You need to triage and fix a bug |
| [Memory Palace: Knowledge Management](memory-palace-knowledge.md) | You want to build a persistent knowledge base |

---

**Difficulty:** Beginner
**Prerequisites:** Claude Code installed, Night Market plugins installed
**Duration:** 5 minutes
