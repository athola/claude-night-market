# Claude Night Market

**Claude Code plugins for software engineering workflows.**

This repository adds 16 plugins to Claude Code to standardize git operations, code review, spec-driven development, and issue management. While each plugin functions independently, they share testing and debugging patterns to maintain consistent behavior across workflows.

## Key Features

**Governance & Quality**
Hooks adapt context based on the active agent, while `pensive` tracks usage frequency and failure rates. `imbue` enforces the Iron Law TDD cycle via a PreToolUse hook that checks for test files before allowing implementation writes. For complex tasks, `imbue:rigorous-reasoning` mandates a step-by-step logic check.

**Security & Session Management**
`leyline` manages OAuth flows for GitHub, GitLab, and AWS with token caching. `conserve` automates permission handling by approving safe commands (like `ls`) and blocking risky ones (`rm -rf /`). `sanctum` isolates named sessions for debugging, feature work, and PR reviews. To maintain quality, `/create-skill` and `/create-command` abort if no failing tests exist.

**Resilience & Collaboration**
The system includes self-correction mechanisms: `/update-plugins` recommends updates based on stability, and `/fix-workflow` attempts to repair failed runs. For strategic decisions, `/attune:war-room` uses reversibility scoring (Type 1/2 framework) to route decisions to appropriate expert panels.

## Workflow Improvements

Commands automate multi-step processes to reduce manual overhead. `/prepare-pr` validates branch scope, runs linting, and verifies a clean state before creating a pull request, while `/full-review` audits syntax, logic, and security in a single pass. `/speckit-specify` enforces a written specification phase before code generation. To keep the agent in sync, `/catchup` reads recent git history to update the context window, and `/attune:init` detects project types (Python, Node) to scaffold necessary configuration files.

## Quick Start

### Option 1: Claude Code Plugin Commands

```bash
# 1. Add the marketplace
/plugin marketplace add athola/claude-night-market

# 2. Install plugins you need
/plugin install sanctum@claude-night-market    # Git workflows
/plugin install pensive@claude-night-market    # Code review
/plugin install spec-kit@claude-night-market   # Spec-driven dev

# 3. Start using
/prepare-pr                                    # Prepare a pull request
/full-review                                   # Run code review
Skill(sanctum:git-workspace-review)            # Invoke a skill (if Skill tool available)
```

### Option 2: npx skills

```bash
# Install the entire marketplace
npx skills add athola/claude-night-market

# Or install specific plugins
npx skills add athola/claude-night-market/sanctum    # Git workflows
npx skills add athola/claude-night-market/pensive    # Code review
npx skills add athola/claude-night-market/conserve   # Resource optimization
```

### Post-Installation Setup (Claude Code 2.1.10+)

After installation, initialize plugins with Setup hooks:

```bash
# Run one-time initialization
claude --init

# Periodic maintenance (weekly recommended)
claude --maintenance
```

> **Note:** If the `Skill` tool is unavailable, read skill files directly: `Read plugins/{plugin}/skills/{skill-name}/SKILL.md` and follow the instructions.

**Next steps:** See [Installation Guide](book/src/getting-started/installation.md) for recommended plugin sets and troubleshooting.

## What's Included

**16 plugins** organized in layers, each building on foundations below:

```mermaid
flowchart TB
    classDef domainClass fill:#e8f4f8,stroke:#2980b9,stroke-width:2px,color:#2c3e50
    classDef utilityClass fill:#f8f4e8,stroke:#f39c12,stroke-width:2px,color:#2c3e50
    classDef foundationClass fill:#f4e8f8,stroke:#8e44ad,stroke-width:2px,color:#2c3e50
    classDef metaClass fill:#e8f4e8,stroke:#27ae60,stroke-width:2px,color:#2c3e50

    subgraph Domain["Domain Specialists"]
        direction LR
        D1[archetypes]:::domainClass
        D2[pensive]:::domainClass
        D3[parseltongue]:::domainClass
        D4[memory-palace]:::domainClass
        D5[spec-kit]:::domainClass
        D6[minister]:::domainClass
        D7[attune]:::domainClass
        D8[scry]:::domainClass
        D9[scribe]:::domainClass
    end

    subgraph Utility["Utility Layer"]
        direction LR
        U1[conserve]:::utilityClass
        U2[conjure]:::utilityClass
        U3[hookify]:::utilityClass
    end

    subgraph Foundation["Foundation Layer"]
        direction LR
        F1[imbue]:::foundationClass
        F2[sanctum]:::foundationClass
        F3[leyline]:::foundationClass
    end

    subgraph Meta["Meta Layer"]
        direction LR
        M1[abstract]:::metaClass
    end

    Domain ==> Utility ==> Foundation ==> Meta
```

### Highlights

*   **sanctum**: Git operations (`/prepare-pr`, `/do-issue`), documentation, and session management.
*   **pensive**: Code reviews (`/full-review`) and audits.
*   **spec-kit**: Requirements definition (`/speckit-specify`).
*   **minister**: GitHub issues (`/create-issue`, `/close-issue`).
*   **conserve**: Codebase bloat reduction (`/bloat-scan`).
*   **attune**: Project scaffolding (`/attune:init`), War Room with reversibility routing (`/attune:war-room`).
*   **parseltongue**: Python tools (`/analyze-tests`).
*   **archetypes**: Architecture guides.
*   **memory-palace**: Knowledge indexing (`/palace`).
*   **scribe**: Documentation review and AI slop detection (`/slop-scan`, `/doc-verify`).
*   **hookify**: Behavioral rules without configuration.
*   **leyline**: Foundation utilities (quota tracking, token estimation, authentication).
*   **imbue**: Review methodologies, Iron Law TDD enforcement via hooks, anti-cargo-cult verification.

See [Capabilities Reference](book/src/reference/capabilities-reference.md) for the full list of 123 skills, 109 commands, and 40 agents.

## Audience

Developers use these plugins to automate CLI tasks and enforce consistency in Claude Code sessions. Teams use them to standardize LLM interactions.

## Common Workflows

See [**Common Workflows Guide**](book/src/getting-started/common-workflows.md) for execution details.

| Workflow | Command | Example |
|----------|-------------|---------|
| Initialize project | `/attune:arch-init` | `attune:arch-init --name my-api` |
| Review a PR | `/full-review` | Run multi-discipline code review |
| Architecture review | `/fpf-review` | FPF (Functional/Practical/Foundation) analysis |
| Fix PR feedback | `/fix-pr` | Address review comments |
| Implement issues | `/do-issue` | Progressive issue resolution with TDD |
| Fix workflow issues | `/fix-workflow` | Self-correcting with Reflexion |
| Prepare a PR | `/prepare-pr` | Quality gates before merge |
| Create GitHub issue | `/create-issue` | Interactive issue creation |
| Manage labels | `/update-labels` | GitHub label taxonomy |
| Catch up on changes | `/catchup` | Context recovery |
| Write specifications | `/speckit-specify` | Spec-driven development |
| Debug issues | `Skill(superpowers:debugging)` | Root cause analysis |
| Improve plugins | `/update-plugins` | Update based on stability metrics |
| Strategic decisions | `/attune:war-room` | Reversibility-based expert routing |

## Demos

### Skills Showcase

![Skills Showcase Demo](assets/gifs/skills-showcase.gif)

This 90-second tutorial demonstrates how to browse skills, examine their frontmatter, and chain them into workflows.

[Full Tutorial](docs/tutorials/skills-showcase.md)

---

## Documentation

*   [**Getting Started**](book/src/getting-started/README.md): Installation and setup.
*   [**Plugin Catalog**](book/src/plugins/README.md): Documentation for each plugin.
*   [**Capabilities Reference**](book/src/reference/capabilities-reference.md): List of all skills and commands.
*   [**Tutorials**](book/src/tutorials/README.md): Guides for specific tasks.
*   [**Advanced Guides**](docs/guides/README.md): Deep dives into architecture and patterns.

## LSP Integration

LSP (Language Server Protocol) support is available in Claude Code v2.0.74+. It enables faster symbol search (~50ms) compared to text search (~45s).

**Setup:**

1.  Enable LSP in `~/.claude/settings.json`:
    ```json
    { "env": { "ENABLE_LSP_TOOL": "1" } }
    ```
2.  Install language servers (e.g., `npm install -g pyright`).
3.  Install LSP plugins:
    ```bash
    /plugin install pyright-lsp@claude-plugins-official
    ```

See [LSP Native Support Guide](docs/guides/lsp-native-support.md) for details.

## Extending Night Market

To create a new plugin:

```bash
make create-plugin NAME=my-plugin
make validate
make lint && make test
```

Refer to the [Plugin Development Guide](docs/plugin-development-guide.md) for architectural patterns.

## Prompt Context Usage

The ecosystem adds ~14.8k characters to the system prompt (limit: 15k), enforced by a pre-commit hook.

## Architecture

Plugins are modular, load progressively to save tokens, and emphasize specifications before coding.

## Contributing

See the [Plugin Development Guide](docs/plugin-development-guide.md) for guidelines. Each plugin maintains its own tests and documentation.

## License

[MIT](LICENSE)
