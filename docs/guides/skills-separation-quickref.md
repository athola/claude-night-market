# Skills Separation Quick Reference

**Problem**: Building AI agents with Claude Code? Don't let development skills collide with runtime skills!

---

## The Golden Rule

```
.claude/skills/          → Claude Code helps YOU (development)
src/agent/prompts/       → YOUR agent uses these (runtime)
```

**NEVER MIX THESE DIRECTORIES**

---

## 4 Separation Patterns

### 1. Physical Directory Separation (Always Use)

```bash
my-agent/
├── .claude/skills/              # Dev skills
│   ├── dev-debug.md
│   └── dev-test.md
└── src/agent/prompts/           # Runtime skills
    ├── create-todo.md
    └── validate-todo.md
```

### 2. Namespace Prefixing (Convention)

```
dev-*        → Development skills
test-*       → Testing skills
runtime-*    → Runtime skills (if in .claude/)
```

### 3. Context Forking (Testing Runtime Skills)

```markdown
---
name: test-runtime-skill
context: fork              # ← Isolated context
---
```

### 4. Scoped Loading (Advanced)

```bash
# Development mode
claude

# Test mode only
CLAUDE_MODE=testing claude

# Debug runtime skills
CLAUDE_MODE=runtime-debug claude
```

---

## SDK Integration

**Your runtime skills = System prompts for your agent**

```python
class MyAgent:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.system_prompt = self._load_skills()

    def _load_skills(self) -> str:
        """Load from src/agent/prompts/, NOT .claude/skills/"""
        skills = []
        for f in Path("src/agent/prompts").glob("*.md"):
            skills.append(f.read_text())
        return "\n\n".join(skills)

    def chat(self, message: str):
        return self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=self.system_prompt,  # ← Runtime skills here
            messages=[{"role": "user", "content": message}]
        )
```

---

## Workflow

```
┌─────────────────────────────────────────────────┐
│ 1. Development (Claude Code)                    │
│    You: "Build create-todo logic"               │
│    Claude: [uses dev-debug.md to help YOU]      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 2. Testing (Context Fork)                       │
│    You: "Test create-todo skill"                │
│    Claude: [loads runtime skill in fork]        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 3. Runtime (Your Agent)                         │
│    User: "Create a todo"                        │
│    Agent: [uses src/agent/prompts/create-todo]  │
└─────────────────────────────────────────────────┘
```

---

## Common Mistakes

| ❌ DON'T | ✅ DO |
|---------|------|
| Put runtime skills in `.claude/skills/` | Separate directory: `src/agent/prompts/` |
| Name skills ambiguously: `debug.md` | Prefix clearly: `dev-debug.md` |
| Load `.claude/` skills into agent | Load from `src/agent/prompts/` only |
| Hardcode system prompts | Compose from skill files dynamically |
| Mix contexts during testing | Use `context: fork` for isolation |

---

## Troubleshooting

**Problem**: Claude Code creates todos instead of building the page

→ **Solution**: Move `create-todo.md` out of `.claude/skills/`

**Problem**: Agent has empty system prompt

→ **Solution**: Check `Path("src/agent/prompts").exists()` and glob

**Problem**: Skills bleeding between contexts

→ **Solution**: Verify directory separation + use namespace prefixes

---

## Night Market Plugins

- **abstract**: `modular-skills` - Skill architecture patterns
- **conserve**: `bloat-scan` - Keep skills lean
- **pensive**: `full-review` - Review separately
- **spec-kit**: `/speckit-specify` - Spec before build

---

## Full Guide

See: [`development-vs-runtime-skills-separation.md`](development-vs-runtime-skills-separation.md)

**Last Updated**: 2026-01-10
