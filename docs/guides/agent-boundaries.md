# Agent Boundaries & Entry Points

> **Created**: 2026-01-08
> **Issue**: #70 - Clarify agent boundaries and reduce overwhelming complexity

Quick reference for understanding which agents to use and how they relate.

## Start Here

**New to the ecosystem?** Start with these agents:

1. **`abstract:plugin-validator`** - Validate plugin structure before making changes
2. **`pensive:code-reviewer`** - Review code changes
3. **`sanctum:pr-agent`** - Prepare pull requests

**Advanced workflows** involve specialized agents that build on these foundations.

---

## Agent Layers

The ecosystem organizes agents in layers, each building on the layer below:

```
┌─────────────────────────────────────────────────────┐
│  Domain Specialists (pensive, parseltongue, etc.)  │
│  ↓ Use utility agents for support                   │
├─────────────────────────────────────────────────────┤
│  Utility Layer (conserve, conjure, hookify)        │
│  ↓ Use foundation agents for workflows             │
├─────────────────────────────────────────────────────┤
│  Foundation (imbue, sanctum, leyline)              │
│  ↓ Use meta agents for validation                  │
├─────────────────────────────────────────────────────┤
│  Meta (abstract) - Plugin dev & validation         │
└─────────────────────────────────────────────────────┘
```

**Key Principle**: Higher-layer agents delegate to lower-layer agents. Lower layers don't know about higher layers.

---

## Agent Responsibilities

### Meta Layer (Plugin Development)

| Agent | When To Use | Boundary |
|-------|-------------|----------|
| `abstract:plugin-validator` | Validating plugin structure before commits | ✅ Structure validation<br>❌ Business logic |
| `abstract:skill-auditor` | Auditing skill quality & token efficiency | ✅ Quality metrics<br>❌ Functional testing |

**Decision Point**: Use meta agents when working ON the plugin ecosystem itself, not when using plugins.

---

### Foundation Layer (Core Workflows)

| Agent | When To Use | Boundary |
|-------|-------------|----------|
| `sanctum:pr-agent` | Preparing pull requests, commit messages | ✅ Git workflows<br>❌ Code review quality |
| `imbue:proof-evaluator` | Validating proof-of-work requirements met | ✅ Verification<br>❌ Implementation |
| `leyline:dependency-mapper` | Understanding plugin dependencies | ✅ Dependency analysis<br>❌ Refactoring |

**Decision Point**: Use foundation agents for version control, validation gates, and cross-plugin coordination.

---

### Utility Layer (Optimization & Generation)

| Agent | When To Use | Boundary |
|-------|-------------|----------|
| `conserve:context-optimizer` | Assessing MECW & token usage | ✅ Token analysis<br>❌ Code optimization |
| `conserve:bloat-auditor` | Detecting codebase bloat | ✅ Detection<br>❌ Remediation decisions |
| `conserve:unbloat-remediator` | Executing bloat removal | ✅ Safe deletion<br>❌ Architecture changes |
| `conjure:generator` | Generating boilerplate code | ✅ Templates<br>❌ Business logic |
| `hookify:rule-compiler` | Compiling hook rules | ✅ Hook generation<br>❌ Hook logic |

**Decision Point**: Use utility agents for cross-cutting concerns like performance, boilerplate, and infrastructure.

---

### Domain Layer (Specialized Tasks)

| Agent | When To Use | Boundary |
|-------|-------------|----------|
| `pensive:code-reviewer` | Multi-discipline code review | ✅ API, architecture, security review<br>❌ Fixing issues |
| `pensive:architecture-reviewer` | Architecture design review | ✅ Design patterns<br>❌ Implementation |
| `pensive:rust-auditor` | Rust-specific code review | ✅ Rust idioms, safety<br>❌ Other languages |
| `parseltongue:python-tester` | Python test generation & execution | ✅ Python testing<br>❌ Other languages |
| `parseltongue:pytest-analyst` | Pytest output analysis | ✅ Test diagnostics<br>❌ Code fixes |
| `memory-palace:curator` | Knowledge management | ✅ Documentation organization<br>❌ Code changes |
| `spec-kit:spec-writer` | Writing specifications | ✅ Requirements<br>❌ Implementation |

**Decision Point**: Use domain agents when you need specialized expertise in a specific language, paradigm, or discipline.

---

## Common Delegation Patterns

### Code Review Workflow

```
User Request: "Review this PR"
       ↓
pensive:code-reviewer (Domain)
       ↓ delegates to →
       ├→ pensive:api-reviewer (API design)
       ├→ pensive:security-reviewer (Security)
       └→ pensive:performance-reviewer (Performance)
       ↓ uses →
sanctum:pr-agent (Foundation) for git integration
       ↓ validates with →
abstract:plugin-validator (Meta) if plugin code
```

### Plugin Development Workflow

```
User Request: "Create new skill"
       ↓
abstract:skill-generator (Meta)
       ↓ validates with →
abstract:skill-auditor (Meta) for quality
       ↓ uses →
conserve:context-optimizer (Utility) for token efficiency
       ↓ commits with →
sanctum:pr-agent (Foundation)
```

### Bloat Remediation Workflow

```
User Request: "Clean up codebase"
       ↓
conserve:bloat-auditor (Utility) - scan
       ↓ reports to user →
User approves changes
       ↓
conserve:unbloat-remediator (Utility) - execute
       ↓ uses →
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

**This is intentional design**. Agents with clear boundaries:
- ✅ Are easier to understand
- ✅ Have predictable behavior
- ✅ Can be combined reliably
- ✅ Reduce token usage (no scope creep)

---

## Agent Selection Decision Tree

```
┌─ Working on plugins themselves?
│  └─ Yes → abstract:* (Meta)
│
├─ Need git/version control?
│  └─ Yes → sanctum:* (Foundation)
│
├─ Need validation/gates?
│  └─ Yes → imbue:* (Foundation)
│
├─ Need token optimization?
│  └─ Yes → conserve:* (Utility)
│
├─ Need code generation?
│  └─ Yes → conjure:* (Utility)
│
├─ Need language-specific help?
│  ├─ Python → parseltongue:*
│  ├─ Rust → pensive:rust-auditor
│  └─ General → pensive:*
│
├─ Need architecture/design?
│  └─ Yes → pensive:architecture-reviewer, spec-kit:*
│
└─ Need documentation?
   └─ Yes → memory-palace:*, sanctum:update-docs
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
