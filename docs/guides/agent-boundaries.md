# Agent Boundaries & Entry Points

This reference details agent selection, relationships, and the boundaries between different specialized sub-agents in the ecosystem.

## Entry Point Agents

Primary entry points for common workflows:

1. **`abstract:plugin-validator`**: Use this to validate plugin structure before making changes.
2. **`pensive:code-reviewer`**: Use this for reviewing code changes and analyzing logic.
3. **`sanctum:pr-agent`**: Use this to prepare pull requests and manage git operations.

Specialized agents build on these foundations for advanced workflows.

## Agent Layers

The ecosystem organizes agents into four layers. Higher-layer agents delegate to lower-layer agents, while lower layers operate independently of higher-level context.

- **Domain Layer**: Specialized tasks for specific languages or paradigms (e.g., `pensive`, `parseltongue`).
- **Utility Layer**: Cross-cutting infrastructure like performance optimization and boilerplate generation (e.g., `conserve`, `conjure`).
- **Foundation Layer**: Core workflows including version control and validation gates (e.g., `imbue`, `sanctum`).
- **Meta Layer**: Tools for developing and validating the plugin ecosystem itself (e.g., `abstract`).

## Agent Responsibilities

### Meta Layer (Plugin Development)

| Agent | When To Use | Boundary |
|-------|-------------|----------|
| `abstract:plugin-validator` | Validate plugin structure before commits | Structure validation only; no business logic analysis. |
| `abstract:skill-auditor` | Audit skill quality and token efficiency | Quality metrics and token usage; no functional testing. |

### Foundation Layer (Core Workflows)

| Agent | When To Use | Boundary |
|-------|-------------|----------|
| `sanctum:pr-agent` | Prepare pull requests and commit messages | Git workflows; no code quality or logic review. |
| `imbue:proof-evaluator` | Validate proof-of-work requirements | Verification of requirements; no code implementation. |
| `leyline:dependency-mapper` | Map plugin dependencies | Dependency analysis; no automated refactoring. |

### Utility Layer (Optimization & Generation)

| Agent | When To Use | Boundary |
|-------|-------------|----------|
| `conserve:context-optimizer` | Assess MECW and token usage | Token analysis; no code-level optimization. |
| `conserve:bloat-auditor` | Detect codebase bloat | Detection of redundant files; no deletion decisions. |
| `conserve:unbloat-remediator` | Execute bloat removal | Execution of safe deletions; no architectural changes. |
| `conjure:generator` | Generate boilerplate code | Template-based generation; no business logic. |
| `hookify:rule-compiler` | Compile hook rules | Hook rule generation; no hook implementation logic. |

### Domain Layer (Specialized Tasks)

| Agent | When To Use | Boundary |
|-------|-------------|----------|
| `pensive:code-reviewer` | Multi-discipline code review | Analysis of API, architecture, and security; no fixes. |
| `pensive:architecture-reviewer` | Architecture design review | Pattern analysis; no implementation work. |
| `pensive:rust-auditor` | Rust-specific code review | Rust idioms and safety; restricted to Rust. |
| `parseltongue:python-tester` | Python test generation | Test case generation; restricted to Python. |
| `parseltongue:pytest-analyst` | Pytest output analysis | Test diagnostics; no code fixes. |
| `memory-palace:curator` | Knowledge management | Documentation organization; no code changes. |
| `spec-kit:spec-writer` | Write specifications | Requirements gathering; no implementation. |

## Delegation Patterns

### Code Review Workflow

A request to review a PR starts with `pensive:code-reviewer`. It delegates specialized tasks to `pensive:api-reviewer`, `pensive:security-reviewer`, and `pensive:performance-reviewer`. It uses `sanctum:pr-agent` for git integration and `abstract:plugin-validator` if the changes involve plugin infrastructure.

### Plugin Development Workflow

Creating a new skill uses `abstract:skill-generator`. It validates the draft with `abstract:skill-auditor`, checks token efficiency with `conserve:context-optimizer`, and stages the commit via `sanctum:pr-agent`.

### Bloat Remediation Workflow

Cleaning the codebase begins with a scan from `conserve:bloat-auditor`. After user approval, `conserve:unbloat-remediator` executes the deletions and uses `sanctum:pr-agent` to commit the changes.

## Boundary Enforcement

Agents redirect requests that fall outside their scope to ensure predictable behavior and minimize token waste.

- **Logic vs. Structure**: `abstract:plugin-validator` redirects logic fix requests to `pensive:code-reviewer`.
- **Git vs. Review**: `pensive:code-reviewer` redirects commit requests to `sanctum:pr-agent`.
- **Remediation vs. Detection**: `conserve:bloat-auditor` redirects deletion requests to `conserve:unbloat-remediator`.

This separation allows each agent to operate with a smaller, more relevant context, reducing the risk of conflicting instructions and lowering the token cost per operation.

## Agent Selection

- **Working on plugins**: Use `abstract:*` (Meta).
- **Git or version control**: Use `sanctum:*` (Foundation).
- **Validation or quality gates**: Use `imbue:*` (Foundation).
- **Token optimization or bloat detection**: Use `conserve:*` (Utility).
- **Code generation**: Use `conjure:*` (Utility).
- **Python-specific tasks**: Use `parseltongue:*` (Domain).
- **Rust-specific tasks**: Use `pensive:rust-auditor` (Domain).
- **Architecture or design review**: Use `pensive:architecture-reviewer` or `spec-kit:*` (Domain).
- **Documentation or knowledge management**: Use `memory-palace:*` or `sanctum:update-docs`.

## FAQ

**Why are agents specialized?**
Specialized agents use smaller context windows, which reduces token consumption and improves reliability. A single agent handling all domains would require a larger, more expensive system prompt and would be more prone to inconsistent behavior when faced with competing goals.

**How is delegation handled?**
Higher-layer agents call lower-layer agents to perform sub-tasks. This hierarchical structure prevents circular dependencies and maintains clear separation of concerns.

**What happens if I select the wrong agent?**
The agent will identify that the request is out of scope and recommend the appropriate agent for the task.

## Related Documentation

- [Plugin Development Guide](../plugin-development-guide.md)
- [Capabilities Reference](../../book/src/reference/capabilities-reference.md)
- [Conservation Guide](../../plugins/conserve/README.md)
