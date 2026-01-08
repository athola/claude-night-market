# Pensieve: Memory Storage for All Skills

**Universal continual learning and memory storage for ALL Claude Code skills - no configuration required.**

## Overview

The Pensieve plugin provides automatic tracking, continual evaluation metrics, and stability gap detection for every skill invocation across ALL plugins by storing skill execution memories:

- **abstract** (skill-auditor, plugin-validator, etc.)
- **sanctum** (pr-review, workflow-improvement, etc.)
- **imbue** (proof-of-work, scope-guard, etc.)
- **memory-palace** (knowledge-intake, review-chamber, etc.)
- **Your custom plugins** (work immediately!)
- **Third-party plugins** (benefit automatically!)

## Installation

### One-Time Setup

```bash
# Clone the repository
git clone https://github.com/athola/claude-night-market.git

# Install the Pensieve plugin
claude plugin install ./claude-night-market/plugins/pensieve

# That's it! All skills are now automatically stored in your Pensieve
```

### Verify Installation

```bash
# Use any skill - it's automatically stored
Skill(abstract:skill-auditor)

# View your memories
/pensieve:metrics

# You should see your skill in the metrics!
```

## What It Does

### Automatic Memory Storage

Every skill invocation is automatically stored in your Pensieve with:

- **Timestamp**: When the memory was created
- **Duration**: How long the skill took
- **Outcome**: Success, failure, or partial success
- **Continual metrics**: Stability gap, worst-case accuracy, trends

### Continual Learning Metrics

After each execution, calculates:

```python
stability_gap = average_accuracy - worst_case_accuracy
```

**Why it matters**:
- Traditional metrics only measure average performance.
- Stability gap detects inconsistencies (sometimes works, sometimes fails).
- Early warning triggers improvement before batch aggregation would catch it.

### Example

```
Memory 1: Success ✓ (accuracy: 1.0, gap: 0.0)
Memory 2: Success ✓ (accuracy: 1.0, gap: 0.0)
Memory 3: Failure ✗ (accuracy: 0.67, gap: 0.67) ⚠️
                      ↑ Stability gap detected!
                Triggers improvement workflow
```

## Usage

### View All Memories

```bash
/pensieve:metrics

# Output:
# Pensieve Memories - All Plugins
# =================================
#
# abstract:
#   skill-auditor:
#     Memories: 47
#     Success rate: 94%
#     Stability gap: 0.12 ✓
#
# sanctum:
#   pr-review:
#     Memories: 23
#     Success rate: 91%
#     Stability gap: 0.08 ✓
#
# Your-custom-plugin:
#   my-skill:
#     Memories: 5
#     Success rate: 80%
#     Stability gap: 0.40 ⚠️
```

### Analyze Specific Skill

```bash
/pensieve:metrics --skill sanctum:pr-review

# Detailed breakdown for that skill's memories
```

### View Memory History

```bash
/pensieve:history --plugin abstract --last 24h

# Shows recent memories with timestamps and outcomes
```

### Find Unstable Skills

```bash
/pensieve:metrics --unstable-only

# Shows only skills with stability_gap > 0.3
```

## How It Works

### Universal Hook Architecture

```
User runs: Skill(any-plugin:any-skill)
    ↓
PreToolUse Hook (Pensieve plugin)
    ├─ Records start time
    ├─ Generates memory ID
    └─ Stores state file
    ↓
Skill executes (in its original plugin)
    ↓
PostToolUse Hook (Pensieve plugin)
    ├─ Reads pre-execution state
    ├─ Calculates duration
    ├─ Evaluates outcome
    ├─ Updates continual metrics
    └─ Stores memory in Pensieve
```

**Key insight**: Hooks are in the Pensieve plugin, but they intercept ALL skill invocations regardless of which plugin defines the skill.

### Storage

```
~/.claude/skills/logs/        # Your Pensieve
├── .history.json              # Aggregated continual metrics
├── abstract/
│   ├── skill-auditor/
│   │   └── 2025-01-08.jsonl   # Memories from this skill
│   └── plugin-validator/
│       └── 2025-01-08.jsonl
├── sanctum/
│   └── pr-review/
│       └── 2025-01-08.jsonl
├── your-custom-plugin/        # Automatically stored!
│   └── your-skill/
│       └── 2025-01-08.jsonl
└── third-party-plugin/        # Automatically stored!
    └── their-skill/
        └── 2025-01-08.jsonl
```

## For Plugin Developers

### Your Plugins Are Automatically Stored

**No setup required!** If you create a plugin with skills:

```bash
my-plugin/
├── skills/
│   └── my-skill.md
└── .claude-plugin/
    └── plugin.json
```

And someone installs Pensieve:

```bash
claude plugin install pensieve
```

Then your skills are **automatically stored** in their Pensieve when users run them:

```bash
Skill(my-plugin:my-skill)  # Automatically stored!
```

### Integration Patterns

**Pattern 1: Passive storage** (default)
- No code changes needed
- Pensieve handles everything

**Pattern 2: Active monitoring**
```python
# Check if skill is unstable before running
if get_stability_gap("my-plugin:my-skill") > 0.3:
    # Warn user or suggest alternative
    pass
```

**Pattern 3: Improvement triggering**
```python
# Automatically trigger improvement
if get_stability_gap("my-plugin:my-skill") > 0.5:
    run_improvement_workflow("my-plugin:my-skill")
```

## Troubleshooting

### Skills Not Being Stored?

1. **Check Pensieve is installed**:
```bash
ls ~/.claude/plugins/ | grep pensieve
```

2. **Verify hooks are registered**:
```bash
cat ~/.claude/plugins/pensieve/hooks/hooks.json
```

3. **Test with a simple skill**:
```bash
Skill(abstract:skill-auditor)
/pensieve:history --plugin abstract --last 1h
```

### Metrics Not Appearing?

1. **Check history file**:
```bash
cat ~/.claude/skills/logs/.history.json
```

2. **Look for error messages** in Claude Code output

3. **Verify file permissions**:
```bash
ls -la ~/.claude/skills/logs/
```

## Advanced Usage

### Export Memories

```bash
# Export to CSV
/pensieve:export --format csv --output memories.csv

# Export to JSON
/pensieve:export --format json --output memories.json

# Export specific time range
/pensieve:export --since "2025-01-01" --until "2025-01-31"
```

### Custom Alerts

```bash
# Configure alerts
/pensieve:alerts configure --threshold stability_gap:0.3 --action notify

# View alert history
/pensieve:alerts history
```

## Performance

- **Overhead**: 12-25ms per skill invocation
- **Storage**: ~500 bytes per memory
- **Scalability**: Tested to 10,000+ executions per day
- **Memory**: ~1MB for history file (1000 skills tracked)

## Compatibility

- **Python**: 3.8+
- **Claude Code**: All versions with hooks support
- **OS**: Linux, macOS, Windows (WSL2)
- **Plugins**: All plugins with skills

## FAQ

**Q: Does this slow down my skills?**
A: Minimal overhead (~12-25ms). Most skills take 100-5000ms, so overhead is <1%.

**Q: What about my private/sensitive skills?**
A: Memories are stored locally in `~/.claude/skills/logs/`. Nothing is sent externally.

**Q: Can I disable storage for specific skills?**
A: Yes, add to your skill's frontmatter:
```yaml
---
pensieve: false
---
```

**Q: How long are memories kept?**
A: Forever, by default. You can clean up old memories:
```bash
/pensieve:cleanup --older-than 90days
```

**Q: Why is it called "Pensieve"?**
A: A "pensieve" stores and organizes memories for later examination and analysis.

## Contributing

Contributions welcome! Please see:
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [Development guide](docs/DEVELOPMENT.md)
- [Issue tracker](https://github.com/athola/claude-night-market/issues)

## License

MIT License - see [LICENSE](LICENSE) file.

## Credits

Created by the claude-night-market community.

Inspired by:
- [Avalanche](https://github.com/ContinualAI/avalanche) - Continual learning research
- [ContinualEvaluation](https://github.com/Mattdl/ContinualEvaluation) - ICLR 2023 paper on stability gap

---

**Plugin**: pensieve
**Version**: 1.0.0
**Status**: Production ready
**Dependencies**: None
**Installation**: One command, works globally
**Concept**: Stores and organizes skill execution memories for analysis
