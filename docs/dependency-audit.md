# Plugin Dependency Audit

Last updated: 2025-01-23

This document tracks external dependencies across plugins, their fallback strategies, and documentation status.

## Dependency Categories

### 1. Python Package Dependencies

| Plugin | Package | Required | Fallback Strategy | Status |
|--------|---------|----------|-------------------|--------|
| leyline | tiktoken | Optional `[tokens]` | Heuristic estimation | Good |
| conjure | tiktoken | Optional `[full]` | Heuristic estimation | Good |
| conjure | leyline | Optional `[full]` | Stub class implementations | Good |
| memory-palace | tiktoken | Optional `[tokens]` | N/A (not currently used) | Fixed |
| memory-palace hooks | pyyaml | Required | None (core dependency) | OK |
| memory-palace hooks | xxhash | Optional `[fast]` | Falls back to hashlib | Good |
| abstract | pyyaml | Required | None (core dependency) | OK |

### 2. External CLI Tools

| Plugin | Tool | Required | Fallback Strategy | Documented |
|--------|------|----------|-------------------|------------|
| scry | ffmpeg | Yes | None (hard requirement) | Yes (README) |
| scry | vhs | Yes | None (hard requirement) | Yes (README) |
| scry | playwright | Yes | None (hard requirement) | Yes (README) |
| conjure | claude | Soft | Error message with instructions | Yes |
| conjure | ccgd/claude-glm | Soft | Multiple fallback paths | Yes |
| sanctum | notify-send | Optional | Graceful failure | Yes (README) |
| sanctum | osascript | Optional | Graceful failure (macOS) | Yes (README) |
| sanctum | powershell | Optional | Graceful failure (Windows) | Yes (README) |
| sanctum | zellij | Optional | Graceful degradation | Implicit |
| sanctum | tmux | Optional | Graceful degradation | Implicit |

### 3. Cross-Plugin Skill References

| Source Plugin | Referenced Skill | Required | Fallback | Documented |
|---------------|------------------|----------|----------|------------|
| hookify | abstract:hook-scope-guide | Soft | Works without, less guidance | Partially |
| sanctum | memory-palace (skill-logs) | Soft | Command unavailable | Implicit |

### 4. Shared Code Patterns

| Pattern | Plugins Using | Implementation | Status |
|---------|---------------|----------------|--------|
| tasks_manager.py | attune, sanctum, spec-kit | Per-plugin differentiated copies | Good |
| memory-palace hooks/shared/ | memory-palace only | Local to plugin | Good |
| abstract/shared-modules/ | abstract only | Local to plugin | Good |

## Fallback Implementation Patterns

### Pattern 1: Optional Import with Stub (Recommended)

Used by `conjure/scripts/quota_tracker.py`:

```python
try:
    from leyline import QuotaConfig, QuotaTracker
except ImportError:
    # Define fallback stub classes
    @dataclass(frozen=True)
    class QuotaConfig:
        requests_per_minute: int
        requests_per_day: int
        tokens_per_minute: int
        tokens_per_day: int

    class QuotaTracker:
        def __init__(self, service: str, config: QuotaConfig, storage_dir: Path | None = None):
            self.service = service
            self.config = config
            self.storage_dir = storage_dir

        def get_quota_status(self) -> tuple[str, list[str]]:
            return "[OK] Healthy", ["(leyline not installed; quota tracking disabled)"]
```

### Pattern 2: Optional Import with Heuristic Fallback

Used by `leyline/src/leyline/tokens.py`:

```python
try:
    import tiktoken
except ImportError:
    tiktoken = None
    logger.debug("tiktoken not available, using heuristic estimation")

def estimate_tokens(files: list[str], prompt: str = "") -> int:
    encoder = _get_encoder()
    if encoder:
        return _estimate_with_encoder(encoder, files, prompt)
    return _estimate_with_heuristic(files, prompt)
```

### Pattern 3: Platform-Specific with Graceful Failure

Used by `sanctum/hooks/session_complete_notify.py`:

```python
def notify_linux(title: str, message: str) -> bool:
    try:
        subprocess.run(["/usr/bin/notify-send", ...], check=True, timeout=1)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False
```

### Pattern 4: Per-Plugin Differentiated Copies

Used for `tasks_manager.py`:

Each plugin (attune, sanctum, spec-kit) has its own copy with:
- Plugin-specific constants (`PLUGIN_NAME`, `TASK_PREFIX`, `DEFAULT_STATE_DIR`)
- Domain-specific `CROSS_CUTTING_KEYWORDS`
- Built-in file-based fallback when Claude Code Tasks unavailable

## Action Items

### Completed

- [x] tasks_manager.py differentiated per plugin (commit d89a55c)
- [x] conjure quota_tracker.py has leyline fallback
- [x] leyline tokens.py has tiktoken fallback
- [x] sanctum notification hook has cross-platform support
- [x] scry dependencies documented in README
- [x] Move tiktoken to optional in memory-palace pyproject.toml
- [x] Move tiktoken/leyline to optional in conjure pyproject.toml
- [x] Fix leyline pyproject.toml optional dependencies format
- [x] Document hookify dependency on abstract:hook-scope-guide skill
- [x] Add optional dependency tables to conjure, leyline, hookify READMEs

### Future Improvements

- [ ] Add dependency documentation to attune plugin template for new plugins
- [ ] Consider adding a `make check-deps` target to validate fallbacks work

## Guidelines for New Dependencies

### When Adding Python Dependencies

1. **Ask**: Is this dependency truly required, or can we use a fallback?
2. **If required**: Add to `dependencies` in pyproject.toml
3. **If optional**: Add to `[project.optional-dependencies]` and implement fallback

### When Referencing Other Plugins

1. **Skill references**: Document in frontmatter `dependencies:` field
2. **Python imports**: Implement stub fallback classes
3. **CLI tools**: Check availability with `shutil.which()` and provide error messages

### Fallback Priority

1. Heuristic/simple implementation (preferred)
2. Stub class with limited functionality
3. Clear error message with installation instructions
4. Hard failure (only for truly essential dependencies)
