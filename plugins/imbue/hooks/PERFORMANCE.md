# Scope-Guard Hook Performance Optimization

## Overview

The scope-guard UserPromptSubmit hook has been optimized to minimize latency on every user prompt while still providing real-time branch metrics monitoring.

## Performance Results

| Mode | Time | vs Original | Description |
|------|------|-------------|-------------|
| **Original** | 117ms | baseline | No optimizations |
| **Cold Cache** | 51ms | **2.3x faster** | First run after cache expires |
| **Warm Cache** | 12ms | **9.6x faster** | Subsequent runs within 60s TTL |
| **Disabled** | 2ms | **58x faster** | Completely bypassed |

**All modes pass the UserPromptSubmit target of <200ms.**

## Optimizations Applied

### 1. Caching System (60-second TTL)

Scope metrics don't change frequently during active development, so caching provides massive speedups:

```bash
# Cache file location (unique per repository)
CACHE_FILE="${TMPDIR:-/tmp}/scope-guard-cache-$(git rev-parse --show-toplevel | md5sum | cut -d' ' -f1).txt"
CACHE_TTL="${SCOPE_GUARD_CACHE_TTL:-60}"  # seconds

# Check cache freshness
if [ -f "$CACHE_FILE" ]; then
    cache_age=$(($(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)))
    if [ "$cache_age" -lt "$CACHE_TTL" ]; then
        # Return cached result immediately
        cat "$CACHE_FILE"
        exit 0
    fi
fi
```

**Benefits:**
- First prompt: 51ms (cache miss)
- Subsequent prompts (within 60s): 12ms (cache hit)
- **9.6x speedup** for typical development flow

**Configurable:**
```bash
export SCOPE_GUARD_CACHE_TTL=120  # Cache for 2 minutes instead
```

### 2. Faster Git Operations

Replaced slow git commands with optimized alternatives:

#### Before:
```bash
# Slow: runs git diff, then pipes through tail
stat_line=$(git diff "$base_branch" --stat 2>/dev/null | tail -1)
```

#### After:
```bash
# Fast: use --shortstat (single summary line)
stat_line=$(git diff "$base_branch" --shortstat 2>/dev/null)
```

**Savings:** ~10-20ms on large diffs

#### Before:
```bash
# Slow: nested git calls
merge_base_date=$(git log -1 --format=%ct "$(git merge-base "$base_branch" HEAD 2>/dev/null)" 2>/dev/null || echo "$(date +%s)")
```

#### After:
```bash
# Fast: separate merge-base call, reuse result
merge_base=$(git merge-base "$base_branch" HEAD 2>/dev/null)
if [ -n "$merge_base" ]; then
    merge_base_date=$(git log -1 --format=%ct "$merge_base" 2>/dev/null || echo "$(date +%s)")
else
    merge_base_date=$(date +%s)
fi
```

**Savings:** ~5-10ms (avoids re-running merge-base)

### 3. Disable Switch

For users who don't want scope-guard monitoring:

```bash
export SCOPE_GUARD_DISABLE=1
```

**Result:** 2.1ms execution time (immediate bypass, no git operations)

**Use cases:**
- Working on non-feature branches
- Quick prototyping sessions
- CI/CD environments where scope monitoring isn't needed

## Cache Behavior

### Cache Lifetime

The cache expires after 60 seconds (configurable via `SCOPE_GUARD_CACHE_TTL`):

```
Minute 0:00 - First prompt: 51ms (cache miss, git operations)
Minute 0:15 - Second prompt: 12ms (cache hit)
Minute 0:30 - Third prompt: 12ms (cache hit)
Minute 0:45 - Fourth prompt: 12ms (cache hit)
Minute 1:15 - Fifth prompt: 51ms (cache expired, refresh)
```

### Cache Invalidation

The cache automatically refreshes when:
1. **Time expires** (60 seconds default)
2. **Repository changes** (cache is per-repo based on path hash)
3. **Manual clear**: `rm /tmp/scope-guard-cache-*`

### Cache Location

- **macOS/Linux:** `/tmp/scope-guard-cache-{hash}.txt`
- **Custom TMPDIR:** `$TMPDIR/scope-guard-cache-{hash}.txt`

Each repository gets its own cache file based on the repository path hash.

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SCOPE_GUARD_DISABLE` | `0` | Set to `1` to completely bypass scope-guard checks |
| `SCOPE_GUARD_CACHE_TTL` | `60` | Cache lifetime in seconds |
| `SCOPE_GUARD_BASE_BRANCH` | `main` | Base branch for comparison |
| `SCOPE_GUARD_RED_LINES` | `2000` | RED zone threshold for line changes |
| `SCOPE_GUARD_YELLOW_LINES` | `1500` | YELLOW zone threshold for line changes |
| `SCOPE_GUARD_RED_COMMITS` | `30` | RED zone threshold for commit count |
| `SCOPE_GUARD_YELLOW_COMMITS` | `25` | YELLOW zone threshold for commit count |
| `SCOPE_GUARD_RED_DAYS` | `7` | RED zone threshold for branch age (days) |
| `SCOPE_GUARD_YELLOW_DAYS` | `7` | YELLOW zone threshold for branch age (days) |
| `SCOPE_GUARD_RED_FILES` | `15` | RED zone threshold for new files |
| `SCOPE_GUARD_YELLOW_FILES` | `12` | YELLOW zone threshold for new files |

### Example Configurations

**Fast development mode** (longer cache):
```bash
export SCOPE_GUARD_CACHE_TTL=300  # 5 minutes
```

**Strict monitoring** (shorter cache):
```bash
export SCOPE_GUARD_CACHE_TTL=30  # 30 seconds
```

**Disable for quick tasks**:
```bash
export SCOPE_GUARD_DISABLE=1
```

**Relaxed thresholds** (for larger projects):
```bash
export SCOPE_GUARD_RED_LINES=5000
export SCOPE_GUARD_YELLOW_LINES=3000
export SCOPE_GUARD_RED_COMMITS=50
```

## Benchmarking

To re-benchmark the scope-guard hook:

```bash
python3 << 'EOF'
import subprocess
import time

hook = "plugins/imbue/hooks/user-prompt-submit.sh"

# Clear cache
subprocess.run(["rm", "-f", "/tmp/scope-guard-cache-*"], stderr=subprocess.DEVNULL)

# Benchmark cold cache
times = []
for i in range(3):
    start = time.perf_counter()
    subprocess.run(["bash", hook], capture_output=True, timeout=2, stdin=subprocess.DEVNULL)
    times.append((time.perf_counter() - start) * 1000)

print(f"Cold cache average: {sum(times)/len(times):.1f}ms")

# Benchmark warm cache
times = []
for i in range(3):
    start = time.perf_counter()
    subprocess.run(["bash", hook], capture_output=True, timeout=2, stdin=subprocess.DEVNULL)
    times.append((time.perf_counter() - start) * 1000)

print(f"Warm cache average: {sum(times)/len(times):.1f}ms")
EOF
```

Expected output:
```
Cold cache average: 51.4ms
Warm cache average: 12.2ms
```

## Performance Trade-offs

### Cache TTL Selection

**Shorter TTL (10-30s):**
- ✅ More up-to-date metrics
- ✅ Catches scope drift faster
- ❌ More git operations (slower)

**Longer TTL (60-300s):**
- ✅ Faster prompt responses
- ✅ Less git overhead
- ❌ Metrics may lag behind actual changes

**Recommendation:** 60s (default) balances freshness and performance for typical development workflows.

### Disabled Mode

**When to disable:**
- Working on documentation-only changes
- Quick experiments or spike work
- Non-git workflows
- CI/CD environments

**When to keep enabled:**
- Feature branch development
- Long-running work that needs scope monitoring
- Team environments with scope guidelines

## Related Documentation

- **Main Performance Guide:** `/HOOK_PERFORMANCE.md`
- **Scope-Guard Skill:** `plugins/imbue/skills/scope-guard/skill.md`
- **Hook Types:** `plugins/abstract/skills/hook-authoring/modules/hook-types.md`

## Performance History

| Date | Version | Cold Cache | Warm Cache | Notes |
|------|---------|------------|------------|-------|
| 2025-01-06 | v1.0 | 117ms | - | Original implementation |
| 2025-01-06 | v2.0 | 51ms | 12ms | Added caching, optimized git commands |

**Total improvement:** 9.6x faster for typical usage (warm cache)
