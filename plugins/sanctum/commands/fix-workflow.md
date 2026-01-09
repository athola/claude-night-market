---
name: fix-workflow
description: |
  Retrospective analysis and improvement of recent workflow components.

  Triggers: fix workflow, workflow improvement, retrospective, session analysis
  Use when: workflow execution felt inefficient or needs optimization
usage: /fix-workflow [--scope sanctum|repo] [--dry-run] [--focus skills|agents|commands|hooks|all]
---

# Fix Workflow

Run a lightweight retrospective on the **most recent command or session slice** visible in the current context window, then implement targeted improvements to the workflow components involved (skills, agents, commands, hooks).

## Usage

```text
/fix-workflow [--scope sanctum|repo] [--dry-run] [--focus skills|agents|commands|hooks|all]
```

- `--scope sanctum|repo`: Default `sanctum`. If `repo`, improvements may touch non-plugin code and project docs/tests as needed.
- `--dry-run`: Produce an improvement plan without making changes.
- `--focus`: Default `all`. Limit to a component type to keep the change set small.

## Workflow

1. Capture the target slice and key evidence:
   - Load workflow-improvement skill: `Skill(sanctum:workflow-improvement)` or read `plugins/sanctum/skills/workflow-improvement/SKILL.md`

2. Recreate the workflow and surface inefficiencies:
   - Use `workflow-recreate-agent` to restate the steps, identify friction, and list involved components.

3. Analyze improvement options:
   - Use `workflow-improvement-analysis-agent` to generate candidate improvements with trade-offs and expected impact.

4. Plan collaboratively (converge on a small, high-use patch):
   - Use `workflow-improvement-planner-agent` to choose the best approach, define acceptance criteria, and assign work.

5. Implement the improvements:
   - Use `workflow-improvement-implementer-agent` to apply code/doc changes, keeping diffs focused and reversible.

6. Validate the improvement is substantive:
   - Use `workflow-improvement-validator-agent` to run targeted tests/validators and re-run a minimal reproduction of the workflow.

## Output

Conclude with:
- The reconstructed workflow slice (1 screen max)
- The improvements applied (per file)
- Validation evidence (commands run + results)
- Follow-ups (if anything deferred)
