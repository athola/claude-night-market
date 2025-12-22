---
name: create-command
description: |
  Guided slash command creation with brainstorming and best practices.

  Triggers: new command, create command, slash command, start command,
  build command, add command, write command

  Use when: creating a new slash command from scratch, need guided brainstorming
  for command design, want structured workflow for command development

  DO NOT use when: creating skills - use /create-skill instead.
  DO NOT use when: creating hooks - use /create-hook instead.
  DO NOT use when: modifying existing commands - edit directly.

  Use this command to create any new slash command.
usage: /create-command [command-description] [--skip-brainstorm] [--plugin <name>]
---

# Create Command

Creates new slash commands through a structured workflow: **brainstorm → design → scaffold → validate**. Uses Socratic questioning to refine rough ideas into well-designed commands before generating any files.

## Usage

```bash
# Start with brainstorming (recommended)
/create-command "run all tests and show coverage report"

# Skip brainstorming if design is clear
/create-command test-coverage --skip-brainstorm

# Create in specific plugin
/create-command "analyze git history" --plugin sanctum
```

## What is a Slash Command?

Slash commands are shortcuts that expand into prompts Claude follows. They're stored as `.md` files in `commands/` and referenced in `plugin.json`.

**Simple command example:**
```markdown
---
description: Run tests with coverage
---

Run all tests with pytest and display a coverage report. Focus on files changed in the current branch.
```

**Command with arguments:**
```markdown
---
description: Review specific PR
usage: /review-pr <pr-number> [--focus security|performance|all]
---

Review pull request #$ARGUMENTS using the code review skill. Focus on ${focus:-all} aspects.
```

## Workflow

### Phase 0: Brainstorming (Default)

Before creating any files, refine the command concept through collaborative dialogue.

**Invoke the brainstorming skill:**
```
Use superpowers:brainstorming to refine this command idea before scaffolding.
```

The brainstorming phase will:

1. **Understand the purpose** - One question at a time:
   - What task does this command automate?
   - How often will it be used? (daily, weekly, occasionally)
   - What's the expected output? (action, report, interactive)
   - Who is the target user?

2. **Explore the interface**:
   - What arguments/options are needed?
   - Should this be interactive or fire-and-forget?
   - Are there variants that should be separate commands?
   - What's a good, memorable name?

3. **Design the implementation**:
   - Simple prompt expansion vs. skill invocation?
   - Does it need an agent for complex tasks?
   - What existing skills/commands can it leverage?
   - What tools will Claude need to use?

4. **Validate the design** - Present in sections:
   - Command signature and description
   - Prompt content
   - Integration with skills/agents
   - Example usage

5. **Document the design**:
   - Write to `docs/plans/YYYY-MM-DD-<command-name>-design.md`
   - Commit the design document

**Skip brainstorming** with `--skip-brainstorm` only when:
- You have a written design document already
- The command is a trivial shortcut
- You're copying an existing command pattern

### Phase 1: Gather Requirements

After brainstorming (or with `--skip-brainstorm`), the command prompts for:

1. **Command name** (if not provided)
   - Must be kebab-case
   - Short and memorable (1-3 words)
   - Verb-first preferred (e.g., `run-tests`, `check-deps`)

2. **Description**:
   - One line, starts with verb
   - Shown in `/help` output
   - Maximum 80 characters

3. **Arguments** (optional):
   - Positional arguments: `<required>` or `[optional]`
   - Flags: `--flag` or `--option <value>`
   - Examples: `<file-path>`, `[--verbose]`, `--format <json|yaml>`

4. **Command type**:
   - `prompt`: Simple text expansion
   - `skill`: Invokes a skill with instructions
   - `agent`: Spawns a specialized agent
   - `workflow`: Multi-step process with checkpoints

### Phase 2: Create Command File

**Standard command structure:**
```bash
commands/
└── ${command_name}.md
```

**Command file template:**
```markdown
---
description: ${one_line_description}
usage: /${command_name} ${arguments}
---

# ${Command Title}

${detailed_instructions}

## Arguments

${argument_descriptions}

## What This Command Does

${step_by_step_behavior}

## Examples

${usage_examples}
```

### Phase 3: Command Type Templates

**Type: Prompt (simple expansion)**
```markdown
---
description: Run tests with coverage
---

Run all tests using pytest with coverage enabled. Show a summary of coverage percentages by file.
```

**Type: Skill Invocation**
```markdown
---
description: Review code for security issues
usage: /security-review [path]
---

Use the security-auditor skill to review ${1:-.} for vulnerabilities.

Focus on:
- Input validation
- Authentication/authorization
- Data exposure
- Injection vulnerabilities

Provide findings in severity order.
```

**Type: Agent Dispatch**
```markdown
---
description: Deep code exploration
usage: /explore <question>
---

Spawn an Explore agent to investigate: $ARGUMENTS

The agent should:
1. Search the codebase thoroughly
2. Read relevant files
3. Trace execution paths
4. Report findings with file:line references
```

**Type: Workflow**
```markdown
---
description: Full release preparation
usage: /prepare-release [version]
---

Execute the release preparation workflow:

1. **Validate** - Run all tests and linting
   - If failures: stop and report

2. **Changelog** - Generate changelog from commits
   - Use conventional commits format
   - Group by type (feat, fix, etc.)

3. **Version** - Update version to ${1:-patch bump}
   - Update package.json/pyproject.toml
   - Update CHANGELOG.md

4. **Review** - Show summary for approval
   - List all changes
   - Show files modified
   - Wait for user confirmation

5. **Commit** - Create release commit
   - Message: "chore: release v${version}"
```

### Phase 4: Validation

Validates the command structure:

```bash
# Check command file syntax
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_command.py \
  commands/${command_name}.md

# Verify plugin.json reference
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-plugin.py
```

Output:
```
Validation Results:
  OK Frontmatter valid
  OK Description present
  OK Usage syntax correct
  OK Referenced in plugin.json

Status: READY FOR USE
```

### Phase 5: Next Steps

```
OK Command created: commands/${command_name}.md

Next Steps:

1. UPDATE PLUGIN.JSON
   Add to commands array:
   "./commands/${command_name}.md"

2. TEST THE COMMAND
   - Reload Claude Code (or start new session)
   - Run: /${command_name} --help (if applicable)
   - Test with sample inputs

3. DOCUMENT EXAMPLES
   - Add real-world usage examples
   - Document edge cases
   - Add to README if user-facing
```

## Examples

### Example 1: Simple Prompt Command

```bash
/create-command "check for outdated dependencies"

Creating command: check-deps
Type: Prompt

Created:
  OK commands/check-deps.md

Content preview:
---
description: Check for outdated dependencies
---

Check all project dependencies for available updates.
Show a table of outdated packages with current and latest versions.
```

### Example 2: Skill-Invoking Command

```bash
/create-command "review PR with focus on testing"

Creating command: review-pr-tests
Type: Skill invocation

Brainstorming:
  Q: What aspects of testing should be reviewed?
  A: Test coverage, edge cases, mocking practices

  Q: Should this use an existing skill?
  A: Yes, use pensive:test-review skill

Created:
  OK commands/review-pr-tests.md

Content preview:
---
description: Review PR focusing on test quality
usage: /review-pr-tests <pr-number>
---

Use the test-review skill to analyze PR #$1.

Focus areas:
- Test coverage for changed code
- Edge case handling
- Appropriate use of mocks
- Test naming and organization
```

### Example 3: Workflow Command

```bash
/create-command "full pre-commit checks with auto-fix"

Creating command: pre-commit
Type: Workflow

Created:
  OK commands/pre-commit.md

Content preview:
---
description: Run all pre-commit checks with auto-fix
---

Execute pre-commit workflow:

1. **Format** - Run formatters (prettier, black, etc.)
2. **Lint** - Run linters with auto-fix where possible
3. **Type Check** - Run type checkers
4. **Test** - Run affected tests
5. **Summary** - Show what was fixed/changed
```

## Command Best Practices

### DO:
- Use clear, action-oriented names
- Keep descriptions under 80 characters
- Provide usage examples
- Reference existing skills when applicable
- Use `$ARGUMENTS` or `$1`, `$2` for arguments

### DON'T:
- Create commands that duplicate built-in functionality
- Use overly generic names (`do-thing`, `run`)
- Create commands for one-time tasks
- Put complex logic in the command file (use skills instead)

## Integration with Existing Infrastructure

Commands can leverage:

- **Skills**: `Use the <skill-name> skill to...`
- **Agents**: `Spawn a <agent-type> agent to...`
- **Other commands**: `First run /other-command, then...`
- **Tools**: Direct tool usage via prompt instructions
- **Wrapper Classes**: For complex integrations, implement wrapper classes in `src/` that translate plugin parameters to superpower calls

### Using Wrapper Classes

When a command needs complex parameter translation or validation, create a wrapper class:

```python
# src/my_command_wrapper.py
from .wrapper_base import SuperpowerWrapper
from typing import Dict, Any

class MyCommandWrapper(SuperpowerWrapper):
    """Wrapper for my-command that delegates to target-superpower"""

    def __init__(self):
        super().__init__(
            source_plugin="my-plugin",
            source_command="my-command",
            target_superpower="target-superpower"
        )

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute with validation and parameter translation"""
        # Validate required parameters
        if not params:
            raise ValueError("Parameters cannot be empty")

        # Translate and call superpower
        translated = self.translate_parameters(params)
        # ... execute logic ...
        return result
```

The wrapper handles:
- Parameter validation and type checking
- Translation from plugin naming to superpower naming
- Error handling with clear messages
- Extension of superpower functionality

## Implementation

```bash
# Interactive creation workflow
# Uses brainstorming skill, then scaffolds based on responses

# If --skip-brainstorm:
# Direct scaffolding with prompts for required fields
```

## See Also

- `/create-skill` - Create new skills
- `/create-hook` - Create new hooks
- `/validate-plugin` - Validate plugin structure
- `superpowers:brainstorming` - Design refinement skill
