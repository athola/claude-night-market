# Run Profiler Command

## Usage

Profiles Python code for performance bottlenecks using cProfile, memory_profiler, or py-spy.

### Basic Usage
```
/run-profiler script.py
```
Runs CPU profiling on the specified script.

### With Options
```
/run-profiler --memory script.py
/run-profiler --line function_name script.py
```

## What It Does

1. **CPU Profiling**: Identifies time-consuming functions
2. **Memory Profiling**: Tracks memory allocations and leaks
3. **Line Profiling**: Profile specific functions line-by-line
4. **Flamegraph Generation**: Visual representation of call stacks
5. **Recommendations**: Suggests optimization patterns

## Profiling Modes

### CPU Mode (default)
```bash
/run-profiler script.py
```
Uses cProfile to identify slow functions.

### Memory Mode
```bash
/run-profiler --memory script.py
```
Uses memory_profiler to track allocations.

### Line Mode
```bash
/run-profiler --line expensive_function script.py
```
Uses line_profiler for detailed analysis.

### Production Mode
```bash
/run-profiler --pid 12345
```
Uses py-spy for profiling running processes.

## Output Format

- **Top Functions**: Ranked by cumulative time
- **Memory Usage**: Peak and average consumption
- **Hotspots**: Specific lines causing issues
- **Recommendations**: Optimization suggestions

## Examples

```bash
# Profile with top 20 functions
/run-profiler --top 20 main.py

# Generate flamegraph
/run-profiler --flamegraph output.svg main.py

# Memory profile with threshold
/run-profiler --memory --threshold 100MB main.py
```

## Integration

Uses the `python-performance` skill's profiling tools:
- `profiler-runner`: cProfile and py-spy execution
- `memory-analyzer`: Memory usage analysis
- `benchmark-suite`: Comparative benchmarking

This command helps identify and resolve performance bottlenecks efficiently.
