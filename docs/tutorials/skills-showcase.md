# Skills Showcase - Claude Code Development Workflows

**Demonstration of skill discovery, validation, and usage patterns.**

![Skills Showcase Demo](../../assets/gifs/skills-showcase.gif)

*Discover 105+ skills, understand their structure, and compose them into workflows.*

---

## What You'll Learn

- Discover skills across all plugins
- Examine skill structure and metadata
- Compose skills into workflows
- Analyze real-world usage patterns

---

## Tutorial Steps

### 1. Discover Skills in the Project

List all available skills across plugins:

```bash
ls plugins/abstract/skills/
```

The claude-night-market contains 100+ skills across 14 plugins. Skills are the building blocks of workflows - reusable, composable units that Claude Code can invoke.

### 2. Count Total Skills

Get a quick count of total skills:

```bash
find plugins -name 'SKILL.md' -type f | wc -l
```

Each plugin organizes its skills in a `skills/` directory with a `SKILL.md` file defining behavior, dependencies, and usage.

### 3. Examine Skill Structure

Look at a skill definition:

```bash
head -30 plugins/abstract/skills/plugin-validator/SKILL.md
```

Skills follow a structured format with YAML frontmatter defining metadata and markdown content defining the workflow.

### 4. Use Skills in Claude Code

In Claude Code, invoke skills with:

```
Skill(abstract:plugin-validator, plugin_name='sanctum')
```

This validates:
- Plugin structure and directories
- SKILL.md frontmatter and formatting
- Command definitions
- Dependencies between skills

### 5. Real Workflow Example

The `sanctum:git-workspace-review` skill analyzes repository state:

1. Run `git status` to see uncommitted changes
2. Run `git log` to see recent commit history
3. Analyze changed files and their impact
4. Provide context for the current development session

### 6. Skills Compose into Workflows

Complex workflows chain multiple skills:

**PR Preparation Workflow:**
1. `Skill(sanctum:git-workspace-review)` - Understand changes
2. `Skill(imbue:scope-guard)` - Check scope drift
3. `Skill(sanctum:commit-messages)` - Generate commit message
4. `Skill(sanctum:pr-prep)` - Prepare PR description

---

## Key Takeaways

- 105 skills across 14 plugins
- Structured workflows for git, review, specs, and testing
- Composable and reusable project components
- Self-documenting with clear dependencies
- Validated structure for quality

---

## Next Steps

- Explore [Plugin Development Guide](../plugin-development-guide.md) for creating your own plugins
- Review [Skill Integration Guide](../skill-integration-guide.md) for skill authoring patterns
- Check [Optimization Patterns](../optimization-patterns.md) for workflow best practices
- See [API Overview](../api-overview.md) for full API reference

---

**Duration:** ~90 seconds
**Difficulty:** Beginner
**Tags:** skills, workflows, claude-code, development, getting-started
