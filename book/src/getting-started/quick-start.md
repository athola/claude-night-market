# Quick Start Guide

Common workflows and patterns for Claude Night Market plugins.

## Workflow Recipes

### Feature Development with Spec-Kit

Start features with a specification:

```bash
# Create specification from idea
/speckit-specify Add user authentication with OAuth2

# Generate implementation plan
/speckit-plan

# Create ordered tasks
/speckit-tasks

# Execute tasks
/speckit-implement
```

### Code Review with Pensive

detailed code review:

```bash
# Full review with intelligent skill selection
/full-review

# Or specific review types
/architecture-review    # Architecture assessment
/api-review            # API surface evaluation
/bug-review            # Bug hunting
/test-review           # Test quality
/rust-review           # Rust-specific (if applicable)
```

### Context Catchup with Imbue

Get up to speed on changes:

```bash
# Quick catchup on recent changes
/catchup

# Or with sanctum's git-specific variant
/git-catchup
```

### Resource Optimization with Conservation

Monitor and optimize context usage:

```bash
# Analyze context window usage
/optimize-context

# Check skill growth patterns
/analyze-growth
```

## Skill Invocation Patterns

### Basic Skill Usage

```bash
# Standard format
Skill(plugin:skill-name)

# Examples
Skill(sanctum:git-workspace-review)
Skill(imbue:diff-analysis)
Skill(conservation:context-optimization)
```

### Skill Chaining

Some skills depend on others:

```bash
# Pensive depends on imbue and sanctum
Skill(sanctum:git-workspace-review)
Skill(imbue:review-core)
Skill(pensive:architecture-review)
```

### Skill with Dependencies

Check a plugin's README for dependency chains:

```
spec-kit depends on imbue
pensive depends on imbue + sanctum
sanctum depends on imbue (for some skills)
```

## Command Quick Reference

### Git Operations (sanctum)

| Command | Purpose |
|---------|---------|
| `/commit-msg` | Generate commit message |
| `/pr` | Prepare pull request |
| `/fix-pr` | Address PR review comments |
| `/fix-issue` | Fix GitHub issues |
| `/update-docs` | Update documentation |
| `/update-readme` | Modernize README |
| `/update-tests` | Maintain tests |
| `/update-version` | Bump versions |

### Specification (spec-kit)

| Command | Purpose |
|---------|---------|
| `/speckit-specify` | Create specification |
| `/speckit-plan` | Generate plan |
| `/speckit-tasks` | Create tasks |
| `/speckit-implement` | Execute tasks |
| `/speckit-analyze` | Check consistency |
| `/speckit-clarify` | Ask clarifying questions |

### Review (pensive)

| Command | Purpose |
|---------|---------|
| `/full-review` | Unified review |
| `/architecture-review` | Architecture check |
| `/api-review` | API surface review |
| `/bug-review` | Bug hunting |
| `/test-review` | Test quality |

### Analysis (imbue)

| Command | Purpose |
|---------|---------|
| `/catchup` | Quick context recovery |
| `/review` | Structured review |
| `/feature-review` | Feature prioritization |

### Plugin Management (leyline)

| Command | Purpose |
|---------|---------|
| `/reinstall-all-plugins` | Refresh all plugins |
| `/update-all-plugins` | Update all plugins |

## Environment Variables

Some plugins support configuration via environment variables:

### Conservation
```bash
# Skip optimization guidance for fast processing
CONSERVATION_MODE=quick claude

# Full guidance with extended allowance
CONSERVATION_MODE=deep claude
```

### Memory Palace
```bash
# Set embedding provider
MEMORY_PALACE_EMBEDDINGS_PROVIDER=hash  # or local
```

## Tips and Best Practices

### 1. Start with Foundation

Install foundation plugins first:
```bash
/plugin install imbue@claude-night-market
/plugin install sanctum@claude-night-market
```

Then add domain specialists as needed.

### 2. Use TodoWrite Integration

Most skills output TodoWrite items for tracking:
```
git-review:repo-confirmed
git-review:status-overview
pr-prep:quality-gates
```

Monitor these for workflow progress.

### 3. Chain Skills Intentionally

Don't invoke all skills at once. Build understanding incrementally:
```bash
# First: understand state
Skill(sanctum:git-workspace-review)

# Then: perform action
Skill(sanctum:commit-messages)
```

### 4. use Superpowers

If superpowers is installed, commands gain enhanced capabilities:
- `/create-skill` uses brainstorming
- `/test-skill` uses TDD methodology
- `/pr` uses code review patterns

## Next Steps

- Explore individual plugins in [Plugin Overview](../plugins/index.html)
- Deep dive into [Tutorials](../tutorials/index.html)
- Reference all capabilities in [Capabilities Reference](../reference/capabilities-reference.md)
