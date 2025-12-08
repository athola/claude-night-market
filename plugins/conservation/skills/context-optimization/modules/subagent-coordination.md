---
name: subagent-coordination
description: |
  Workflow decomposition and subagent delegation patterns for
  managing context-heavy operations.
category: conservation
---

# Subagent Coordination Module

## Overview

This module provides patterns for decomposing complex workflows and delegating to subagents to maintain MECW compliance.

## When to Delegate

### Delegation Triggers

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Context pressure | > 40% usage | Consider delegation |
| Task complexity | > 5 distinct steps | Recommend delegation |
| File operations | > 3 large files | Require delegation |
| Parallel work | Independent subtasks | Optimal for delegation |

### Decision Framework

```python
def should_delegate(task, context_usage):
    """
    Determine if task should be delegated to subagent.
    """
    # Mandatory delegation
    if context_usage > 0.45:
        return True, "Context pressure requires delegation"

    # Recommended delegation
    if task.estimated_tokens > 10000:
        return True, "Large task benefits from fresh context"

    if task.is_parallelizable and len(task.subtasks) >= 3:
        return True, "Parallel subtasks can run concurrently"

    return False, "Task can be handled in current context"
```

## Workflow Decomposition

### Breaking Down Complex Tasks

```python
def decompose_workflow(task):
    """
    Break complex task into delegatable units.
    """
    subtasks = []

    # Identify independent components
    for component in task.components:
        if component.has_no_dependencies():
            subtasks.append({
                'type': 'parallel',
                'component': component,
                'can_run_concurrently': True
            })
        else:
            subtasks.append({
                'type': 'sequential',
                'component': component,
                'dependencies': component.dependencies
            })

    return subtasks
```

### Task Packaging

When delegating to a subagent, package:
1. **Clear objective**: What the subagent should accomplish
2. **Required context**: Minimal context needed for the task
3. **Expected output**: Format and content of results
4. **Constraints**: Time limits, resource bounds, quality requirements

## Subagent Patterns

### Pattern 1: Parallel Exploration

```python
# Launch multiple subagents for independent searches
subagents = [
    Task(subagent_type="Explore", prompt="Find auth implementations"),
    Task(subagent_type="Explore", prompt="Find database models"),
    Task(subagent_type="Explore", prompt="Find API endpoints"),
]
# All run concurrently with fresh context each
```

### Pattern 2: Sequential Pipeline

```python
# Chain subagents where each builds on previous
def sequential_pipeline(tasks):
    context = {}
    for task in tasks:
        result = delegate_to_subagent(task, context)
        context.update(result.summary)  # Pass only summary
    return context
```

### Pattern 3: Map-Reduce

```python
# Split large operation, process in parallel, combine results
def map_reduce(files, operation):
    # Map phase: delegate each file to subagent
    results = parallel_delegate([
        {'file': f, 'operation': operation}
        for f in files
    ])

    # Reduce phase: synthesize results
    return synthesize_results(results)
```

## Execution Coordination

### Managing Subagent State

```python
class SubagentCoordinator:
    def __init__(self):
        self.active_subagents = []
        self.results = {}

    def dispatch(self, task_spec):
        """Dispatch task to subagent."""
        subagent_id = launch_subagent(task_spec)
        self.active_subagents.append(subagent_id)
        return subagent_id

    def collect_results(self):
        """Collect and synthesize subagent results."""
        for subagent_id in self.active_subagents:
            self.results[subagent_id] = get_subagent_result(subagent_id)
        return self.synthesize()

    def synthesize(self):
        """Combine results from all subagents."""
        return {
            'status': 'completed',
            'results': list(self.results.values()),
            'summary': create_summary(self.results)
        }
```

## Result Synthesis

### Combining Subagent Output

1. **Extract key findings**: Pull essential information from each result
2. **Resolve conflicts**: Handle contradictory findings
3. **Build coherent summary**: Create unified view for parent context
4. **Preserve references**: Keep pointers to detailed results if needed

### Synthesis Patterns

```python
def synthesize_exploration_results(results):
    """
    Combine results from parallel exploration subagents.
    """
    synthesis = {
        'files_found': [],
        'patterns_identified': [],
        'recommendations': []
    }

    for result in results:
        synthesis['files_found'].extend(result.get('files', []))
        synthesis['patterns_identified'].extend(result.get('patterns', []))
        synthesis['recommendations'].extend(result.get('recommendations', []))

    # Deduplicate and prioritize
    synthesis['files_found'] = list(set(synthesis['files_found']))
    synthesis['recommendations'] = prioritize(synthesis['recommendations'])

    return synthesis
```

## Best Practices

1. **Minimize handoff context**: Pass only essential information
2. **Define clear boundaries**: Each subagent has specific scope
3. **Plan for failures**: Handle subagent errors gracefully
4. **Summarize aggressively**: Keep only key results
5. **Parallelize when possible**: Use concurrent execution for speed

## Integration

- **Principles**: Follows MECW limits from `mecw-principles`
- **Assessment**: Triggered by risk detection in `mecw-assessment`
- **MCP**: Works with `mcp-code-execution` for code-heavy tasks
