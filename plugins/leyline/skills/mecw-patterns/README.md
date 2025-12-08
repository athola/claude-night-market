# MECW Patterns Skill

Maximum Effective Context Window (MECW) theory and practical patterns for preventing hallucinations through context management.

## Overview

This skill provides the theoretical foundations and practical utilities for managing context window usage according to MECW principles. The core principle: **Never use more than 50% of total context window for input content.**

## Components

- **SKILL.md**: Main skill document with quick start guide
- **modules/mecw-theory.md**: Theoretical foundations and the physics of context pressure
- **modules/monitoring-patterns.md**: Advanced patterns for continuous monitoring

## Python Module

The skill is backed by the `leyline.mecw` Python module:

```python
from leyline import (
    MECW_THRESHOLDS,
    MECWMonitor,
    MECWStatus,
    calculate_context_pressure,
    check_mecw_compliance,
)
```

## Usage

See [SKILL.md](SKILL.md) for detailed usage examples and integration patterns.

## Key Functions

- `calculate_context_pressure()`: Get pressure level (LOW/MODERATE/HIGH/CRITICAL)
- `check_mecw_compliance()`: Full compliance check with recommendations
- `MECWMonitor`: Continuous monitoring with trend analysis

## Integration

Reference this skill in your plugin:

```yaml
dependencies: [leyline:mecw-patterns]
```

Then use the utilities to manage context window usage and prevent hallucinations.
