# Plugin Dependency Audit

Last updated: 2026-03-27

This document tracks external dependencies across plugins,
their fallback strategies, and documentation status.

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

## Supply Chain Incidents

### Incident 1: LiteLLM PyPI Compromise (March 2026)

**Date**: 2026-03-24 (10:39 UTC - 16:00 UTC)
**Affected versions**: `1.82.7`, `1.82.8` (both removed from PyPI)
**Attack vector**: Compromised maintainer PyPI credentials (linked to Trivy CI/CD supply chain attack)
**Payload**: Credential stealer in `proxy_server.py` and `litellm_init.pth` — harvested environment variables, SSH keys, cloud provider credentials, Kubernetes tokens, and database passwords
**Source**: https://docs.litellm.ai/blog/security-update-march-2026

**Impact on our ecosystem**: None. Only `simple-resume` uses litellm, locked to `1.81.15`.
Patched with version exclusions: `litellm>=1.0,<2.0,!=1.82.7,!=1.82.8`

**Detection indicators**:
- Presence of `litellm_init.pth` file in site-packages
- Lockfile resolving to `1.82.7` or `1.82.8`

**Lessons learned**:
1. Lockfile hash pinning (uv.lock SHA256) would have caught a tampered reinstall
2. Version exclusions (`!=`) are a lightweight defense for known-bad releases
3. Safety/CVE databases lag behind zero-day supply chain attacks — need OSV scanning
4. Daily CI scans are insufficient for attacks with <6 hour windows — SessionStart hooks provide per-session defense

### Incident Response Checklist

When a supply chain compromise is reported:

1. **Scan all lockfiles** on the machine for affected versions
2. **Search for malicious artifacts** (e.g., `.pth` files, unexpected scripts)
3. **Check installed versions** in all `.venv` directories
4. **Add version exclusions** to `pyproject.toml` for affected packages
5. **Rotate credentials** if any environment was on a compromised version
6. **Document the incident** in this file
7. **Update the blocklist** in `plugins/leyline/skills/supply-chain-advisory/known-bad-versions.json`

## Guidelines for New Dependencies

### When Adding Python Dependencies

1. **Ask**: Is this dependency truly required, or can we use a fallback?
2. **If required**: Add to `dependencies` in pyproject.toml
3. **If optional**: Add to `[project.optional-dependencies]`
   and implement fallback

### When Referencing Other Plugins

1. **Skill references**: Document in frontmatter `dependencies:` field
2. **Python imports**: Implement stub fallback classes
3. **CLI tools**: Check availability with `shutil.which()`
   and provide error messages

### Fallback Priority

1. Heuristic/simple implementation (preferred)
2. Stub class with limited functionality
3. Clear error message with installation instructions
4. Hard failure (only for truly essential dependencies)
