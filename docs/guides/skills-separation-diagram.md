# Skills Separation Visual Guide

Visual diagrams showing the separation between development skills and runtime skills.

---

## The Problem: Namespace Collision

```mermaid
flowchart TB
    subgraph problem["❌ PROBLEM: Mixed Skills in .claude/skills/"]
        dev1[dev-debug.md]
        dev2[dev-test.md]
        runtime1[create-todo.md]
        runtime2[validate-todo.md]
    end

    claude[Claude Code]
    user[You ask: 'Build todo page']

    user --> claude
    claude -.sees all skills.-> problem
    claude -.confuses context!.-> runtime1

    style problem fill:#ffcccc,stroke:#ff0000
    style claude fill:#cce5ff,stroke:#0066cc
```

**What goes wrong**:
- You: "Build the to-do list page"
- Claude Code: *Sees `create-todo.md`*
- Claude Code: *Tries to CREATE a todo instead of BUILDING THE PAGE*

---

## The Solution: Physical Separation

```mermaid
flowchart TB
    subgraph dev[".claude/skills/ (Development)"]
        direction LR
        dev1[dev-debug-agent.md]
        dev2[dev-test-runtime.md]
        dev3[dev-review-code.md]
    end

    subgraph runtime["src/agent/prompts/ (Runtime)"]
        direction LR
        runtime1[create-todo.md]
        runtime2[validate-todo.md]
        runtime3[confirm-action.md]
    end

    claude[Claude Code]
    agent[Your Agent]
    sdk[SDK Integration]

    claude -->|loads only| dev
    agent -->|loads via SDK| runtime
    sdk -.reads & composes.-> runtime

    style dev fill:#ccffcc,stroke:#00cc00
    style runtime fill:#ffffcc,stroke:#cccc00
    style claude fill:#cce5ff,stroke:#0066cc
    style agent fill:#ffccff,stroke:#cc00cc
```

---

## Complete Workflow

```mermaid
sequenceDiagram
    participant You
    participant Claude as Claude Code
    participant DevSkills as .claude/skills/
    participant RuntimeSkills as src/agent/prompts/
    participant Agent as Your Agent (SDK)

    Note over You,Agent: Phase 1: Development

    You->>Claude: "Build create-todo logic"
    Claude->>DevSkills: Load dev-debug-agent.md
    Claude->>You: Help write src/agent/prompts/create-todo.md
    You->>RuntimeSkills: Save create-todo.md

    Note over You,Agent: Phase 2: Testing (Context Fork)

    You->>Claude: "Test create-todo skill"
    Claude->>DevSkills: Load test-runtime-skill.md (context: fork)
    Claude->>RuntimeSkills: Read create-todo.md in fork
    Claude->>You: Report test results

    Note over You,Agent: Phase 3: Production Runtime

    You->>Agent: Run agent application
    Agent->>RuntimeSkills: Load all .md files
    Agent->>Agent: Compose system_prompt
    Agent->>You: Ready (runtime skills loaded)

    Note over Claude,DevSkills: Claude Code NOT involved in runtime
```

---

## Directory Structure

```
my-todo-agent/
│
├── .claude/                               ← DEVELOPMENT NAMESPACE
│   ├── skills/                            ← Claude Code loads these
│   │   ├── dev-debug-agent.md             │  (helps YOU build)
│   │   ├── dev-test-runtime.md            │
│   │   └── dev-review-architecture.md     │
│   │                                       │
│   ├── hooks/                              │
│   │   ├── hooks.json                      │
│   │   └── scope_skills.py                │  (optional: scoped loading)
│   │                                       │
│   └── settings.json                       │
│
├── src/
│   └── agent/
│       ├── prompts/                       ← RUNTIME NAMESPACE
│       │   ├── create-todo.md             │  (agent capabilities)
│       │   ├── validate-todo.md           │
│       │   ├── update-todo.md             │
│       │   └── confirm-action.md          │
│       │                                   │
│       ├── main.py ←──────────────────────┘  loads prompts/ via SDK
│       └── database.py
│
├── tests/
│   ├── test_agent.py
│   └── test_skills/
│       └── test_create_todo.py
│
└── pyproject.toml


CRITICAL RULES:
═══════════════
1. Claude Code ONLY sees .claude/skills/
2. Your agent ONLY loads src/agent/prompts/ (via SDK)
3. NEVER import .claude/ from your agent code
4. NEVER put runtime skills in .claude/skills/
```

---

## SDK Integration Flow

```mermaid
flowchart LR
    subgraph app["Your Application"]
        main[main.py]
        agent[TodoAgent class]
        init[__init__ method]
    end

    subgraph prompts["src/agent/prompts/"]
        skill1[create-todo.md]
        skill2[validate-todo.md]
        skill3[confirm-action.md]
    end

    subgraph sdk["Anthropic SDK"]
        client[anthropic.Anthropic]
        messages[messages.create]
    end

    init -->|"Path('src/agent/prompts').glob('*.md')"| prompts
    prompts -->|read & compose| init
    init -->|system_prompt| agent
    agent -->|uses| client
    client -->|system=system_prompt| messages

    style app fill:#ccffcc,stroke:#00cc00
    style prompts fill:#ffffcc,stroke:#cccc00
    style sdk fill:#ffccff,stroke:#cc00cc
```

**Code**:
```python
# In src/agent/main.py
def _build_system_prompt(self) -> str:
    skills = []
    for f in Path("src/agent/prompts").glob("*.md"):  # ← Runtime skills
        skills.append(f.read_text())
    return "\n\n".join(skills)

# In chat method
self.client.messages.create(
    system=self.system_prompt,  # ← Composed from runtime skills
    messages=[{"role": "user", "content": message}]
)
```

---

## Context Isolation with Forking

```mermaid
flowchart TB
    subgraph main["Main Development Context"]
        mainSkills[".claude/skills/
        dev-debug-agent.md
        dev-review-code.md
        test-runtime-skill.md"]
    end

    subgraph fork["Forked Context (Isolated)"]
        direction TB
        forkSkill["test-runtime-skill.md
        (context: fork)"]
        runtimeSkill["src/agent/prompts/
        create-todo.md
        ← loaded in fork"]
        test[Test execution]

        forkSkill --> runtimeSkill
        runtimeSkill --> test
    end

    results["Test Results
    ✓ Validation works
    ✓ Confirmation prompt correct
    ✓ Database structure valid"]

    mainSkills -->|invoke with fork| fork
    fork -->|report back| results
    results -->|return to| main

    style main fill:#cce5ff,stroke:#0066cc
    style fork fill:#fff3cd,stroke:#ffc107
    style results fill:#d4edda,stroke:#28a745
```

**How it works**:
1. You invoke `Skill(test-runtime-skill)` in Claude Code
2. `context: fork` creates isolated context window
3. Runtime skill loads ONLY in fork (no pollution)
4. Results return to main development context
5. Main context stays clean

---

## Anti-Patterns vs Correct Patterns

### ❌ Anti-Pattern: Mixed Namespace

```
.claude/skills/
├── debug-python.md          ← Development
├── review-architecture.md   ← Development
├── create-todo.md           ← Runtime (WRONG!)
└── validate-todo.md         ← Runtime (WRONG!)
```

**Problem**: Claude Code will confuse runtime skills with requests

### ✅ Correct Pattern: Separated Namespaces

```
.claude/skills/              ← Development ONLY
├── dev-debug-python.md
├── dev-review-architecture.md
└── test-runtime-skill.md    (uses context: fork)

src/agent/prompts/           ← Runtime ONLY
├── create-todo.md
└── validate-todo.md
```

**Benefit**: Clear separation, no confusion

---

### ❌ Anti-Pattern: Hardcoded System Prompt

```python
# main.py
system_prompt = """
You are a todo agent. When user asks to create a todo:
1. Validate the input
2. Confirm with user
3. Insert into database
"""
```

**Problem**:
- Not maintainable (hardcoded)
- No separation from application logic
- Can't reuse skills

### ✅ Correct Pattern: Dynamic Composition

```python
# main.py
def _build_system_prompt(self) -> str:
    skills = []
    for f in Path("src/agent/prompts").glob("*.md"):
        skills.append(f.read_text())
    return "\n\n".join(skills)
```

**Benefit**:
- Skills are files (maintainable)
- Easy to add/remove capabilities
- Can test skills independently

---

## Decision Tree

```mermaid
flowchart TD
    start([You need to write a skill])
    question1{Who will use it?}
    question2{For what purpose?}
    question3{How to load it?}

    start --> question1

    question1 -->|Claude Code helps YOU| devSkill[Development Skill]
    question1 -->|Your AGENT uses it| runtimeSkill[Runtime Skill]

    devSkill --> devPath["📁 .claude/skills/
    📄 dev-debug-agent.md
    📄 dev-test-runtime.md"]

    runtimeSkill --> question2

    question2 -->|Agent capability| capabilityPath["📁 src/agent/prompts/
    📄 create-todo.md
    📄 validate-todo.md"]

    question2 -->|Testing runtime skill| testSkill["📁 .claude/skills/
    📄 test-runtime-skill.md
    (context: fork)"]

    capabilityPath --> question3
    question3 -->|SDK Integration| sdk["Load via Path.glob
    Compose into system_prompt
    Pass to messages.create"]

    style devSkill fill:#cce5ff,stroke:#0066cc
    style runtimeSkill fill:#ffffcc,stroke:#cccc00
    style testSkill fill:#fff3cd,stroke:#ffc107
    style sdk fill:#ffccff,stroke:#cc00cc
```

---

## Summary Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SKILLS SEPARATION RULES                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Development Skills              Runtime Skills                     │
│  ┌─────────────────┐            ┌──────────────────┐               │
│  │ .claude/skills/ │            │ src/agent/       │               │
│  │                 │            │ prompts/         │               │
│  │ dev-*.md        │            │                  │               │
│  │ test-*.md       │            │ create-todo.md   │               │
│  │                 │            │ validate-todo.md │               │
│  └─────────────────┘            └──────────────────┘               │
│         ▲                                ▲                          │
│         │                                │                          │
│         │ loads                          │ loads                   │
│         │                                │                          │
│  ┌──────┴────────┐            ┌─────────┴────────┐                │
│  │ Claude Code   │            │ Your Agent (SDK) │                │
│  │               │            │                  │                │
│  │ Helps YOU     │            │ Runtime behavior │                │
│  │ build agent   │            │ (independent)    │                │
│  └───────────────┘            └──────────────────┘                │
│                                                                      │
│  CRITICAL: These namespaces NEVER overlap                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## References

- **Full Guide**: [development-vs-runtime-skills-separation.md](development-vs-runtime-skills-separation.md)
- **Quick Reference**: [skills-separation-quickref.md](skills-separation-quickref.md)
- **Guides Index**: [README.md](README.md)

---

**Last Updated**: 2026-01-10
**Applies To**: Claude Code 2.1.0+, Anthropic SDK 0.40.0+
