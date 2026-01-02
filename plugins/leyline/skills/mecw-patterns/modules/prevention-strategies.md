---
name: prevention-strategies
description: Proactive strategies and best practices for preventing MECW violations and maintaining optimal context window health
category: patterns
parent_skill: leyline:mecw-patterns
estimated_tokens: 520
reusable_by: [conserve, conjure, spec-kit, sanctum, imbue]
tags: [prevention, optimization, delegation, best-practices]
---

# MECW Prevention Strategies

Proactive approaches to prevent context window issues before they occur.

## Core Prevention Strategies

### 1. Early Detection

Monitor context usage continuously rather than reactively:

```python
from leyline import MECWMonitor

monitor = MECWMonitor()

# Check at regular intervals
for operation in operations:
    status = monitor.get_status()
    if status.pressure_level in ["HIGH", "CRITICAL"]:
        # Trigger optimization before proceeding
        optimize_context()
    execute_operation(operation)
```

**Why it works**: Catching pressure increases early allows graceful optimization rather than emergency measures.

### 2. Proactive Compression

Compress content before hitting limits:

```python
# Start compression at 80% of MECW threshold (40% of total)
if monitor.current_tokens > (monitor.mecw_threshold * 0.8):
    # Proactive compression
    summarize_completed_work()
    remove_intermediate_results()
    monitor.track_usage(recalculate_tokens())
```

**Best practices**:
- Summarize completed sections as you go
- Remove redundant information immediately
- Keep only essential context for continuation

### 3. Strategic Delegation

Use subagents for complex workflows:

```python
from leyline import MECWMonitor

monitor = MECWMonitor()

if estimated_tokens > monitor.get_safe_budget():
    # Too large for current session - delegate
    result = delegate_to_subagent(task)
else:
    # Safe to handle in current session
    result = execute_directly(task)
```

**When to delegate**:
- Task estimated >40% of remaining budget
- Complex multi-step workflows
- Independent subtasks that can run in parallel
- Tasks requiring deep context that would exceed MECW

**Benefits**:
- Each subagent gets fresh context window
- Parallel execution possible
- Total capacity = N × MECW per subagent

### 4. Progressive Disclosure

Load only what's needed when needed:

```python
# Instead of loading everything upfront
safe_budget = monitor.get_safe_budget()
files_to_load = select_most_relevant_files(all_files, budget=safe_budget)

# Load in stages
for batch in batched_files:
    load_batch(batch)
    process_batch()
    summarize_results()  # Compress before next batch
```

**Techniques**:
- Load files on-demand
- Process in batches with summarization between
- Use file snippets instead of full files
- Query specific sections rather than full documents

## Best Practices by Use Case

### Code Generation (Target: 40% MECW)

```python
SAFE_BUDGET_CODE_GEN = mecw_threshold * 0.40

# Needs reasoning space for:
# - Understanding requirements
# - Planning implementation
# - Generating code
# - Self-review
```

**Practices**:
- Load only relevant code sections
- Summarize requirements before implementation
- Generate in focused modules
- Review incrementally

### Code Review (Target: 50% MECW)

```python
SAFE_BUDGET_CODE_REVIEW = mecw_threshold * 0.50

# Can use fuller context for:
# - Reading code comprehensively
# - Cross-referencing patterns
# - Identifying issues
```

**Practices**:
- Load complete relevant files
- Focus on changed code + immediate context
- Batch similar files together
- Summarize findings as you go

### Data Analysis (Target: 35% MECW)

```python
SAFE_BUDGET_DATA_ANALYSIS = mecw_threshold * 0.35

# Needs extra space for:
# - Statistical calculations
# - Data transformations
# - Result formatting
```

**Practices**:
- Load data samples, not full datasets
- Summarize statistics instead of raw data
- Use aggregations over detail
- Stream processing when possible

### Documentation (Target: 45% MECW)

```python
SAFE_BUDGET_DOCUMENTATION = mecw_threshold * 0.45

# Moderate reasoning needs:
# - Understanding codebase
# - Structuring content
# - Examples and references
```

**Practices**:
- Load code sections incrementally
- Document in focused sections
- Cross-reference without loading all files
- Generate examples from summaries

## Planning and Budgeting

### Budget Allocation Strategy

```python
def plan_budget_allocation(task_type, estimated_content):
    """Plan safe budget allocation."""

    # Target usage by task type
    targets = {
        'code_generation': 0.40,
        'code_review': 0.50,
        'data_analysis': 0.35,
        'documentation': 0.45,
        'conversation': 0.50
    }

    target_ratio = targets.get(task_type, 0.40)  # Conservative default
    safe_budget = mecw_threshold * target_ratio

    if estimated_content > safe_budget:
        return {
            'direct': False,
            'strategy': 'delegate_or_chunk',
            'budget': safe_budget,
            'overage': estimated_content - safe_budget
        }

    return {
        'direct': True,
        'strategy': 'execute_directly',
        'budget': safe_budget,
        'headroom': safe_budget - estimated_content
    }
```

### Multi-Turn Planning

```python
def plan_multi_turn_workflow(operations, avg_growth_per_turn=1000):
    """Plan workflow accounting for turn-by-turn growth."""

    current_tokens = get_current_context_size()
    projected_tokens = current_tokens

    for i, operation in enumerate(operations):
        # Project tokens after this operation
        projected_tokens += estimate_operation_tokens(operation)
        projected_tokens += avg_growth_per_turn  # Conversation overhead

        if projected_tokens > mecw_threshold:
            return {
                'can_complete': False,
                'turns_possible': i,
                'recommendation': 'split_or_optimize_after_turn_{}'.format(i)
            }

    return {
        'can_complete': True,
        'final_projected': projected_tokens,
        'headroom': mecw_threshold - projected_tokens
    }
```

## Essential Practices

### 1. Plan for 40% Usage

**Rule**: Design workflows to use ~40% of context window, leaving comfortable buffer.

```python
# Good: Targets 40%
max_input = mecw_threshold * 0.40
files = select_files_within_budget(all_files, max_input)

# Bad: Uses full MECW (50%)
max_input = mecw_threshold  # Too aggressive
```

### 2. Reserve 50% for Model Work

**Rule**: Total context window must accommodate both input and output.

Budget breakdown:
- 40% - Input content (your data)
- 10% - Conversation overhead
- 50% - Model reasoning + response

### 3. Monitor Continuously

**Rule**: Check context at each major step.

```python
# Check before major operations
status = monitor.get_status()
if status.pressure_level != "LOW":
    handle_pressure(status)

# Execute
result = perform_operation()

# Update tracking
monitor.track_usage(calculate_new_total())
```

### 4. Fail Fast

**Rule**: Abort and restructure when approaching limits.

```python
if estimated_tokens > monitor.get_safe_budget():
    # Don't try to squeeze it in
    raise NeedsDelegationError(
        f"Task requires {estimated_tokens:,} tokens, "
        f"but safe budget is {monitor.get_safe_budget():,}"
    )
```

### 5. Document Aggressively

**Rule**: Keep summaries for context recovery after reset.

```python
# Before optimization/reset
checkpoint = {
    'completed': summarize_completed_work(),
    'in_progress': current_task_state(),
    'next_steps': planned_operations(),
    'key_decisions': important_choices()
}

save_checkpoint(checkpoint)

# After reset, reload minimal context
load_essential_context(checkpoint)
```

## Anti-Patterns to Avoid

### Loading Everything Upfront

```python
# Bad: Load entire codebase
all_files = load_all_project_files()  # 150,000 tokens!
analyze(all_files)
```

**Fix**: Load incrementally
```python
# Good: Load on-demand
relevant_files = find_relevant_files(query)
for file in relevant_files[:5]:  # Top 5 most relevant
    analyze_file(file)
```

### Ignoring Growth Trends

```python
# Bad: No monitoring
for i in range(100):
    execute_operation(i)  # Context grows unchecked
```

**Fix**: Monitor and optimize
```python
# Good: Continuous monitoring
for i in range(100):
    if i % 10 == 0:
        status = monitor.get_status()
        if status.pressure_level == "HIGH":
            optimize_context()
    execute_operation(i)
```

### Reactive Optimization

```python
# Bad: Wait for problems
try:
    execute_all()
except ContextOverflowError:
    # Too late
    optimize()
```

**Fix**: Proactive management
```python
# Good: Prevent problems
if monitor.current_tokens > mecw_threshold * 0.80:
    optimize_before_continuing()
execute_safely()
```

### Skipping Subagent Delegation

```python
# Bad: Try to handle everything in one session
process_all_1000_files()  # Will hit MECW
```

**Fix**: Use subagents
```python
# Good: Delegate large tasks
batches = chunk_files_into_mecw_batches(all_files)
results = [process_batch_in_subagent(batch) for batch in batches]
final_result = synthesize_results(results)
```

## Integration Examples

### With Conjure Delegation

```python
from leyline import MECWMonitor
from conjure import delegate_to_model

monitor = MECWMonitor()

if estimated_tokens > monitor.get_safe_budget():
    # Delegate to fresh model instance
    result = delegate_to_model(
        task=task,
        model="gemini-2.0-flash-thinking-exp"
    )
else:
    result = execute_directly(task)
```

### With Conservation Optimization

```python
from leyline import MECWMonitor
from conserve import optimize_skill_loading

monitor = MECWMonitor()
status = monitor.get_status()

if status.pressure_level in ["HIGH", "CRITICAL"]:
    # Use conserve patterns to optimize
    optimize_skill_loading(
        load_only_essential=True,
        compress_examples=True
    )
```

### With Spec-Kit Planning

```python
from leyline import MECWMonitor
from spec_kit import estimate_implementation_tokens

monitor = MECWMonitor()
plan_tokens = estimate_implementation_tokens(specification)

if plan_tokens > monitor.get_safe_budget():
    # Split plan into phases
    phases = split_implementation_by_mecw(specification)
else:
    # Can execute plan directly
    execute_implementation(specification)
```

## Summary

Effective MECW prevention requires:

1. **Planning**: Budget for 40% usage before starting
2. **Monitoring**: Check continuously, not reactively
3. **Compression**: Optimize proactively at 80% of threshold
4. **Delegation**: Use subagents when tasks exceed budget
5. **Progressive Loading**: Load only what's needed, when needed

Following these practices prevents hallucinations and maintains high-quality outputs throughout long sessions.
