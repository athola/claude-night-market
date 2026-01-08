---
name: mcp-subagents
description: Create focused, single-purpose subagents for complex workflow
  decomposition with MECW compliance.
location: plugin
token_budget: 150  # Optimized subagent coordination
progressive_loading: true
dependencies:
  hub: [mcp-code-execution]
  modules: []
---

# MCP Subagents Module

## Quick Start
Decompose complex workflows into focused subagents that operate
within MECW limits.

## Critical: Base Overhead Reality

**Every subagent inherits ~8-16k tokens of system context** (tool definitions,
permissions, system prompts) regardless of your instruction length.

### The Efficiency Formula

```
Efficiency = Task_Reasoning_Tokens / (Task_Reasoning_Tokens + Base_Overhead)
```

| Task Reasoning | + Overhead (~8k) | Efficiency | Verdict |
|---------------|------------------|------------|---------|
| 50 tokens | 8,050 | **0.6%** | ❌ Parent does it |
| 500 tokens | 8,500 | **5.9%** | ❌ Parent does it |
| 2,000 tokens | 10,000 | **20%** | ⚠️ Borderline |
| 5,000 tokens | 13,000 | **38%** | ✅ Use subagent |
| 15,000 tokens | 23,000 | **65%** | ✅ Definitely use |

**Minimum threshold**: Task should require **>2,000 tokens of reasoning** to justify subagent overhead.

## CRITICAL: Check BEFORE Invoking

**The complexity check MUST happen BEFORE calling the Task tool.**

```
❌ WRONG: Invoke subagent → Subagent bails → 8k tokens wasted
✅ RIGHT: Parent checks → Skip invocation → 0 tokens spent
```

### Pre-Invocation Checklist

Before ANY Task invocation:
1. Can I do this in one command? → Do it directly
2. Is reasoning < 500 tokens? → Do it directly
3. Check agent's ⚠️ PRE-INVOCATION CHECK in description → Follow it

## When to Use
- **Automatic**: Keywords: `subagent`, `decompose`, `break down`, `modular`
- **Complex Workflows**: Multi-step processes requiring specialization
- **MECW Pressure**: When single approach would exceed 50% context rule
- **Task Specialization**: Different phases require different expertise
- **NOT for simple tasks**: Parent should execute directly if reasoning < 2k tokens

## Required TodoWrite Items
1. `mcp-subagents:analyze-complexity`
2. `mcp-subagents:create-subagents`
3. `mcp-subagents:coordinate-execution`
4. `mcp-subagents:synthesize-results`

## Subagent Design Principles

### MECW-Compliant Subagent Structure
```python
class FocusedSubagent:
    def __init__(self, purpose, max_tokens=125):
        self.purpose = purpose
        self.max_tokens = max_tokens  # Strict MECW compliance
        self.progress_file = f"/tmp/subagents/{purpose}.json"

    def execute_focused_task(self, task_input):
        # Work within strict MECW token budget
        result = self.process(task_input, max_tokens=self.max_tokens)

        # Store externally for later synthesis
        self.store_externally(result)

        # Return only essential summary
        return {
            "status": "completed",
            "tokens_used": estimate_tokens(result),
            "summary": summarize_result(result),
            "external_location": self.progress_file
        }
```

## Step 1 – Analyze Complexity (`mcp-subagents:analyze-complexity`)

### Workflow Decomposition Strategy
```python
def analyze_for_subagent_breakdown(workflow):
    """Determine optimal subagent decomposition"""

    complexity_factors = {
        'tool_chain_length': len(workflow.tool_chain),
        'data_volume': workflow.data_size,
        'context_pressure': estimate_context_usage(),
        'task_diversity': count_distinct_task_types(workflow)
    }

    if complexity_factors['tool_chain_length'] > 3:
        return {
            'strategy': 'sequential_subagents',
            'subagent_count': complexity_factors['tool_chain_length'],
            'coordination_pattern': 'pipeline'
        }
    elif complexity_factors['task_diversity'] > 2:
        return {
            'strategy': 'specialized_subagents',
            'subagent_count': complexity_factors['task_diversity'],
            'coordination_pattern': 'parallel'
        }
    else:
        return {
            'strategy': 'single_optimized',
            'subagent_count': 1,
            'coordination_pattern': 'direct'
        }
```

## Step 2 – Create Subagents (`mcp-subagents:create-subagents`)

### Subagent Factory Patterns

#### Data Processing Subagent
```python
class DataProcessingSubagent(FocusedSubagent):
    def __init__(self, data_type):
        super().__init__(
            purpose=f"data_processing_{data_type}",
            max_tokens=200  # MECW-compliant for data tasks
        )
        self.data_type = data_type

    def process_data_in_mecw_chunks(self, data_source):
        # Process data in chunks that fit MECW limits
        chunks = self.chunk_for_mecw(data_source)

        for chunk in chunks:
            if estimate_context_usage(chunk) > self.max_tokens * 0.8:
                # Create sub-subagent for this chunk
                self.delegate_to_subsubagent(chunk)
            else:
                result = self.process_chunk(chunk)
                self.store_chunk_result(result)

        return self.synthesize_external_results()
```

#### Analysis Subagent
```python
class AnalysisSubagent(FocusedSubagent):
    def __init__(self, analysis_type):
        super().__init__(
            purpose=f"analysis_{analysis_type}",
            max_tokens=150  # Conservative for complex analysis
        )
        self.analysis_type = analysis_type

    def break_analysis_steps(self, data_source):
        # Decompose analysis into MECW-compliant steps
        steps = self.plan_analysis_steps(data_source)

        for step_id, step in enumerate(steps):
            if self.estimate_step_context(step) > self.max_tokens:
                # Emergency: create sub-subagent
                self.perform_emergency_decomposition(step, step_id)
            else:
                result = self.execute_analysis_step(step)
                self.store_step_result(step_id, result)

        return self.create_analysis_summary()
```

## Step 3 – Coordinate Execution (`mcp-subagents:coordinate-execution`)

### Subagent Orchestration Patterns

#### Pipeline Coordination
```python
def coordinate_pipeline_subagents(subagents, input_data):
    """Execute subagents in sequence with MECW monitoring"""

    current_data = input_data
    results = []

    for subagent in subagents:
        # Monitor context before each subagent
        if estimate_context_usage() > get_mecw_limit() * 0.8:
            apply_emergency_compaction()

        # Execute subagent with minimal context
        subagent_result = subagent.execute_focused_task({
            'data': current_data,
            'context_limit': get_mecw_limit() * 0.4
        })

        current_data = subagent_result.get('next_input', current_data)
        results.append(subagent_result)

        # Store intermediate results externally
        store_intermediate_result(subagent.purpose, subagent_result)

    return results
```

#### Parallel Coordination
```python
def coordinate_parallel_subagents(subagents, input_data):
    """Execute multiple subagents simultaneously"""

    # Split input data for parallel processing
    data_splits = split_input_for_parallel(input_data, len(subagents))

    # Launch subagents with minimal context
    futures = []
    for subagent, data_split in zip(subagents, data_splits):
        future = subagent.execute_async({
            'data': data_split,
            'context_limit': get_mecw_limit() // len(subagents)
        })
        futures.append(future)

    # Collect results with external storage
    results = []
    for future in futures:
        result = future.get_result()
        store_external_result(result.subagent_id, result.data)
        results.append(result)

    return synthesize_parallel_results(results)
```

## Step 4 – Synthesize Results (`mcp-subagents:synthesize-results`)

### External Result Synthesis
```python
def synthesize_subagent_results(subagent_results):
    """Combine results from external storage"""

    # Load all external results
    all_data = []
    for result in subagent_results:
        if result.external_location:
            external_data = load_external_result(result.external_location)
            all_data.append(external_data)

    # Synthesize within MECW limits
    synthesis_budget = get_mecw_limit() * 0.3
    synthesized = synthesize_with_token_limit(all_data, synthesis_budget)

    return {
        'status': 'synthesized',
        'summary': synthesized.summary,
        'detailed_results': synthesized.external_reference,
        'token_efficiency': calculate_subagent_efficiency(subagent_results),
        'mecw_compliance': verify_mecw_rules(all_data)
    }
```

## MECW Compliance Features

### Token Budget Enforcement
- Each subagent operates within strict token limits
- Dynamic budget allocation based on task complexity
- Emergency decomposition when limits exceeded

### Context Pressure Monitoring
- Real-time context usage tracking
- Proactive subagent splitting when pressure increases
- External state management for intermediate results

### Hallucination Prevention
- Focused task scope reduces hallucination risk
- External result storage preserves accuracy
- Validation at each synthesis step

## Success Metrics
- **Subagent Efficiency**: >90% of subagents complete within token budget
- **MECW Compliance**: 100% adherence to 50% context rule
- **Decomposition Quality**: <5% need for emergency re-decomposition
- **Synthesis Accuracy**: >95% preservation of original insights
