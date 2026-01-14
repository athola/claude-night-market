# Agent Boundaries & Entry Points

> **Created**: 2026-01-08
> **Issue**: #70 - Clarify agent boundaries and reduce complexity

Reference for agent selection and relationships.

## Start Here

Primary entry point agents:

1. **`abstract:plugin-validator`** - Validate plugin structure before making changes
2. **`pensive:code-reviewer`** - Review code changes
3. **`sanctum:pr-agent`** - Prepare pull requests

**Advanced workflows** involve specialized agents that build on these foundations.

---

## Agent Layers

The ecosystem organizes agents in layers, each building on the layer below:

```
[ Domain Specialists (pensive, parseltongue, etc.) ]
  (Use utility agents for support)
[ Utility Layer (conserve, conjure, hookify) ]
  (Use foundation agents for workflows)
[ Foundation (imbue, sanctum, leyline) ]
  (Use meta agents for validation)
[ Meta (abstract) - Plugin dev & validation ]
```

**Key Principle**: Higher-layer agents delegate to lower-layer agents. Lower layers don't know about higher layers.

---

## Agent Responsibilities

### Meta Layer (Plugin Development)

| Agent | When To Use | Boundary |
|-------|-------------|----------|
| `abstract:plugin-validator` | Validate plugin structure before commits | Structure validation (no business logic) |
| `abstract:skill-auditor` | Audit skill quality and token efficiency | Quality metrics (no functional testing) |

**Context**: Use meta agents for development within the plugin ecosystem.

---

### Foundation Layer (Core Workflows)

| Agent | When To Use | Boundary |
|-------|-------------|----------|
| `sanctum:pr-agent` | Prepare pull requests and commit messages | Git workflows (no code review quality) |
| `imbue:proof-evaluator` | Validate proof-of-work requirements | Verification (no implementation) |
| `leyline:dependency-mapper` | Map plugin dependencies | Dependency analysis (no refactoring) |

**Context**: Use foundation agents for version control, validation gates, and cross-plugin coordination.

---

### Utility Layer (Optimization & Generation)

| Agent | When To Use | Boundary |
|-------|-------------|----------|
| `conserve:context-optimizer` | Assess MECW and token usage | Token analysis (no code optimization) |
| `conserve:bloat-auditor` | Detect codebase bloat | Detection (no remediation decisions) |
| `conserve:unbloat-remediator` | Execute bloat removal | Safe deletion (no architecture changes) |
| `conjure:generator` | Generate boilerplate code | Templates (no business logic) |
| `hookify:rule-compiler` | Compile hook rules | Hook generation (no hook logic) |

**Context**: Use utility agents for cross-cutting concerns like performance, boilerplate, and infrastructure.

---

### Domain Layer (Specialized Tasks)

| Agent | When To Use | Boundary |
|-------|-------------|----------|
| `pensive:code-reviewer` | Multi-discipline code review | API, architecture, and security review (no fixes) |
| `pensive:architecture-reviewer` | Architecture design review | Design patterns (no implementation) |
| `pensive:rust-auditor` | Rust-specific code review | Rust idioms and safety (no other languages) |
| `parseltongue:python-tester` | Python test generation | Python testing (no other languages) |
| `parseltongue:pytest-analyst` | Pytest output analysis | Test diagnostics (no code fixes) |
| `memory-palace:curator` | Knowledge management | Documentation organization (no code changes) |
| `spec-kit:spec-writer` | Write specifications | Requirements (no implementation) |

**Context**: Use domain agents for specialized expertise in a language, paradigm, or discipline.

---

## Common Delegation Patterns

### Code Review Workflow

```
User Request: "Review this PR"
       |
pensive:code-reviewer (Domain)
       | delegates to ->
       |- pensive:api-reviewer (API design)
       |- pensive:security-reviewer (Security)
       |_ pensive:performance-reviewer (Performance)
       | uses ->
sanctum:pr-agent (Foundation) for git integration
       | validates with ->
abstract:plugin-validator (Meta) if plugin code
```

### Plugin Development Workflow

```
User Request: "Create new skill"
       |
abstract:skill-generator (Meta)
       | validates with ->
abstract:skill-auditor (Meta) for quality
       | uses ->
conserve:context-optimizer (Utility) for token efficiency
       | commits with ->
sanctum:pr-agent (Foundation)
```

### Bloat Remediation Workflow

```
User Request: "Clean up codebase"
       |
conserve:bloat-auditor (Utility) - scan
       | reports to user ->
User approves changes
       |
conserve:unbloat-remediator (Utility) - execute
       | uses ->
sanctum:pr-agent (Foundation) for commit
```

---

## When Agents Say "No"

Agents respect their boundaries. Here's what happens when you ask outside their scope:

| Request | Agent Response | Next Step |
|---------|----------------|-----------|
| "abstract:plugin-validator, fix this bug" | "I validate structure, not fix logic. Use `pensive:code-reviewer` instead." | Redirect to domain agent |
| "pensive:code-reviewer, commit this" | "I review code, not manage git. Use `sanctum:pr-agent` to commit." | Redirect to foundation agent |
| "conserve:bloat-auditor, delete these files" | "I detect bloat, not remediate. Use `conserve:unbloat-remediator` to delete." | Redirect to sibling agent |

This design is intentional. Agents with clear boundaries are easier to understand and maintain predictable behavior. They combine more reliably and help reduce token usage by preventing scope creep into unrelated tasks.

## Agent Selection Decision Tree

```
+-- Working on plugins themselves?
|   +-- Yes -> abstract:* (Meta)
|
+-- Need git/version control?
|   +-- Yes -> sanctum:* (Foundation)
|
+-- Need validation/gates?
|   +-- Yes -> imbue:* (Foundation)
|
+-- Need token optimization?
|   +-- Yes -> conserve:* (Utility)
|
+-- Need code generation?
|   +-- Yes -> conjure:* (Utility)
|
+-- Need language-specific help?
|   +-- Python -> parseltongue:*
|   +-- Rust -> pensive:rust-auditor
|   +-- General -> pensive:*
|
+-- Need architecture/design?
|   +-- Yes -> pensive:architecture-reviewer, spec-kit:*
|
+-- Need documentation?
    +-- Yes -> memory-palace:*, sanctum:update-docs
```

---

## FAQ

**Q: Why so many agents? Can't one agent do everything?**

A: Specialized agents are more reliable, use fewer tokens, and compose better. A general-purpose agent would need the context of all domains, leading to:
- Higher token cost per invocation
- Conflicting guidance (e.g., "ship fast" vs. "comprehensive tests")
- Harder to predict behavior

**Q: How do I know which agent to start with?**

A: Use the decision tree above, or:
1. **For code**: `pensive:code-reviewer`
2. **For plugins**: `abstract:plugin-validator`
3. **For git**: `sanctum:pr-agent`
4. **For optimization**: `conserve:bloat-auditor`

**Q: Can agents call each other?**

A: Yes, via **delegation**. Higher-layer agents delegate to lower-layer agents. The ecosystem prevents circular dependencies by design.

**Q: What if I pick the wrong agent?**

A: The agent will tell you and recommend the right one (see "When Agents Say 'No'" above).

---

## Related Documentation

- [Plugin Development Guide](../plugin-development-guide.md) - Building new plugins/agents
- [Capabilities Reference](../../book/src/reference/capabilities-reference.md) - All 107 skills, 81 commands, 34 agents
- [Conservation Guide](../../plugins/conserve/README.md) - Token optimization strategies

---

**Last Updated**: 2026-01-08
**Related Issue**: [#70 - Clarify token conservation strategy and agent boundaries](https://github.com/athola/claude-night-market/issues/70)
