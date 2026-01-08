# Quota Tracking in Conjure

**Plugin**: conjure
**Component**: GeminiQuotaTracker
**Last Updated**: 2025-01-08

## Overview

The `conjure` plugin implements quota tracking for Gemini API delegation to prevent rate limit violations and optimize resource usage. This document provides technical implementation details and usage patterns.

## Architecture

### Inheritance Structure

```python
from leyline import QuotaTracker, QuotaConfig

class GeminiQuotaTracker(QuotaTracker):
    """Gemini-specific quota tracker with advanced token estimation"""

    def __init__(self, limits: dict[str, int] | None = None):
        # Convert legacy dict format to QuotaConfig
        config = self._create_config(limits)
        super().__init__(
            service="gemini",
            config=config,
            storage_dir=Path.home() / ".claude" / "hooks" / "gemini"
        )
```

### Component Diagram

```
leyline.QuotaTracker (base class)
├── Service-agnostic quota logic
├── 8 core methods (inherited)
│   ├── record_request()
│   ├── get_quota_status()
│   ├── can_handle_task()
│   ├── get_current_usage()
│   ├── _load_usage()
│   ├── _save_usage()
│   ├── _cleanup_old_data()
│   └── estimate_file_tokens()
└── Storage management

GeminiQuotaTracker (extends base)
├── Gemini-specific configuration
├── Overridden methods
│   └── estimate_task_tokens() (with tiktoken)
└── Gemini-only features
    ├── _get_encoder()
    ├── _estimate_with_encoder()
    ├── _estimate_with_heuristic()
    ├── _iter_source_paths()
    └── limits property (backward compatibility)
```

## Configuration

### Default Quota Limits

```python
GEMINI_QUOTA_CONFIG = QuotaConfig(
    requests_per_minute=60,
    requests_per_day=1000,
    tokens_per_minute=32000,
    tokens_per_day=1000000,
)
```

### Custom Limits

```python
# Legacy dict format (backward compatible)
tracker = GeminiQuotaTracker(limits={
    "requests_per_minute": 100,
    "requests_per_day": 1500,
    "tokens_per_minute": 50000,
    "tokens_per_day": 1500000,
})

# Modern QuotaConfig (recommended)
from leyline import QuotaConfig

custom_config = QuotaConfig(
    requests_per_minute=100,
    requests_per_day=1500,
    tokens_per_minute=50000,
    tokens_per_day=1500000,
)
tracker = GeminiQuotaTracker(limits=custom_config.__dict__)
```

## Token Estimation

### Estimation Strategy

The tracker uses a multi-tier estimation strategy:

1. **tiktoken estimation** (most accurate)
   - Uses `cl100k_base` encoding (compatible with Gemini)
   - Requires `tiktoken` package
   - Accuracy: ~95-98%

2. **Heuristic estimation** (fallback)
   - Character-based approximation
   - No external dependencies
   - Accuracy: ~70-80%

### Implementation

```python
def estimate_task_tokens(
    self,
    file_paths: list[Path],
    prompt_length: int
) -> int:
    """Estimate total tokens for a task"""

    # Try tiktoken estimation first
    try:
        encoder = self._get_encoder()
        if encoder:
            return self._estimate_with_encoder(
                file_paths,
                prompt_length,
                encoder
            )
    except ImportError:
        pass  # Fall back to heuristic

    # Use heuristic as fallback
    return self._estimate_with_heuristic(
        file_paths,
        prompt_length
    )
```

### File Token Estimation

```python
def _estimate_with_encoder(
    self,
    file_paths: list[Path],
    prompt_length: int,
    encoder
) -> int:
    """Accurate estimation using tiktoken"""

    total_tokens = prompt_length

    for file_path in self._iter_source_paths(file_paths):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tokens = encoder.encode(content)
                total_tokens += len(tokens)
        except (OSError, UnicodeDecodeError):
            # Skip unreadable files
            continue

    return total_tokens
```

## Usage Patterns

### Basic Usage

```python
from conjure.scripts.quota_tracker import GeminiQuotaTracker

# Initialize with defaults
tracker = GeminiQuotaTracker()

# Check quota status
healthy, warnings = tracker.get_quota_status()
if not healthy:
    print("Quota issues:")
    for warning in warnings:
        print(f"  - {warning}")

# Estimate task tokens
tokens = tracker.estimate_task_tokens(
    file_paths=[Path("src/main.py")],
    prompt_length=500
)

# Check if task can be handled
can_handle, issues = tracker.can_handle_task(tokens)
if can_handle:
    # Execute task
    success = execute_gemini_request(tokens)
    tracker.record_request(tokens, success)
else:
    print("Cannot handle task:")
    for issue in issues:
        print(f"  - {issue}")
```

### Hook Integration

The tracker is integrated into Gemini hooks:

```python
# plugins/conjure/hooks/gemini/pre_execution.py

from quota_tracker import GeminiQuotaTracker

tracker = GeminiQuotaTracker()

def check_quota_before_execution(command: str) -> tuple[bool, str]:
    """Check if quota allows execution"""

    # Parse command to estimate tokens
    tokens = estimate_tokens_from_gemini_command(command)

    # Check quota status
    can_handle, issues = tracker.can_handle_task(tokens)

    if not can_handle:
        return False, f"Quota limit reached: {', '.join(issues)}"

    return True, "Quota OK"
```

### CLI Interface

```bash
# Check current quota status
$ python scripts/quota_tracker.py --status
Status: healthy
  RPM: 45/60 (75%)
  TPM: 24560/32000 (76%)
  Daily requests: 234/1000 (23%)
  Daily tokens: 456789/1000000 (45%)

# Validate configuration
$ python scripts/quota_tracker.py --validate-config
Quota configuration validation:
  requests_per_minute: 60
  requests_per_day: 1000
  tokens_per_minute: 32000
  tokens_per_day: 1000000
  Configuration is valid

# Estimate tokens for files
$ python scripts/quota_tracker.py --estimate README.md pyproject.toml
Estimated tokens for ['README.md', 'pyproject.toml']: 2,368
```

## Storage

### Usage Data Structure

```json
{
  "usage": {
    "requests": {
      "last_minute": [
        {"timestamp": 1704681600, "tokens": 1500},
        {"timestamp": 1704681660, "tokens": 2000}
      ],
      "last_day": [
        {"date": "2025-01-08", "requests": 45, "tokens": 67890}
      ]
    },
    "last_cleanup": 1704681600
  }
}
```

### Storage Location

- **Path**: `~/.claude/hooks/gemini/usage.json`
- **Format**: JSON
- **Cleanup**: Automatic removal of entries older than 24 hours

## Backward Compatibility

### Legacy API Support

All existing code continues to work without changes:

```python
# Dict-based limits (legacy)
tracker = GeminiQuotaTracker(limits={
    "requests_per_minute": 100,
    ...
})

# Access limits as dict (legacy property)
limits = tracker.limits  # Returns dict
assert limits["requests_per_minute"] == 100

# Standalone function
tokens = estimate_tokens_from_gemini_command(
    "gemini @file.py ask 'What does this do?'"
)
```

## Performance Characteristics

### Computational Complexity

- **Token estimation**: O(n) where n = total characters
- **Quota check**: O(1) - in-memory counter lookup
- **Recording**: O(1) - append to list with periodic cleanup
- **Storage**: O(1) - single file read/write

### Memory Usage

- **Base tracker**: ~1 KB
- **Per request**: ~100 bytes (in-memory counters)
- **tiktoken encoder**: ~5 MB (if loaded)
- **Storage file**: ~10-50 KB (depending on usage)

## Testing

### Unit Tests

```python
def test_quota_status_checking():
    """Test quota status returns correct warnings"""

    tracker = GeminiQuotaTracker()

    # Normal usage
    with patch.object(tracker, 'get_current_usage') as mock_usage:
        mock_usage.return_value = {
            "requests_last_minute": 30,
            "tokens_last_minute": 15000,
            "requests_today": 500,
            "tokens_today": 500000,
        }

        healthy, warnings = tracker.get_quota_status()
        assert healthy
        assert len(warnings) == 0

    # High usage
    with patch.object(tracker, 'get_current_usage') as mock_usage:
        mock_usage.return_value = {
            "requests_last_minute": 58,  # Near limit
            "tokens_last_minute": 31000,  # Near limit
            "requests_today": 950,  # Near limit
            "tokens_today": 950000,  # Near limit
        }

        healthy, warnings = tracker.get_quota_status()
        assert not healthy
        assert len(warnings) == 4
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_quota_enforcement_in_hook():
    """Test that hook enforces quota limits"""

    tracker = GeminiQuotaTracker()

    # Fill quota to 90%
    for _ in range(54):  # 90% of 60 RPM
        tracker.record_request(500, success=True)

    # Next request should be blocked
    can_handle, issues = tracker.can_handle_task(500)
    assert not can_handle
    assert any("RPM" in issue for issue in issues)
```

## Error Handling

### Common Errors

1. **Storage Access Denied**
   - **Error**: `PermissionError: ~/.claude/hooks/gemini/usage.json`
   - **Resolution**: Check directory permissions, create if missing
   - **Recovery**: Create directory with `mkdir -p ~/.claude/hooks/gemini`

2. **Invalid Configuration**
   - **Error**: `ValueError: QuotaConfig values must be positive`
   - **Resolution**: Verify all quota limits are positive integers
   - **Prevention**: Use `--validate-config` to check before use

3. **tiktoken Import Failed**
   - **Warning**: Falls back to heuristic estimation
   - **Resolution**: Install with `pip install tiktoken`
   - **Impact**: Reduced estimation accuracy (~70-80%)

## Migration from Standalone

If you have a standalone quota tracking implementation:

1. **Add leyline dependency**:
   ```toml
   # pyproject.toml
   dependencies = [
       "leyline>=1.0.0",
   ]
   ```

2. **Extend base class**:
   ```python
   from leyline import QuotaTracker, QuotaConfig

   class MyServiceQuotaTracker(QuotaTracker):
       def __init__(self):
           config = QuotaConfig(...)
           super().__init__(service="myservice", config=config, ...)
   ```

3. **Override service-specific methods**:
   ```python
   def estimate_task_tokens(self, file_paths, prompt_length):
       # Your service-specific estimation logic
       pass
   ```

4. **Test and verify**:
   ```bash
   python scripts/quota_tracker.py --validate-config
   python scripts/quota_tracker.py --status
   ```

## Future Enhancements

### Planned Features

1. **Automatic Backoff**
   - Implement exponential backoff when approaching limits
   - Add jitter to prevent thundering herd

2. **Metrics Export**
   - Export quota metrics to monitoring systems
   - Integration with Prometheus/Grafana

3. **Distributed Tracking**
   - Support for multi-process quota tracking
   - Shared storage (Redis, database)

4. **Predictive Analytics**
   - Forecast quota exhaustion based on usage patterns
   - Proactive warnings before limits reached

## Related Documentation

- [ADR-0002: Extract QuotaTracker to Leyline](../../../docs/adr/0002-quota-tracker-refactoring.md)
- [leyline.QuotaTracker API Documentation](../../../leyline/src/leyline/quota_tracker.py)
- [Gemini API Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)

## Support

For issues or questions:

1. Check health status: `python scripts/quota_tracker.py --status`
2. Validate configuration: `python scripts/quota_tracker.py --validate-config`
3. Review logs: `~/.claude/hooks/gemini/usage.json`
4. Consult error handling guide: [Error Handling Guide](../../../docs/guides/error-handling-guide.md)
