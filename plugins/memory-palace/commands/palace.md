# Memory Palace Command

## Usage

Create and manage memory palaces for spatial knowledge organization. Palaces are the unified storage for all captured knowledge from research sessions.

### List Palaces
```
/palace list
```
Shows all existing memory palaces with entry counts and last-modified dates.

### View Palace
```
/palace view <palace-id>
```
Displays the structure, districts, and entries of a specific palace.

### Create Palace
```
/palace create <name> <domain> [--metaphor <type>]
```
Creates a new memory palace with the specified name and domain.

### Sync from Queue
```
/palace sync [--dry-run] [--auto-create]
```
Process the intake queue (`data/intake_queue.jsonl`) into palaces:
- Matches queued research to existing palaces by domain/tags
- Creates new entries in appropriate palace districts
- With `--auto-create`: Creates new palaces for unmatched domains
- With `--dry-run`: Preview changes without applying

### Prune / Maintenance
```
/palace prune [--stale-days 90]
```
Check palaces for entries needing cleanup. Also available via the consolidated garden command:
```
memory_palace_cli.py garden tend --palaces [--stale-days 90]
```

Identifies:
- Stale entries (older than stale-days, default 90)
- Low quality entries (novelty score < 0.3)
- Duplicate entries across palaces

Shows recommendations and **prompts for user approval** before any changes.

### Apply Cleanup
```
/palace prune --apply
```
Apply cleanup after reviewing recommendations. **Only run after reviewing the prune check output.**

### Status
```
/palace status
```
Shows:
- Total palaces and entry counts
- Intake queue size (pending items)
- Palace health metrics

### Delete Palace
```
/palace delete <palace-id>
```
Removes a palace (creates backup first).

## What It Does

1. **Unified Knowledge Storage**: Palaces are the single source of truth for captured knowledge
2. **Queue Processing**: Syncs research from intake queue into palace entries
3. **Domain Organization**: Groups knowledge by domain in districts within palaces
4. **Lifecycle Management**: Tracks creation, updates, quality scores
5. **Integration**: Works with `/update-plugins` for automated maintenance

## Architectural Metaphors

Choose a metaphor that fits your knowledge domain:

| Metaphor | Best For |
|----------|----------|
| `building` | General organization (default) |
| `fortress` | Security, defense, production-grade systems |
| `library` | Research, documentation |
| `workshop` | Practical skills, tools |
| `garden` | Evolving knowledge |
| `observatory` | Exploration, patterns |

## Examples

```bash
# List all palaces with entry counts
/palace list

# Check queue size and palace health
/palace status

# Sync queued research into palaces (dry run first)
/palace sync --dry-run
/palace sync

# Create a new palace for a domain
/palace create "K8s Concepts" "kubernetes" --metaphor workshop

# View specific palace structure
/palace view abc123
```

## Data Flow

```
WebSearch/Research → data/intake_queue.jsonl
                            ↓
                    /palace sync
                            ↓
                    data/palaces/*.json
```

Research captured during sessions is automatically queued. Run `/palace sync` (or `/update-plugins` which includes it) to process queued items into palaces.

## CLI Integration

Uses `memory_palace_cli.py` from the plugin's scripts directory:

```bash
# Run from repository root with absolute paths
plugins/memory-palace/.venv/bin/python \
  plugins/memory-palace/scripts/memory_palace_cli.py <command> [args]

# Available commands: enable, disable, status, skills, install,
#                     garden, export, import, create, list, sync, prune, search, manager
```

**Requirements**:
- Plugin venv must be installed: `cd plugins/memory-palace && uv sync`
- Plugin must be enabled first: `<cli> enable`

**First-Time Setup**:
```bash
# 1. Enable the plugin (creates config)
plugins/memory-palace/.venv/bin/python \
  plugins/memory-palace/scripts/memory_palace_cli.py enable

# 2. Now you can list/create palaces
plugins/memory-palace/.venv/bin/python \
  plugins/memory-palace/scripts/memory_palace_cli.py list
```
