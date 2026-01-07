---
name: context-optimization
description: |

Triggers: context, optimization
  Reduce context usage with MECW principles (keep under 50% of total window).

  Triggers: context pressure, token usage, MECW, context window, optimization,
  decomposition, workflow splitting, context management, token optimization

  Use when: context usage approaches 50% of window, tasks need decomposition,
  complex multi-step operations planned, context pressure is high

  DO NOT use when: simple single-step tasks with low context usage.
  DO NOT use when: already using mcp-code-execution for tool chains.

  Use this skill BEFORE starting complex tasks. Check context levels proactively.
category: conservation
token_budget: 150
progressive_loading: true
---
## Table of Contents

- [Quick Start](#quick-start)
- [When to Use](#when-to-use)
- [Core Hub Responsibilities](#core-hub-responsibilities)
- [Module Selection Strategy](#module-selection-strategy)
- [Context Classification](#context-classification)
- [Integration Points](#integration-points)
- [Resources](#resources)


# Context Optimization Hub



## Quick Start

### Basic Usage
\`\`\`bash
# Run the main command
python -m module_name

# Show help
python -m module_name --help
\`\`\`

**Verification**: Run with `--help` flag to confirm installation.
## When to Use



- **Automatic**: Keywords: `context`, `tokens`, `optimization`, `MECW`.

- **MECW Threshold**: When context usage approaches 50% of total window size.

- **Complex Tasks**: For tasks requiring multiple steps or analysis.



## Core Hub Responsibilities



1. Assess context pressure and MECW compliance.

2. Route to appropriate specialized modules.

3. Coordinate subagent-based workflows.

4. Manage token budget allocation across modules.

5. Synthesize results from modular execution.



## Module Selection Strategy



```python

def select_optimal_modules(context_situation, task_complexity):

    if context_situation == "CRITICAL":

        return ['mecw-assessment', 'subagent-coordination']

    elif task_complexity == 'high':

        return ['mecw-principles', 'subagent-coordination']

    else:

        return ['mecw-assessment']

```



## Context Classification



| Utilization | Status | Action |

|-------------|--------|--------|

| < 30% | LOW | Continue normally |

| 30-50% | MODERATE | Monitor, apply principles |

| > 50% | CRITICAL | Immediate optimization required |



## Integration Points



- **Token Conservation**: Receives usage strategies, returns MECW-compliant optimizations.

- **CPU/GPU Performance**: Aligns context optimization with resource constraints.

- **MCP Code Execution**: Delegates complex patterns to specialized MCP modules.



## Resources



For implementation details:



- **MECW Theory**: See `modules/mecw-principles.md` for core concepts and 50% rule.

- **Context Analysis**: See `modules/mecw-assessment.md` for risk identification.

- **Workflow Delegation**: See `modules/subagent-coordination.md` for decomposition patterns.
## Troubleshooting

### Common Issues

**Command not found**
Ensure all dependencies are installed and in PATH

**Permission errors**
Check file permissions and run with appropriate privileges

**Unexpected behavior**
Enable verbose logging with `--verbose` flag
