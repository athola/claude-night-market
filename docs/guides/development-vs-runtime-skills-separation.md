# Separating Development and Application Skills

Using Claude Code to build an AI agent can cause confusion if the assistant mistakes development tools for application features. This guide shows how to separate development skills from runtime application capabilities.

## The Problem

Development and runtime skills collide when they share the same directory:

```bash
# Problematic Structure
.claude/skills/
├── create-todo.md          # Runtime: Agent capability
├── debug-python.md         # Development: Assistance
```

If you ask Claude Code to "Build the to-do list page," it may incorrectly invoke the `create-todo.md` runtime skill instead of assisting with development. This happens because two different contexts share a single discovery mechanism.

---

## Architectural Solutions

| Pattern | Separation Mechanism | Use Case |
|---------|---------------------|----------|
| **Physical Directory** | Different folders for dev vs runtime | Foundation for all projects |
| **Scoped Loading** | Hooks control skill availability | Complex or multi-mode projects |
| **Context Forking** | Isolated context windows | Testing runtime skills without pollution |
| **Namespace Prefixing** | Explicit naming: `dev:*` vs `app:*` | Multi-agent systems |

---

## Physical Directory Separation

Keep development skills in `.claude/` and runtime skills in `src/agent/prompts/` (or your application's prompt directory).

### Directory Structure

```bash
my-todo-app/
├── .claude/                          # Development-time (Claude Code)
│   ├── skills/
│   │   ├── dev-debug-python.md       # Helps YOU debug
│   └── hooks/
│       └── hooks.json                # Claude Code automation
│
├── src/
│   └── agent/
│       ├── prompts/                  # Runtime (your agent)
│       │   ├── create-todo.md        # Agent capability
│       └── main.py                   # SDK integration code
```

### Advantages

Physical separation provides isolation: Claude Code only scans `.claude/skills/`, while your agent loads from `src/agent/prompts/`. Skill purpose is explicit from location.

### Implementation

**Development skill** (`.claude/skills/dev-debug-python.md`):
```markdown
---
name: dev-debug-python
description: Debug Python code in the todo agent application. Use when investigating runtime errors or logic bugs in the agent itself.
category: development
allowed-tools:
  - Read
  - Grep
  - Bash
---

# Debug Python Agent Code

## Purpose
Help the developer debug the todo agent application code.

## When to Use
- Python exceptions in agent code
- Logic errors in todo creation/validation
- Performance issues in agent loops

## How to Use
1. Read the error traceback
2. Grep for relevant code sections
3. Suggest fixes with explanations
```

**Runtime skill** (`src/agent/prompts/create-todo.md`):
```markdown
# Create Todo Item

You are a todo list agent. When the user requests creating a todo:

1. **Validation**: Check the todo has required fields:
   - title (required, max 200 chars)
   - description (optional)
   - due_date (optional, ISO format)
   - priority (required, values: low/medium/high)

2. **Confirmation**: Show the user what will be created:
   ```
   New Todo:
   Title: {title}
   Priority: {priority}
   Due: {due_date or "No deadline"}

   Proceed? (yes/no)
   ```

3. **Execution**: Only if user confirms "yes":
   - Insert into database
   - Return success message with todo ID

## Example

User: "Create a todo to review PR by Friday with high priority"

Response:
```
New Todo:
Title: Review PR
Priority: high
Due: 2026-01-15

Proceed? (yes/no)
```
```

---

## Pattern 2: Scoped Loading with Hooks

**Advanced**: Use hooks to dynamically control which skills are available in different contexts.

### Use Case

You want to:
- Load development skills during normal coding
- Load ONLY testing skills when running integration tests
- Load ONLY runtime skills when debugging agent behavior

### Implementation with SessionStart Hook

**File**: `.claude/hooks/hooks.json`
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": ".*",
        "command": "python .claude/hooks/scope_skills.py",
        "timeout": 5000
      }
    ]
  }
}
```

**File**: `.claude/hooks/scope_skills.py`
```python
#!/usr/bin/env python3
"""
Dynamically scope which skills Claude Code loads based on environment.
"""
import os
import sys
import json

def main():
    # Read environment variable to determine mode
    mode = os.getenv("CLAUDE_MODE", "development")

    skill_scopes = {
        "development": {
            "skills_dir": ".claude/skills",
            "allowed_prefixes": ["dev-", "test-"],
            "blocked_prefixes": ["runtime-"]
        },
        "testing": {
            "skills_dir": ".claude/skills",
            "allowed_prefixes": ["test-"],
            "blocked_prefixes": ["dev-", "runtime-"]
        },
        "runtime-debug": {
            "skills_dir": "src/agent/prompts",
            "allowed_prefixes": [],  # Load all runtime skills
            "blocked_prefixes": ["dev-"]
        }
    }

    scope = skill_scopes.get(mode, skill_scopes["development"])

    # Return hook output with scope configuration
    output = {
        "hookSpecificOutput": {
            "mode": mode,
            "skills_dir": scope["skills_dir"],
            "scope": scope
        },
        "continueWithRequest": True
    }

    print(json.dumps(output), file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Usage

```bash
# Normal development - loads dev-* and test-* skills
claude

# Testing mode - loads only test-* skills
CLAUDE_MODE=testing claude

# Runtime debugging - loads runtime agent skills into Claude Code
CLAUDE_MODE=runtime-debug claude
```

---

## Pattern 3: Context Forking

**New in Claude Code 2.1.0**: Run skills in isolated context windows.

### Use Case

You want to test your runtime skills WITHOUT them polluting Claude Code's development context.

### Skill with Context Forking

**File**: `.claude/skills/test-runtime-skill.md`
```markdown
---
name: test-runtime-skill
description: Test a runtime agent skill in isolation. Use when validating agent behavior without affecting development context.
category: testing
context: fork                 # ← Runs in isolated sub-agent
allowed-tools:
  - Read
  - Bash
---

# Test Runtime Agent Skill

## Purpose
Load and test a runtime skill (from `src/agent/prompts/`) in an isolated context to verify it works correctly.

## Usage

```
Skill(test-runtime-skill, skill_path="src/agent/prompts/create-todo.md")
```

## Implementation

1. Read the specified runtime skill file
2. Create a test scenario
3. Execute the skill logic in this forked context
4. Report results back to development context

## Example

Test the create-todo skill with sample input:
- Read: `src/agent/prompts/create-todo.md`
- Simulate: User says "Create high priority todo for code review"
- Verify: Correct validation, confirmation prompt, and database structure
```

**How it works:**
- `context: fork` creates a NEW context window
- Runtime skill loads ONLY in the fork
- Results return to main development context
- No pollution between development and runtime namespaces

---

## Pattern 4: Namespace Prefixing

**Convention-based**: Use explicit prefixes to indicate skill purpose.

### Naming Convention

```
Development Skills:
├── dev-debug-python.md
├── dev-review-architecture.md
├── dev-run-tests.md
└── dev-profile-performance.md

Testing Skills:
├── test-runtime-skill.md
├── test-integration.md
└── test-agent-responses.md

Runtime Skills (in src/agent/prompts/):
├── runtime-create-todo.md
├── runtime-validate-todo.md
└── runtime-confirm-action.md
```

### Benefits

1. **Visual Clarity**: Instant recognition of skill purpose
2. **Glob Filtering**: Easy to exclude patterns: `!runtime-*`
3. **Documentation**: Self-documenting directory structure
4. **Tool Compatibility**: Works with any skill loader

---

## SDK Integration

### The Key Question

> "When I am calling the SDK for sending messages to the LLM how do I include the relevant skills file instructions with the request (not using containers, local skills files not stored in cloud)."

### Answer: Compose System Prompts

Your runtime skills are NOT Claude Code skills - they're system prompts for YOUR agent.

### SDK Pattern

**File**: `src/agent/main.py`
```python
"""
Todo Agent - Main entry point
"""
from pathlib import Path
import anthropic

class TodoAgent:
    def __init__(self, prompts_dir: Path = Path("src/agent/prompts")):
        self.client = anthropic.Anthropic()
        self.prompts_dir = prompts_dir
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """
        Compose system prompt from runtime skill files.

        This is YOUR agent's instruction set, NOT Claude Code's.
        """
        skills = []

        # Load all runtime skills from prompts directory
        for skill_file in self.prompts_dir.glob("*.md"):
            skill_content = skill_file.read_text()
            skills.append(f"## {skill_file.stem}\n\n{skill_content}")

        # Compose into single system prompt
        system_prompt = f"""
You are a todo list management agent.

Your capabilities are defined below as individual skills.
When the user makes a request, determine which skill(s) to use.

# Available Skills

{chr(10).join(skills)}

# Operating Rules

1. ALWAYS validate input before taking action
2. ALWAYS confirm destructive operations (delete, update)
3. NEVER create todos without explicit user request
4. Follow the exact format specified in each skill
"""
        return system_prompt

    def chat(self, user_message: str) -> str:
        """Send message to agent with composed runtime skills."""
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=self.system_prompt,  # ← Runtime skills loaded here
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return response.content[0].text

# Usage
if __name__ == "__main__":
    agent = TodoAgent()

    # Runtime skills are loaded into system_prompt
    # Claude Code skills are NOT involved at runtime
    result = agent.chat("Create a todo to review the PR with high priority")
    print(result)
```

### Key Insights

Runtime skills are system prompts (markdown files you compose). Load them dynamically from `src/agent/prompts/` at init. Claude Code helps BUILD the agent; it's not involved at runtime.

---

## Complete Example

### Project Structure

```bash
todo-agent/
├── .claude/                                # Development namespace
│   ├── skills/
│   │   ├── dev-debug-agent.md
│   │   ├── dev-test-skills.md
│   │   └── test-runtime-skill.md         # Uses context: fork
│   ├── hooks/
│   │   ├── hooks.json
│   │   └── scope_skills.py
│   └── settings.json
│
├── src/
│   └── agent/
│       ├── prompts/                       # Runtime namespace
│       │   ├── create-todo.md
│       │   ├── validate-todo.md
│       │   ├── update-todo.md
│       │   ├── delete-todo.md
│       │   └── confirm-action.md
│       ├── main.py                        # SDK integration
│       └── database.py
│
├── tests/
│   ├── test_agent.py
│   └── test_skills/
│       └── test_create_todo.py
│
├── pyproject.toml
└── README.md
```

### Development Workflow

1. **Build Agent Logic**: Normal Claude Code session uses `dev-*` skills to help write runtime prompts
2. **Test Runtime Skills**: Use `test-runtime-skill.md` with `context: fork` to test in isolation
3. **Run Agent**: `python src/agent/main.py` - agent runs independently with composed system prompt

---

## Best Practices

1. **Separate Directories**: Dev skills in `.claude/skills/`, runtime in `src/agent/prompts/`
2. **Explicit Namespacing**: Use `dev-*`, `test-*`, `runtime-*` prefixes
3. **Context Forking**: Use `context: fork` when testing runtime skills from Claude Code
4. **Programmatic Composition**: Read prompts from directory, compose into system prompt

## Summary

| Aspect | Development Skills | Runtime Skills |
|--------|-------------------|----------------|
| **Location** | `.claude/skills/` | `src/agent/prompts/` |
| **Loaded By** | Claude Code | Application SDK code |
| **Purpose** | Development assistance | Agent capabilities |
| **Naming** | `dev-*`, `test-*` | `runtime-*` |

## References

- [Claude Code Skills Documentation](https://docs.claude.com/claude-code/skills)
- [Anthropic SDK - System Prompts](https://docs.anthropic.com/claude/docs/system-prompts)
- [Plugin Development Guide](../plugin-development-guide.md)
