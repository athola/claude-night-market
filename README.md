# Claude Night Market

**Claude Code plugins for software engineering workflows.**

This repository adds 15 plugins to Claude Code for git operations, code review, spec-driven development, and issue management. These plugins work independently but share a common set of patterns for testing and debugging.

## Key Features

*   **Agent-Aware Context:** Hooks (v2.1.2+) adapt context to the active agent.
*   **Skill Metrics:** The `pensive` plugin tracks usage and stability for `/skill-review` analysis.
*   **Proof-of-Work TDD:** The `imbue` plugin mandates a failing test before accepting implementation code.
*   **Test Enforcement:** `/create-skill` and `/create-command` block implementation until a failing test exists.
*   **Self-Correction:** `/update-plugins` suggests improvements based on skill stability; `/fix-workflow` attempts to repair failed workflows; `workflow-monitor` creates issues for detected inefficiencies.

## Workflow Improvements

Specialized commands replace manual steps:

*   **Git:** `/prepare-pr` validates branch scope and checks before creation.
*   **Reviews:** `/full-review` performs a multi-step audit (syntax, logic, security).
*   **Specs:** `/speckit-specify` creates detailed specifications before coding.
*   **Context:** `/catchup` summarizes recent changes to restore context.
*   **Setup:** `/attune:init` scaffolds projects based on detected types.

## Quick Start

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

> **Note:** If the `Skill` tool is unavailable, read skill files directly: `Read plugins/{plugin}/skills/{skill-name}/SKILL.md` and follow the instructions.

**Next steps:** See [Installation Guide](book/src/getting-started/installation.md) for recommended plugin sets and troubleshooting.

## What's Included

**15 plugins** organized in layers, each building on foundations below:

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

The ecosystem covers several domains:

*   **sanctum** handles git operations (`/prepare-pr`, `/commit-msg`, `/do-issue`) and documentation updates.
*   **pensive** manages code reviews (`/full-review`, `/fpf-review`) and audits shell usage.
*   **spec-kit** defines requirements (`/speckit-specify`) before implementation.
*   **minister** interfaces with GitHub issues (`/create-issue`, `/close-issue`, `/update-labels`).
*   **conserve** detects and reduces codebase bloat (`/bloat-scan`, `/unbloat`).
*   **attune** scaffolds new projects (`/attune:init`).
*   **parseltongue** provides Python-specific tools like test analysis (`/analyze-tests`).
*   **archetypes** offers architecture guides.
*   **memory-palace** indexes project knowledge (`/palace`, `/garden`).
*   **hookify** applies behavioral rules without configuration.

See [Capabilities Reference](book/src/reference/capabilities-reference.md) for the full list of 107 skills, 90 commands, and 35 agents.

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

The ecosystem adds ~14.8k characters to the system prompt (limit: 15k). A pre-commit hook enforces this limit.

## Architecture

Plugins are modular and have minimal dependencies. They load progressively to minimize token usage. The workflow emphasizes writing specifications before writing code.

## Contributing

See [CONTRIBUTING](docs/plugin-development-guide.md#contributing) for guidelines. Each plugin maintains its own tests and documentation.

## License

[MIT](LICENSE)
