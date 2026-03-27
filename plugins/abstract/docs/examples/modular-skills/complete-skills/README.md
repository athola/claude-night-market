# Modular Skills: Development Workflow Example

This directory demonstrates the hub-and-spoke pattern
for skill organization using a development workflow
as the concrete example.

## Structure

```
complete-skills/
├── development-workflow/
│   ├── SKILL.md              # Hub (45 tokens)
│   └── modules/
│       ├── git-workflow.md
│       ├── testing-strategies.md
│       ├── code-review.md
│       ├── documentation-guidelines.md
│       └── deployment-procedures.md
└── README.md
```

## Why Modular?

A monolithic skill (850+ tokens, all topics in one file)
forces loading everything for any operation.
The modular equivalent splits into a 45-token hub
plus ~120-token focused modules, yielding:

- **Single-topic lookup**: 165 tokens (81% reduction)
- **Typical workflow**: 510 tokens (40% reduction)
- **Full load**: 645 tokens (24% reduction)

## How It Works

The hub skill (`development-workflow/SKILL.md`) lists
available modules and their purposes.
Each module covers one topic and works independently.

To use: load the hub, then load only the modules
relevant to your current task.

## Key Takeaways

1. Hub-and-spoke gives 60-80% token savings for common ops
2. Each module has a single responsibility
3. Modules can be used independently across contexts
4. Team members can own different modules
