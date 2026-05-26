---
module: kuva-visualization
category: output
dependencies: [Bash, Read]
estimated_tokens: 350
---

# Visualizing Performance Findings with kuva

**When a performance review produces before/after benchmark data,
render it as a chart.** Text comparisons like "380ms → 60ms" are
correct but hard to scan across multiple hotspots. A scatter or
bar chart makes regressions and wins immediately visible.

[kuva](https://github.com/Psy-Fer/kuva) is a Rust scientific
plotting library (and CLI binary) that renders directly from TSV/CSV
input to SVG, PNG, or the terminal. Install once; pipe benchmark
data in without modifying project source.

## Install

```bash
cargo install kuva --features cli
```

## Rendering a before/after benchmark comparison

### criterion (Rust)

criterion writes per-benchmark timing samples to
`target/criterion/<name>/new/estimates.json`. Extract the mean and
pipe to kuva:

```bash
# Collect before/after means for all criterion benchmarks
python3 - <<'EOF'
import json, pathlib, sys

rows = ["benchmark\tstage\tns"]
for est in pathlib.Path("target/criterion").rglob("estimates.json"):
    bench = est.parts[-3]
    data = json.loads(est.read_text())
    mean_ns = data["mean"]["point_estimate"]
    # Distinguish before/after by tag; adjust to your workflow.
    rows.append(f"{bench}\tafter\t{mean_ns:.1f}")

print("\n".join(rows))
EOF | kuva bar /dev/stdin --x benchmark --y ns --color-by stage \
      --title "Before vs After" --terminal
```

For a paired comparison where you have both runs saved:

```bash
# before.tsv and after.tsv each contain: benchmark<TAB>ns
kuva scatter before.tsv after.tsv \
    --x ns --y ns --color-by stage \
    --title "Hotspot timing (lower is better)" \
    -o perf-comparison.svg
```

### pytest-benchmark (Python)

```bash
pytest --benchmark-json=bench.json tests/

# Convert to TSV
python3 -c "
import json, sys
d = json.load(open('bench.json'))
print('name\tns')
for b in d['benchmarks']:
    print(b['name'] + '\t' + str(b['stats']['mean'] * 1e9))
" | kuva bar /dev/stdin --x name --y ns \
      --title "Benchmark means (ns)" -o bench.svg
```

### Ad-hoc timing table

If you are capturing timings manually (e.g., from production traces
as in the mlock war story):

```tsv
stage	p50_ms	p99_ms
before_mlock	180	380
after_mlock	35	60
```

```bash
kuva bar timings.tsv --x stage --y p99_ms \
    --title "p99 barge-in latency (ms)" -o latency.svg
```

## Terminal output (no file required)

For quick CI feedback without writing an SVG artifact, add
`--terminal` to any kuva command. The chart renders as Unicode
block characters directly in the shell, visible in CI logs.

```bash
kuva bar timings.tsv --x stage --y p99_ms --terminal
```

## When to attach a chart as evidence

The `Skill(imbue:proof-of-work)` discipline requires evidence
references `[E1]`/`[E2]` for before/after claims. A kuva-rendered
SVG in the PR description or comments is a valid `[E2]` when it
shows the post-fix benchmark result alongside the pre-fix baseline.

Minimum evidence bar:

| Claim | Required chart type |
|-------|---------------------|
| "Latency improved by X" | Bar or scatter with before/after |
| "Throughput doubled" | Line or bar over input size range |
| "Memory usage flat" | Line over time or input size |
| "O(n log n) vs O(n²)" | Log-log scatter showing slope change |

## When NOT to use kuva

- The project already has matplotlib/plotly in its dev dependencies;
  consistency matters more than zero-dep.
- The hotspot is trivial (single function, clear before/after number
  in a two-column table). Charts are for 3+ data points.
- CI environment has no Rust toolchain and adding one is not
  worth it; fall back to a numeric table in the PR comment.
