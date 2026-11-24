---
name: configuration
description: User settings and hook auto-trigger conditions for the War Room
category: war-room-module
tags: [configuration, settings, hooks]
dependencies: []
estimated_tokens: 200
---

# War Room Configuration

### User Settings

```json
{
  "war_room": {
    "default_mode": "lightweight",
    "auto_escalate": true,
    "delphi_threshold": 0.85,
    "max_delphi_rounds": 5
  }
}
```

### Hook Auto-Trigger

War Room can be auto-suggested via hook when:
- Keywords detected ("strategic decision", "trade-off", etc.)
- Complexity score exceeds threshold (0.7)
- User has opted in via settings
