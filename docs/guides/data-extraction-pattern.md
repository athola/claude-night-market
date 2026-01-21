# Data Extraction Pattern: Separating Data from Code

**Purpose**: Reduce script token footprint by extracting embedded data to YAML configuration files

**Benefits**: 75% average code reduction, easier maintenance, non-programmer editable

---

## The Problem

Large Python scripts often embed data directly in code, leading to several maintenance challenges. When data changes require code modifications, it increases the risk of introducing bugs in the logic. Large data structures also bloat script files, making them harder to read and navigate. Furthermore, this pattern prevents non-programmers from updating catalogs or templates and results in messy diffs when data changes.

---

## The Solution Pattern

### 5-Step Refactoring Process

#### 1. Identify Embedded Data
Look for:
- Large dictionaries, lists, or constants (>100 lines)
- Configuration data mixed with logic
- Templates, catalogs, or lookup tables
- Data that changes independently of code logic

#### 2. Extract to YAML
Create `data/` directory and design schema:

```yaml
# data/seed_topics.yaml
topics:
  - id: python-best-practices
    category: programming
    title: Python Best Practices
    subtopics:
      - type-hints
      - error-handling
      - testing
```

#### 3. Add Deserialization
Create loader function and dataclass methods:

```python
from pathlib import Path
import yaml
from dataclasses import dataclass

DATA_DIR = Path(__file__).parent.parent / "data"
TOPICS_FILE = DATA_DIR / "seed_topics.yaml"

@dataclass
class Topic:
    id: str
    category: str
    title: str
    subtopics: list[str]

    @classmethod
    def from_dict(cls, data: dict) -> 'Topic':
        """Deserialize from YAML dict."""
        return cls(
            id=data["id"],
            category=data["category"],
            title=data["title"],
            subtopics=data.get("subtopics", [])
        )

def load_topics() -> list[Topic]:
    """Load topics from YAML configuration."""
    if not TOPICS_FILE.exists():
        raise FileNotFoundError(f"Topics file not found: {TOPICS_FILE}")

    with open(TOPICS_FILE) as f:
        data = yaml.safe_load(f)

    return [Topic.from_dict(t) for t in data["topics"]]
```

#### 4. Update Script
Replace embedded data with loader calls:

```python
# Before
topics = _topics()  # Calls 830-line function

# After
topics = load_topics()  # Loads from YAML
```

#### 5. Validate
- Test script works with loaded data
- Compare outputs before/after
- Check error handling (missing files, malformed YAML)

---

## Real-World Examples

### Example 1: Seed Corpus (Memory Palace)

**Before**: 1,117 lines
**After**: ~285 lines + YAML data file
**Savings**: ~832 lines (75%)

**What was extracted**:
- Topic catalog with 100+ entries
- Nested subtopic hierarchies
- Category mappings

### Example 2: Architecture Templates (Attune)

**Before**: 792 lines
**After**: ~130 lines + YAML data file
**Savings**: ~662 lines (84%)

**What was extracted**:
```yaml
templates:
  functional-core:
    description: "Functional Core, Imperative Shell pattern"
    python_structure:
      - "src/{module}/core/__init__.py"
      - "src/{module}/core/domain.py"
      - "src/{module}/shell/cli.py"
    rust_structure:
      - "src/core/mod.rs"
      - "src/shell/main.rs"
```

### Example 3: Makefile Targets (Abstract)

**Before**: 793 lines
**After**: ~200 lines + YAML data file
**Savings**: ~593 lines (75%)

**What was extracted**:
- Essential target definitions
- Target safety levels (safe/conditional/risky)
- Skip directories configuration
- Recommended targets by project type

### Example 4: Decision Matrix (Attune)

**Before**: 641 lines
**After**: ~180 lines + YAML data file
**Savings**: ~461 lines (72%)

**What was extracted**:
- Paradigm selection matrix
- Project type modifiers
- Scalability modifiers
- Security requirements

---

## Code Template

```python
"""
Example refactored script with data extraction.
"""
from pathlib import Path
from dataclasses import dataclass
import yaml

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CONFIG_FILE = DATA_DIR / "config.yaml"

@dataclass
class ConfigItem:
    """Configuration item."""
    name: str
    value: str
    options: dict

    @classmethod
    def from_dict(cls, data: dict) -> 'ConfigItem':
        """Deserialize from YAML dict."""
        return cls(
            name=data["name"],
            value=data["value"],
            options=data.get("options", {})
        )

def load_config() -> dict:
    """
    Load configuration from YAML file.

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file missing
        yaml.YAMLError: If config malformed
    """
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_FILE}\n"
            f"Expected location: {CONFIG_FILE.absolute()}"
        )

    try:
        with open(CONFIG_FILE) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in {CONFIG_FILE}: {e}")

    return data

class MyProcessor:
    """Main processor using loaded configuration."""

    def __init__(self):
        # Load configuration at initialization
        config_data = load_config()
        self.items = [
            ConfigItem.from_dict(item)
            for item in config_data.get("items", [])
        ]

    def process(self):
        """Process using loaded configuration."""
        for item in self.items:
            print(f"Processing {item.name}: {item.value}")
```

---

## Best Practices

### YAML Schema Documentation

Document your YAML structure:

```yaml
# data/config.yaml
#
# Schema:
#   items: list of configuration items
#     - name: string (required) - Item identifier
#     - value: string (required) - Item value
#     - options: dict (optional) - Additional options
#       - enabled: bool - Whether item is active
#       - priority: int - Processing priority (1-10)
#
items:
  - name: example
    value: test
    options:
      enabled: true
      priority: 5
```

### Error Handling

Provide clear error messages:

```python
def load_config() -> dict:
    """Load with detailed error handling."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Configuration missing: {CONFIG_FILE}\n"
            f"Create it with: cp config.example.yaml {CONFIG_FILE}"
        )

    try:
        with open(CONFIG_FILE) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Malformed YAML in {CONFIG_FILE}: {e}")

    # Validate required fields
    if "items" not in data:
        raise ValueError(f"Missing required 'items' key in {CONFIG_FILE}")

    return data
```

### Defaults and Secondary Values

Handle missing optional fields:

```python
@classmethod
def from_dict(cls, data: dict) -> 'ConfigItem':
    """Deserialize with sensible defaults."""
    return cls(
        name=data["name"],
        value=data.get("value", ""),  # Default to empty string
        options=data.get("options", {}),  # Default to empty dict
        enabled=data.get("enabled", True),  # Default to enabled
        priority=data.get("priority", 5)  # Default to medium priority
    )
```

### Version Migration

Support schema evolution:

```python
def load_config(version: str = "2.0") -> dict:
    """Load configuration with version migration."""
    with open(CONFIG_FILE) as f:
        data = yaml.safe_load(f)

    config_version = data.get("version", "1.0")

    # Migrate old versions
    if config_version == "1.0" and version == "2.0":
        data = migrate_v1_to_v2(data)

    return data

def migrate_v1_to_v2(data: dict) -> dict:
    """Migrate v1.0 schema to v2.0."""
    # Example: Rename field
    for item in data["items"]:
        if "old_field" in item:
            item["new_field"] = item.pop("old_field")

    data["version"] = "2.0"
    return data
```

---

## When to Apply This Pattern

### Good Candidates
- Configuration catalogs (>100 lines)
- Template definitions
- Lookup tables and mappings
- Large constant definitions
- Data that changes independently of code
- Domain-specific knowledge bases

### Poor Candidates
- Small constants (<20 lines)
- Data tightly coupled to code logic
- Computed values (use code, not data)
- Performance-critical hot paths
- Data with complex interdependencies

---

## Impact Metrics

From 4 real-world refactorings:

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Total Lines** | 3,343 | ~795 | -76% |
| **Token Savings** | - | ~10,192 | - |
| **Files Created** | 4 scripts | 4 scripts + 4 YAML | +4 data files |
| **Avg Reduction** | - | 75% | - |

### Individual Results
- **seed_corpus.py**: 1,117 → 285 lines (75% reduction)
- **makefile_dogfooder.py**: 793 → 200 lines (75% reduction)
- **template_customizer.py**: 792 → 130 lines (84% reduction)
- **architecture_researcher.py**: 641 → 180 lines (72% reduction)

---

## Integration with Other Patterns

### Progressive Disclosure
Combine with hub-and-spoke documentation:
- Hub document references YAML schema
- Detailed documentation in separate files
- Examples load from data files on-demand

### Lazy Loading
Load data only when needed:

```python
class Processor:
    def __init__(self):
        self._config = None  # Lazy-loaded

    @property
    def config(self) -> dict:
        """Lazy-load configuration."""
        if self._config is None:
            self._config = load_config()
        return self._config
```

### Shared Utilities
Create reusable YAML loaders:

```python
# utils/config_loader.py
def load_yaml_config(file_path: Path, schema_version: str = "1.0") -> dict:
    """Generic YAML config loader with validation."""
    # Reusable across multiple scripts
```

---

## Common Pitfalls

### 1. Type Safety Loss
**Problem**: YAML is untyped, runtime errors possible

**Solution**: Validate at load time
```python
from typing import TypedDict

class TopicDict(TypedDict):
    id: str
    category: str
    title: str

def validate_topic(data: dict) -> TopicDict:
    """Validate topic structure."""
    required = ["id", "category", "title"]
    missing = [f for f in required if f not in data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    return data  # type: ignore
```

### 2. Complex Nested Data
**Problem**: Deeply nested structures hard to maintain

**Solution**: Flatten or split into multiple files
```yaml
# Instead of deep nesting:
templates:
  paradigm1:
    languages:
      python:
        files: [...]
      rust:
        files: [...]

# Flatten:
templates:
  - id: paradigm1-python
    files: [...]
  - id: paradigm1-rust
    files: [...]
```

### 3. Circular Dependencies
**Problem**: Data references itself

**Solution**: Use IDs and resolve after loading
```python
def resolve_references(items: list[Item]) -> list[Item]:
    """Resolve ID-based references after loading."""
    item_map = {item.id: item for item in items}
    for item in items:
        if item.parent_id:
            item.parent = item_map.get(item.parent_id)
    return items
```

---

## See Also

- [Progressive Disclosure Pattern](./documentation-standards.md#progressive-disclosure)
- [Optimization Patterns](../optimization-patterns.md)
- [Plugin Overview](../../book/src/plugins/README.md)

---

**Pattern Status**: Production-ready
**Applied to**: 4 scripts in claude-night-market (Memory Palace, Abstract, Attune)
**Maintained by**: claude-night-market core team
