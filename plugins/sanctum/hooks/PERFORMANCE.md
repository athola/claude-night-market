# Hook Performance Optimization

## Problem

The Stop hooks were taking 5+ seconds to complete, making Claude Code feel sluggish at the end of every command.

**Root causes:**
1. `session_complete_notify.py` made synchronous subprocess calls with long timeouts
2. Terminal detection (tmux) took up to 2 seconds
3. Notification sending took 3-5 seconds per platform
4. All operations ran **sequentially** in the foreground

## Solution

### 1. Background Execution (Primary Fix)

The notification hook now:
- **Spawns itself in background** using `subprocess.Popen` with `start_new_session=True`
- Returns immediately (~38ms) without waiting for notification
- Notification sends asynchronously in detached child process

**Before:**
```python
terminal_info = get_terminal_info()  # 2s
send_notification(title, message)    # 3-5s
# Total: 5-7 seconds blocking
```

**After:**
```python
subprocess.Popen([sys.executable, __file__, "--background"], ...)
sys.exit(0)
# Total: ~38ms, notification runs in background
```

### 2. Reduced Timeouts (Secondary Fix)

Timeout reductions for background operations:
- tmux detection: 2s → 0.5s
- Linux notify-send: 3s → 1s
- macOS osascript: 3s → 1s
- Windows PowerShell: 5s → 2s

### 3. Hook Configuration Timeout

Reduced hook timeouts in `hooks.json`:
- `verify_workflow_complete.py`: 5s → 2s
- `session_complete_notify.py`: 5s → 1s

## Performance Results

**Before optimization (v1):**
- Average: 5-7 seconds
- Blocked Claude Code until complete

**After background execution (v2):**
- Average: **60ms** (2 separate hooks)
- Non-blocking - notification sends in background
- Workflow verification: ~26ms (inline)
- Notification: ~39ms (background process)

This optimization maintains separate hooks for better modularity while keeping performance excellent through background execution.

## Disabling Notifications

If you prefer no notifications at all, set the environment variable:

```bash
export CLAUDE_NO_NOTIFICATIONS=1
```

The `session_complete_notify.py` hook checks this variable and exits early if set, maintaining the workflow verification while skipping notifications.

## Architecture

```
┌─────────────────────────────────┐
│ Claude Code finishes command    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Stop hooks invoked              │
└────────────┬────────────────────┘
             │
             ├──────────────────┬─────────────────────┐
             │                  │                     │
             ▼                  ▼                     ▼
┌────────────────────┐  ┌──────────────────┐  ┌───────────────────┐
│ verify_workflow_   │  │ session_complete │  │ Child process     │
│ _complete.py       │  │ _notify.py       │  │ (background)      │
│ - Inline check     │  │ - Spawn BG       │  │ - get_term_info() │
│ - ~26ms            │  │ - Exit ~39ms      │  │ - send_notify()   │
└────────────────────┘  └──────────────────┘  │ - Runs async      │
                                             └───────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Claude Code continues           │
│ (non-blocking)                  │
└─────────────────────────────────┘
```

## Testing Hook Performance

```bash
# Test individual Stop hook speeds
python3 -c "
import time
import subprocess
import sys

hooks = [
    'plugins/sanctum/hooks/verify_workflow_complete.py',
    'plugins/sanctum/hooks/session_complete_notify.py'
]

for hook in hooks:
    times = []
    for i in range(5):
        start = time.perf_counter()
        result = subprocess.run([sys.executable, hook], capture_output=True, timeout=2, stdin=subprocess.DEVNULL)
        duration = time.perf_counter() - start
        times.append(duration * 1000)

    avg = sum(times) / len(times)
    print(f'{hook.split(\"/\")[-1]}: {avg:.2f}ms')

print(f'Target: <100ms per hook')
"
```

Expected output:
```
verify_workflow_complete.py: 26.14ms
session_complete_notify.py: 38.97ms
Target: <100ms per hook ✓
```

## Related Documentation

- **Performance Guidelines**: `plugins/abstract/skills/hook-authoring/modules/performance-guidelines.md`
- **Hook Types**: `plugins/abstract/skills/hook-authoring/modules/hook-types.md`
- **Stop Hook Budget**: Target <2s, Maximum 10s

## Lessons Learned

1. **Notifications are non-critical** - perfect candidates for background execution
2. **subprocess.Popen > subprocess.run** when you don't need the result
3. **start_new_session=True** properly detaches the child process
4. **Always measure** - the 132x speedup came from profiling first
5. **Timeouts compound** - serial operations with 2s+3s+5s = 10s total
