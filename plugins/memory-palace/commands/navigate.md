# Navigate Command

## Usage

Search and navigate across memory palaces to find and retrieve information.

### Search
```
/navigate search "<query>" [--type semantic|exact|fuzzy] [--palace <id>]
```
Searches for concepts across palaces.

### Locate
```
/navigate locate "<concept>" [--palace <id>]
```
Finds the exact location of a specific concept.

### Path
```
/navigate path "<from-concept>" "<to-concept>"
```
Shows the navigation path between two concepts.

### Explore
```
/navigate explore <palace-id> [--depth <levels>]
```
Lists concepts reachable from a starting point.

## What It Does

1. **Multi-Modal Search**: Finds concepts using semantic, exact, or fuzzy matching
2. **Cross-Palace Search**: Searches across all palaces simultaneously
3. **Path Finding**: Calculates routes between concepts
4. **Discovery**: Suggests related concepts for exploration
5. **Access Tracking**: Records search patterns for optimization

## Search Types

| Type | Description | Best For |
|------|-------------|----------|
| `semantic` | Meaning-based matching (default) | General queries |
| `exact` | Exact string match | Known concept names |
| `fuzzy` | Partial/approximate match | Uncertain queries |

## Examples

```bash
# Search for authentication concepts
/navigate search "authentication" --type semantic

# Find OAuth specifically
/navigate locate "OAuth 2.0"

# Path from one concept to another
/navigate path "OAuth" "JWT"

# Explore a palace
/navigate explore abc123 --depth 2
```

## Output

Returns search results with:
- **Match location**: Palace, district, building, room
- **Relevance score**: How closely it matches the query
- **Connections**: Related concepts nearby
- **Last accessed**: When the concept was last retrieved

## Integration

Uses the palace_manager.py search functionality:
```bash
python scripts/palace_manager.py search "<query>" --type <type>
```
