---
name: speckit-taskstoissues
description: Convert tasks.md entries into GitHub Issues
usage: /speckit-taskstoissues [feature-dir]
---

# Speckit Tasks to Issues

Before proceeding, load the `speckit-orchestrator` skill
for workflow coordination.

## When To Use

Use this command when you need to:

- Push task breakdown into GitHub Issues for tracking
- Create a project board from spec-kit tasks
- Enable team collaboration on task assignments

## When NOT To Use

- Tasks are not yet generated (run /speckit-tasks first)
- Repository is not hosted on GitHub
- Working solo without need for issue tracking

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding
(if not empty).

## Outline

1. **Setup**: Run
   `.specify/scripts/bash/check-prerequisites.sh --json
   --require-tasks --include-tasks` from repo root.
   Parse FEATURE_DIR and tasks file path.
   For single quotes in args like "I'm Groot", use
   escape syntax: e.g `'I'\''m Groot'` (or double-quote
   if possible: `"I'm Groot"`).

2. **Detect git remote**: Run `git remote get-url origin`
   and verify it points to a GitHub repository
   (github.com in URL). If not GitHub, abort with message
   suggesting manual issue creation.

3. **Parse tasks.md**: Extract all tasks with:
   - Task ID (T001, T002, etc.)
   - Priority markers ([P] for parallel)
   - Story labels ([US1], [US2], etc.)
   - Risk classification ([R:GREEN], [R:YELLOW], etc.)
   - Description and file paths
   - Phase grouping

4. **Generate issue content**: For each task, create
   an issue with:
   - **Title**: `[TaskID] Description` (e.g.,
     "[T001] Create project structure")
   - **Body**: Include phase, dependencies, file paths,
     and acceptance criteria from the task
   - **Labels**: Map from task metadata:
     - Story labels -> `user-story:US1` etc.
     - Risk classification -> `risk:green` etc.
     - Phase -> `phase:setup`, `phase:foundational` etc.
     - Parallel marker -> `parallelizable`

5. **Create issues**: Use `gh issue create` CLI to create
   each issue. Present a preview table first:

   | Task ID | Title | Labels | Create? |
   |---------|-------|--------|---------|
   | T001 | Create project structure | phase:setup | Y |
   | T002 | [P] Setup database | phase:setup, parallel | Y |

   Ask user to confirm before creating issues.

6. **Report**: Output created issue URLs and suggest
   creating a GitHub Project board for tracking.

## Rules

- Never create issues without user confirmation
- Preserve task ordering in issue creation
- Include cross-references between dependent tasks
- Add a "spec-kit" label to all created issues
- If labels don't exist yet, create them automatically
