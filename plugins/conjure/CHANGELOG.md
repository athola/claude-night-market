# Changelog

All notable changes to the `conjure` plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Quota Tracking Documentation** - Comprehensive technical guide
  - **Location**: `docs/quota-tracking.md`
  - **Content**: Architecture, configuration, token estimation, usage patterns
  - **Integration**: Hook integration patterns and CLI interface details
  - **Migration**: Guide from standalone to leyline.QuotaTracker inheritance

### Changed

- **GeminiQuotaTracker Refactoring** (2025-12-05)
  - **Reduced Code**: 287 → 255 lines (-32 lines, -11.1%)
  - **Inheritance**: Now extends `leyline.QuotaTracker` base class
  - **Eliminated Duplication**: 11 methods now inherited from base class
  - **Backward Compatibility**: 100% compatible with existing code
  - **See Also**: ADR-0002 in main repository

### Technical Details

#### Inherited Methods (from leyline.QuotaTracker)
- `record_request()` - Record API request with tokens
- `get_quota_status()` - Check quota status with warnings
- `can_handle_task()` - Verify task capacity
- `get_current_usage()` - Get current usage statistics
- `_load_usage()` - Load usage from JSON storage
- `_save_usage()` - Save usage to JSON storage
- `_cleanup_old_data()` - Remove old usage entries
- `estimate_file_tokens()` - Basic file token estimation

#### Gemini-Specific Features (Preserved)
- **Advanced Token Estimation**: Multi-tier strategy with tiktoken support
  - `estimate_task_tokens()` - Main estimation method (overridden)
  - `_get_encoder()` - Optional tiktoken encoder loading
  - `_estimate_with_encoder()` - Accurate estimation with tiktoken
  - `_estimate_with_heuristic()` - Fallback heuristic estimation
- **File Handling**:
  - `_iter_source_paths()` - Directory walking with file type filtering
- **Backward Compatibility**:
  - `limits` property - Dict-based access for legacy code

#### Configuration Changes

**Before** (dict-based):
```python
tracker = GeminiQuotaTracker(limits={
    "requests_per_minute": 60,
    "requests_per_day": 1000,
    "tokens_per_minute": 32000,
    "tokens_per_day": 1000000,
})
```

**After** (QuotaConfig-based, backward compatible):
```python
# Still works (converted internally)
tracker = GeminiQuotaTracker(limits={...})

# New recommended way
from leyline import QuotaConfig
config = QuotaConfig(
    requests_per_minute=60,
    requests_per_day=1000,
    tokens_per_minute=32000,
    tokens_per_day=1000000,
)
tracker = GeminiQuotaTracker(limits=config.__dict__)
```

### Dependencies

**Added**:
- `leyline>=1.0.0` - Service-agnostic quota tracking base class

**Existing**:
- `tiktoken>=0.7.0` - Optional accurate token estimation
- `pre-commit>=3.0.0` - Development tooling

### Migration Notes

If you're using `GeminiQuotaTracker` in your code:

1. **No changes required** - All existing code continues to work
2. **Optional updates**:
   - Use `QuotaConfig` for type safety
   - Review new documentation in `docs/quota-tracking.md`
   - Consider extending the pattern for other services

### Testing

All functionality verified:
- ✅ Instantiation with default and custom limits
- ✅ Quota status checking (`get_quota_status()`)
- ✅ Request recording (`record_request()`)
- ✅ Task capacity checking (`can_handle_task()`)
- ✅ Token estimation (`estimate_task_tokens()`)
- ✅ Gemini command parsing (`estimate_tokens_from_gemini_command()`)
- ✅ File-based token estimation
- ✅ Hook import patterns

### Related Documentation

- [Technical Guide](docs/quota-tracking.md) - Implementation details
- [ADR-0002](../../docs/adr/0002-quota-tracker-refactoring.md) - Architecture decision
- [leyline.QuotaTracker](../../leyline/src/leyline/quota_tracker.py) - Base class

## [1.2.0] - 2025-12-05

### Added

- Initial quota tracking implementation for Gemini API delegation
- Rate limit management for RPM and TPM
- Daily quota tracking for requests and tokens
- Token estimation for files and prompts
- CLI interface for status checking and validation
