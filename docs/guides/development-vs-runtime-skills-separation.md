# Separating Development and Application Skills

Namespace collisions occur when Claude Code mistakes development tools for application features. This guide defines structures to separate development-time skills from runtime application capabilities.

## The Problem

Namespace collisions typically happen when development and runtime skills share a directory. For example, if `.claude/skills/` contains both `create-todo.md` (a runtime capability) and `debug-python.md` (a development skill), Claude Code may invoke the runtime tool when asked to "Build the to-do list page." Isolation prevents two different execution contexts from sharing a single discovery mechanism.

## Architectural Solutions

| Pattern | Separation Mechanism | Implementation |
|---------|---------------------|----------------|
| **Physical Directory** | Distinct folders for development and runtime skills | Core isolation strategy |
| **Scoped Loading** | Lifecycle hooks to filter available skills | For complex or multi-mode projects |
| **Context Forking** | Isolated execution windows for sub-agents | For testing runtime skills without state pollution |
| **Namespace Prefixing** | Explicit naming conventions: `dev:*` vs `app:*` | For multi-agent systems |

## Physical Directory Separation

Store development skills in `.claude/` and runtime skills in an application-specific prompt directory, such as `src/agent/prompts/`.

### Directory Structure

```bash
my-todo-app/
├── .claude/                          # Development-time (Claude Code)
│   ├── skills/
│   │   ├── dev-debug-python.md       # Developer assistance
│   └── hooks/
│       └── hooks.json                # Automation logic
│
├── src/
│   └── agent/
│       ├── prompts/                  # Runtime (application agent)
│       │   ├── create-todo.md        # Agent tool definition
│       └── main.py                   # SDK integration logic
```

This structure ensures Claude Code only scans `.claude/skills/` for CLI operations. The application agent loads its instructions explicitly from `src/agent/prompts/`.

## Pattern 2: Scoped Loading with Hooks

Lifecycle hooks can dynamically filter skill availability based on the environment or task mode. This allows loading testing-only skills during integration runs or runtime-only skills when debugging specific agent behaviors.

### Implementation with SessionStart Hook

Define a `SessionStart` hook in `.claude/hooks/hooks.json` to execute a scoping script:

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

The scoping script (`.claude/hooks/scope_skills.py`) reads the `CLAUDE_MODE` environment variable to determine which skill directory to load and which prefixes to allow or block.

## Pattern 3: Context Forking

Claude Code supports running skills in isolated sub-agent contexts using `context: fork`. This allows testing runtime skills without polluting the primary development session.

### Skill with Context Forking

Define the test skill in `.claude/skills/test-runtime-skill.md` with the `context: fork` metadata. The skill then reads the runtime definition from `src/agent/prompts/`, executes the logic in the forked context, and returns the result to the main session. This prevents intermediate outputs and tool calls from interfering with the developer's primary history.

## Pattern 4: Namespace Prefixing

Explicit prefixes provide visual clarity and allow for glob-based filtering when loading skills programmatically.

- **Development**: `dev-debug-python.md`, `dev-run-tests.md`
- **Testing**: `test-runtime-skill.md`, `test-agent-responses.md`
- **Runtime**: `runtime-create-todo.md`, `runtime-confirm-action.md`

## SDK Integration

Runtime skills are not directly managed by Claude Code; they function as system prompts for the application agent. Load these files programmatically from the prompts directory and compose them into the system prompt during initialization.

### SDK Pattern

In `src/agent/main.py`, use a class to manage prompt loading. The `_build_system_prompt` method iterates through the `*.md` files in the prompts directory, reads their content, and joins them into a single string. This approach avoids hardcoding prompt logic into the application code and allows for dynamic updates to agent capabilities.

## Technical Standards

Enforce directory boundaries by keeping development-time logic in `.claude/skills/` and runtime logic in `src/agent/prompts/`. Use consistent prefixing (`dev-`, `test-`, `runtime-`) to simplify troubleshooting. When validating runtime behavior, use `context: fork` to avoid side effects in the development environment.

## Summary

| Aspect | Development Skills | Runtime Skills |
|--------|-------------------|----------------|
| **Location** | `.claude/skills/` | `src/agent/prompts/` |
| **Execution** | Loaded by Claude Code | Loaded by Application SDK |
| **Purpose** | Development assistance | Agent tool definitions |
| **Prefix** | `dev-*`, `test-*` | `runtime-*` |
