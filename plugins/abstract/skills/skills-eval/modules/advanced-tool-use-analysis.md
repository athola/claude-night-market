# Advanced Tool Use Analysis

Two scripts measure part of what this module covers. Run them from
`plugins/abstract`. Discovery patterns, programmatic calling and MCP
compliance have no script and are judged by reading the skill.

## Dynamic Discovery Evaluation

### Tool Discovery Patterns

`tool_performance_analyzer.py` times each executable file under a
directory by running it with `--help`. It executes what it finds:
point it only at code you trust.

```bash
python3 scripts/tool_performance_analyzer.py skills/skills-eval
```

### Discovery Optimization Targets
- **Loading Efficiency**: Minimize tool discovery latency
- **Pattern Recognition**: Tighten keyword matching and categorization
- **Contextual Loading**: Load tools based on relevance to current context
- **Memory Management**: Efficient tool caching and retrieval

## Programmatic Calling Assessment

### Calling Metrics

Review the skill's workflow steps by hand against these points:

- **Sequential Efficiency**: Order tool calls so none waits needlessly
- **Parallel Processing**: Identify concurrent tool opportunities
- **Context Preservation**: Minimize context loss between calls
- **Error Recovery**: production-grade error handling and retry mechanisms

## Context Preservation Analysis

### Context Window Utilization

`token_usage_tracker.py` estimates tokens per skill and lists the skills
over a per-skill limit (default 2000).

```bash
python3 scripts/token_usage_tracker.py skills/
python3 scripts/token_usage_tracker.py skills/ --optimal-limit 1500
```

### Optimization Strategies
- **Efficient Token Usage**: Maximize information density
- **Pollution Reduction**: Minimize irrelevant context accumulation
- **Window Management**: Strategic context window allocation
- **Compression Techniques**: Intelligent content summarization

## Performance Benchmarking

### Evaluation Criteria
- **MCP Compliance**: Validation against Model Context Protocol standards
- **Accuracy Metrics**: Tool discovery and execution accuracy improvements
- **Token Efficiency**: Usage patterns and optimization opportunities
- **Latency Analysis**: Multi-step workflow performance bottlenecks

### Target Improvements
- **Token Usage Reduction**: Aim for 37% reduction through programmatic calling optimization
- **Accuracy Improvements**: Target 25% improvement in tool discovery and execution
- **Context Optimization**: Maintain 95% context window preservation
- **Latency Reduction**: Eliminate multiple inference passes in complex workflows

## Advanced Analysis Techniques

### Comparative Analysis

No script compares a skill against a baseline or tracks it over time.
Save the JSON output of `scripts/skills_auditor.py --format json` per
release and compare the files.

### Optimization Recommendations
1. **Tool Grouping**: Related tools should be discoverable together
2. **Progressive Loading**: Load essential tools first, advanced tools later
3. **Context Caching**: Preserve relevant context between tool calls
4. **Error Patterns**: Analyze common error scenarios and fix the frequent ones
