# Memory Palace Command

## Usage

Create and manage memory palaces for spatial knowledge organization.

### Create Palace
```
/palace create <name> <domain> [--metaphor <type>]
```
Creates a new memory palace with the specified name and domain.

### List Palaces
```
/palace list
```
Shows all existing memory palaces with their metadata.

### View Palace
```
/palace view <palace-id>
```
Displays the structure and contents of a specific palace.

### Delete Palace
```
/palace delete <palace-id>
```
Removes a palace (creates backup first).

### Status
```
/palace status
```
Shows overall memory palace system status and statistics.

## What It Does

1. **Creates Palaces**: Initializes new spatial knowledge structures
2. **Manages Lifecycle**: Handles creation, modification, and archival
3. **Tracks Metadata**: Maintains creation dates, concept counts, domains
4. **Provides Navigation**: Enables browsing palace contents
5. **Generates Reports**: Summarizes palace health and usage

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
# Create a palace for learning Kubernetes
/palace create "K8s Concepts" "kubernetes" --metaphor workshop

# List all palaces
/palace list

# Check system status
/palace status

# View specific palace
/palace view abc123
```

## Integration

Uses the palace_manager.py tool:
```bash
python scripts/palace_manager.py <command> [args]
```
