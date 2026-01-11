# Separating Development Skills from Application Skills

**Problem Statement**: How do you use Claude Code to build an AI agent application without the development assistant confusing its own skills with the skills you're programming into your agent?

This guide shows proven patterns from the claude-night-market ecosystem for maintaining clean separation between:
1. **Development Skills**: Skills that help YOU build your application (Claude Code assisting development)
2. **Runtime Skills**: Skills that your APPLICATION uses when deployed (your agent's capabilities)

## Table of Contents

- [The Problem](#the-problem)
- [Architectural Solutions](#architectural-solutions)
- [Pattern 1: Physical Directory Separation](#pattern-1-physical-directory-separation)
- [Pattern 2: Scoped Loading with Hooks](#pattern-2-scoped-loading-with-hooks)
- [Pattern 3: Context Forking](#pattern-3-context-forking)
- [Pattern 4: Namespace Prefixing](#pattern-4-namespace-prefixing)
- [SDK Integration](#sdk-integration)
- [Complete Example](#complete-example)
- [Best Practices](#best-practices)

---

## The Problem

Consider building a to-do list agent using Claude Code:

```
❌ Problematic Structure:
.claude/skills/
├── create-todo.md          # Runtime: Agent creates todos
├── validate-todo.md        # Runtime: Agent validates todos
├── debug-python.md         # Development: Claude Code helps you debug
└── review-architecture.md  # Development: Claude Code reviews your design
```

**What goes wrong:**
1. You ask Claude Code: "Build the to-do list page"
2. Claude Code sees `create-todo.md` skill
3. Claude Code tries to CREATE a todo instead of BUILDING THE PAGE
4. You wanted the second skill, got the first by mistake

This is **namespace collision** - two different contexts (development vs runtime) sharing the same skill discovery mechanism.

---

## Architectural Solutions

The claude-night-market ecosystem uses 4 complementary patterns:

| Pattern | Separation Mechanism | Use When |
|---------|---------------------|----------|
| **Physical Directory** | Different folders for dev vs runtime | Always (foundation) |
| **Scoped Loading** | Hooks control which skills load when | Complex projects |
| **Context Forking** | Isolated context windows per skill | Testing runtime skills |
| **Namespace Prefixing** | Explicit naming: `dev:*` vs `app:*` | Multi-agent systems |

---

## Pattern 1: Physical Directory Separation

**Core Principle**: Keep development skills in `.claude/` and runtime skills in `src/agent/prompts/` (or similar application directory).

### Directory Structure

```bash
my-todo-app/
├── .claude/                          # Development-time (Claude Code)
│   ├── skills/
│   │   ├── dev-debug-python.md       # Helps YOU debug
│   │   ├── dev-review-code.md        # Helps YOU review
│   │   └── dev-test-agent.md         # Helps YOU test the agent
│   └── hooks/
│       └── hooks.json                # Claude Code automation
│
├── src/
│   └── agent/
│       ├── prompts/                  # Runtime (your agent)
│       │   ├── create-todo.md        # Agent capability
│       │   ├── validate-todo.md      # Agent capability
│       │   └── confirm-action.md     # Agent capability
│       └── main.py                   # SDK integration code
│
└── pyproject.toml
```

### Why This Works

1. **Claude Code only scans `.claude/skills/`** - it won't auto-load runtime skills
2. **Your agent only loads `src/agent/prompts/`** - it doesn't see development skills
3. **Clear semantic boundary** - directory name indicates purpose

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

1. **Runtime skills are system prompts** - They're markdown files you read and compose
2. **Load skills dynamically** - Read from `src/agent/prompts/` at initialization
3. **No Claude Code involvement at runtime** - Your agent runs independently
4. **Claude Code helps BUILD the agent** - Using development skills in `.claude/`

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

#### Step 1: Build Agent Logic (Claude Code Development Mode)

```bash
# Normal Claude Code session
claude

# You have access to:
# - dev-debug-agent.md
# - dev-test-skills.md
# - test-runtime-skill.md
```

Example interaction:
```
You: "Help me implement the create-todo agent skill"

Claude Code:
[Uses dev-debug-agent.md to help YOU write src/agent/prompts/create-todo.md]
[Suggests validation rules, confirmation patterns, error handling]
```

#### Step 2: Test Runtime Skills (Forked Context)

```bash
# Still in Claude Code, but testing runtime behavior
claude
```

```
You: "Test the create-todo runtime skill with sample input"

Claude Code:
[Uses test-runtime-skill.md with context: fork]
[Loads src/agent/prompts/create-todo.md in isolated context]
[Simulates user input, verifies agent response]
[Reports results back to development context]
```

#### Step 3: Run Agent (Production Runtime)

```bash
# Your application runs independently
python src/agent/main.py

# Agent loads:
# - src/agent/prompts/create-todo.md (into system_prompt)
# - src/agent/prompts/validate-todo.md (into system_prompt)
# - ... all runtime skills
```

**No Claude Code involvement** - your agent runs with its own system prompt composed from runtime skill files.

---

## Best Practices

### 1. Clear Directory Boundaries

```
✅ DO:
.claude/skills/          # Development only
src/agent/prompts/       # Runtime only

❌ DON'T:
.claude/skills/          # Mixed development + runtime
```

### 2. Namespace Everything

```
✅ DO:
dev-debug-python.md      # Clear prefix
runtime-create-todo.md   # Clear prefix

❌ DON'T:
debug.md                 # Ambiguous
create-todo.md          # Which context?
```

### 3. Use Context Forking for Testing

```markdown
✅ DO:
---
name: test-runtime-skill
context: fork            # Isolated testing
---

❌ DON'T:
Load runtime skills directly into development context
```

### 4. Compose System Prompts Programmatically

```python
✅ DO:
def _build_system_prompt(self) -> str:
    skills = []
    for skill_file in self.prompts_dir.glob("*.md"):
        skills.append(skill_file.read_text())
    return compose_skills(skills)

❌ DON'T:
system_prompt = """
Hardcoded instructions...
"""
```

### 5. Document Separation in README

```markdown
# Todo Agent

## Architecture

This project separates development-time and runtime-time AI skills:

- `.claude/skills/`: Claude Code development assistance
- `src/agent/prompts/`: Agent runtime capabilities (loaded into system_prompt)

See `docs/skills-separation.md` for details.
```

---

## Related Night Market Plugins

| Plugin | Helps With | Key Skills/Commands |
|--------|-----------|---------------------|
| **abstract** | Skill architecture patterns | `modular-skills`, `validate-plugin-structure` |
| **conserve** | Context optimization | `bloat-scan` (keep skills lean) |
| **pensive** | Code review | `full-review` (review agent + dev code separately) |
| **sanctum** | Git workflows | `/pr` (prepare agent releases) |
| **spec-kit** | Spec-driven development | `/speckit-specify` (spec before building skills) |

---

## Troubleshooting

### Problem: Claude Code uses runtime skills during development

**Symptom**: You ask "Build the todo page" and Claude tries to create a todo.

**Solution**:
1. Move runtime skills OUT of `.claude/skills/`
2. Put them in `src/agent/prompts/` or similar app directory
3. Use `test-runtime-skill.md` with `context: fork` if you need to test them

### Problem: Agent can't find runtime skills

**Symptom**: Agent starts but has empty system prompt.

**Solution**:
```python
# Check prompts directory exists
assert self.prompts_dir.exists(), f"Prompts dir not found: {self.prompts_dir}"

# Log loaded skills
skills = list(self.prompts_dir.glob("*.md"))
print(f"Loaded {len(skills)} runtime skills: {[s.stem for s in skills]}")
```

### Problem: Skills bleeding between contexts

**Symptom**: Development skills appear in agent responses.

**Solution**:
1. **Verify directory separation**: `ls .claude/skills/` vs `ls src/agent/prompts/`
2. **Check imports**: Make sure `main.py` doesn't import from `.claude/`
3. **Use namespacing**: Prefix all skills with `dev-` or `runtime-`

---

## Summary

| Aspect | Development Skills | Runtime Skills |
|--------|-------------------|----------------|
| **Location** | `.claude/skills/` | `src/agent/prompts/` |
| **Loaded By** | Claude Code | Your application SDK code |
| **Purpose** | Help YOU build | Your AGENT's capabilities |
| **Format** | Skill frontmatter + markdown | Plain markdown/prompts |
| **Naming** | `dev-*`, `test-*` | `runtime-*` or domain-specific |
| **Testing** | Regular Claude Code usage | `context: fork` or unit tests |

**Mental Model**:
- Development skills = Tools in YOUR toolbox (Claude Code assists)
- Runtime skills = Instructions in YOUR AGENT's brain (system prompts)

They should NEVER mix.

---

## References

- [Claude Code Skills Documentation](https://docs.claude.com/claude-code/skills)
- [Anthropic SDK - System Prompts](https://docs.anthropic.com/claude/docs/system-prompts)
- [claude-night-market Plugin Development Guide](../plugin-development-guide.md)
- [Skill Observability Guide](skill-observability-guide.md) - Track skill execution metrics
- [Context Forking (2.1.0)](../plugin-development-guide.md#new-frontmatter-fields-210)

---

**Last Updated**: 2026-01-10
**Applies To**: Claude Code 2.1.0+, Anthropic SDK 0.40.0+
