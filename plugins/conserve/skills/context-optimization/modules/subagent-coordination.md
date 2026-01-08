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

## Critical: Subagent Overhead Reality

**Every subagent inherits ~16k+ tokens of system context** (tool definitions, permissions, system prompts) regardless of instruction length. This is the "base overhead" that makes subagents expensive for simple tasks.

### The Economics

| Task Type | Task Tokens | + Base Overhead | Total | Efficiency |
|-----------|-------------|-----------------|-------|------------|
| Simple commit | ~50 | +8,000 | 8,050 | **0.6%** ❌ |
| PR description | ~200 | +8,000 | 8,200 | **2.4%** ❌ |
| Code review | ~3,000 | +8,000 | 11,000 | **27%** ⚠️ |
| Architecture analysis | ~15,000 | +8,000 | 23,000 | **65%** ✅ |
| Multi-file refactor | ~25,000 | +8,000 | 33,000 | **76%** ✅ |

**Rule of Thumb**: If task reasoning < 2,000 tokens, parent agent should do it directly.

### Cost Comparison (Haiku vs Opus)

Even though Haiku is ~60x cheaper per token:
- Parent (Opus) doing simple commit: ~200 tokens = ~$0.009
- Subagent (Haiku) doing simple commit: ~8,700 tokens = ~$0.0065

**Marginal savings ($0.003) don't justify**:
- Latency overhead (subagent spin-up)
- Complexity cost (more failure modes)
- Opportunity cost (8k tokens could fund real reasoning)

## When to Delegate

### CRITICAL: Pre-Invocation Check

**The complexity check MUST happen BEFORE calling the Task tool.**

Once you invoke a subagent, it has already loaded ~8k+ tokens of system context.
A subagent that "bails early" still costs nearly the full overhead.

```
❌ WRONG: Invoke agent → Agent checks complexity → Agent bails → 8k tokens wasted

✅ RIGHT: Parent checks complexity → Skip invocation → 0 tokens spent
```

### Simple Task Threshold

**Before delegating, ask**: "Does this task require analysis, or just execution?"

| Task Type | Reasoning Required | Delegate? |
|-----------|-------------------|-----------|
| `git add && git commit && git push` | None | **NO** - parent does directly |
| "Classify changes and write commit" | Minimal | **NO** - parent does directly |
| "Review PR for security issues" | Substantial | **MAYBE** - if context pressure |
| "Analyze architecture and suggest refactors" | High | **YES** - benefits from fresh context |

### Pre-Invocation Checklist (Parent MUST verify)

Before calling ANY subagent via Task tool:

1. **Can I do this in one command?** → Do it directly
2. **Is the reasoning < 500 tokens?** → Do it directly
3. **Is this a "run X" request?** → Run X directly
4. **Check agent description for ⚠️ PRE-INVOCATION CHECK** → Follow it

### Delegation Triggers (Updated)

| Trigger | Threshold | Action |
|---------|-----------|--------|
| **Task reasoning** | < 2,000 tokens | ❌ Parent does directly |
| Task reasoning | > 2,000 tokens | Consider delegation |
| Context pressure | > 40% usage | Consider delegation |
| Task complexity | > 5 distinct steps | Recommend delegation |
| File operations | > 3 large files | Require delegation |
| Parallel work | Independent subtasks | Optimal for delegation |

### Decision Framework

```python
# Constants
BASE_OVERHEAD = 8000  # System context inherited by every subagent
MIN_EFFICIENCY = 0.20  # 20% minimum efficiency threshold

def should_delegate(task, context_usage):
    """
    Determine if task should be delegated to subagent.

    Key insight: Every subagent inherits ~8k tokens of system context.
    Simple tasks (git commit, file move) waste 99%+ on overhead.
    Only delegate when task reasoning justifies the base cost.
    """
    # FIRST CHECK: Is this a simple execution task?
    if task.estimated_reasoning_tokens < 500:
        return False, "Simple task - parent executes directly"

    # Calculate efficiency
    efficiency = task.estimated_reasoning_tokens / (
        task.estimated_reasoning_tokens + BASE_OVERHEAD
    )

    if efficiency < MIN_EFFICIENCY:
        return False, f"Efficiency {efficiency:.1%} below threshold - parent does it"

    # Context pressure override (delegate even if borderline efficient)
    if context_usage > 0.45:
        return True, "Context pressure requires delegation"

    # Recommended delegation for complex tasks
    if task.estimated_reasoning_tokens > 2000:
        return True, f"Substantial reasoning ({task.estimated_reasoning_tokens} tokens) justifies subagent"

    if task.is_parallelizable and len(task.subtasks) >= 3:
        return True, "Parallel subtasks can run concurrently"

    return False, "Task can be handled in current context"


def estimate_reasoning_tokens(task_description: str) -> int:
    """
    Estimate how many tokens of actual reasoning a task requires.

    Examples:
    - "git add && commit && push" → ~20 tokens (just commands)
    - "Write conventional commit for staged changes" → ~100 tokens
    - "Review PR for security issues" → ~3000 tokens
    - "Analyze architecture and propose refactors" → ~10000 tokens
    """
    # Simple heuristic based on task type
    simple_patterns = ["git add", "git commit", "git push", "mv ", "cp ", "rm "]
    if any(p in task_description.lower() for p in simple_patterns):
        return 50  # Pure execution, minimal reasoning

    analysis_patterns = ["review", "analyze", "evaluate", "assess", "audit"]
    if any(p in task_description.lower() for p in analysis_patterns):
        return 3000  # Substantial reasoning required

    creation_patterns = ["refactor", "implement", "design", "architect"]
    if any(p in task_description.lower() for p in creation_patterns):
        return 5000  # Heavy reasoning required

    return 500  # Default moderate reasoning
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
