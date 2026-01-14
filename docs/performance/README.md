# Performance Documentation

Performance optimization guides and benchmarks for the claude-night-market project.

## Documentation Index

### Hook Performance

**[Hook Performance Guide](hooks.md)** - Detailed guide to hook optimization across all plugins

- Performance benchmarks (7/7 hooks passing)
- Timeout configuration philosophy
- Optimization techniques applied
- Environment variables for tuning
- Benchmarking scripts

**Plugin-Specific Guides:**
- **[Sanctum Hook Performance](../../plugins/sanctum/hooks/PERFORMANCE.md)** - Stop hook optimizations (notification background execution)
- **[Imbue Hook Performance](../../plugins/imbue/hooks/PERFORMANCE.md)** - Scope-guard caching and git optimizations

### Performance Targets

Based on `plugins/abstract/skills/hook-authoring/modules/performance-guidelines.md`:

| Hook Event | Target Time | Maximum Time |
|------------|-------------|--------------|
| PreToolUse | <100ms | 1s |
| PostToolUse | <500ms | 5s |
| UserPromptSubmit | <200ms | 2s |
| Stop | <2s | 10s |
| SessionStart | <2s | 10s |

### Key Optimizations

Performance improvements across the ecosystem include implementing background execution for notifications in the sanctum plugin and using 60-second git metrics caching in the imbue plugin. We have also achieved a 5.2x reduction in the total timeout budget and introduced environment variables to skip non-critical hooks when necessary.

### Environment Variables

```bash
# Disable desktop notifications
export CLAUDE_NO_NOTIFICATIONS=1

# Disable scope-guard checks
export SCOPE_GUARD_DISABLE=1

# Adjust scope-guard cache TTL (default: 60s)
export SCOPE_GUARD_CACHE_TTL=120
```

### Performance Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Slowest hook | 5000ms | 39ms | 128x faster |
| Total timeout budget | 130s | 25s | 5.2x reduction |
| Average hook time | ~700ms | ~45ms | 15.5x faster |
| Hooks passing targets | 6/7 (86%) | 7/7 (100%) | 100% pass rate |

**Result:** Claude Code feels significantly more responsive, especially at session start/stop.

## Related Documentation

- **[Hook Authoring Performance Guidelines](../../plugins/abstract/skills/hook-authoring/modules/performance-guidelines.md)** - Official performance standards
- **[Hook Types](../../plugins/abstract/skills/hook-authoring/modules/hook-types.md)** - Event signatures and timing budgets
- **[SDK Callbacks](../../plugins/abstract/skills/hook-authoring/modules/sdk-callbacks.md)** - Implementation patterns

## Benchmarking

To re-benchmark all hooks:

```bash
python3 << 'EOF'
import subprocess, time, sys
from pathlib import Path

HOOKS = [
    ("plugins/conserve/hooks/context_warning.py", "PreToolUse", 100),
    ("plugins/conserve/hooks/session-start.sh", "SessionStart", 2000),
    ("plugins/imbue/hooks/session-start.sh", "SessionStart", 2000),
    ("plugins/imbue/hooks/user-prompt-submit.sh", "UserPromptSubmit", 200),
    ("plugins/sanctum/hooks/post_implementation_policy.py", "SessionStart", 2000),
    ("plugins/sanctum/hooks/verify_workflow_complete.py", "Stop", 2000),
    ("plugins/sanctum/hooks/session_complete_notify.py", "Stop", 2000),
]

results = []
for hook_path, event_type, target in HOOKS:
    full_path = Path.cwd() / hook_path
    if not full_path.exists(): continue

    cmd = [sys.executable, str(full_path)] if hook_path.endswith(".py") else ["bash", str(full_path)]
    times = []

    for _ in range(3):
        start = time.perf_counter()
        subprocess.run(cmd, capture_output=True, timeout=5, stdin=subprocess.DEVNULL, check=False)
        times.append((time.perf_counter() - start) * 1000)

    avg = sum(times) / len(times)
    status = "PASS" if avg < target else "FAIL"
    print(f"{status} {hook_path:50s} {avg:6.1f}ms / {target:4.0f}ms")

passed = sum(1 for h, e, t in HOOKS if Path.cwd() / h in results)
print(f"\nPassed: {passed}/{len(HOOKS)} hooks")
EOF
```

## Maintenance

When adding new hooks:

1. Follow performance targets from guidelines
2. Implement caching for expensive operations
3. Add disable flags for non-critical features
4. Set timeouts: `max(actual_time * 20, performance_target)`
5. Benchmark regularly with the script above
6. Document optimizations in plugin-specific PERFORMANCE.md

---

**Last Updated:** 2025-01-06
**Optimization Session:** Hook performance optimization (7/7 passing)
