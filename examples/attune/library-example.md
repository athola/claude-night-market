# Library Example: Validation Framework

This example demonstrates architecture-aware initialization for a reusable library.

## Project Scenario

**Project**: Schema Validation Library
**Team**: 2 developers (small open-source project)
**Requirements**:
- Validate data against schemas
- Support multiple schema formats (JSON Schema, custom DSL)
- Type-safe API with good IDE support
- Minimal dependencies
- High performance for bulk validation
- Extensible with custom validators

## Workflow

### Step 1: Architecture-Aware Initialization

```bash
/attune:arch-init --name schema-validator
```

### Interactive Session

```
============================================================
Architecture-Aware Project Initialization
============================================================

Project Context
------------------------------------------------------------

Project Type: 5 (library)
Domain Complexity: 3 (Complex)
Team Size: 1 (< 5)
Programming Language: 1 (Python)
Framework: (none)
Scalability Needs: 2 (Moderate)
Security Requirements: 1 (Standard)
Time to Market: 3 (Not Urgent)
```

### Research Phase

```
============================================================
Online Research Phase
============================================================

Generated search queries for your project context:
------------------------------------------------------------

1. library architecture best practices 2026
   Command: WebSearch("library architecture best practices 2026")

2. python library architecture patterns 2026
   Command: WebSearch("python library architecture patterns 2026")

3. complex domain architecture patterns python
   Command: WebSearch("complex domain architecture patterns python")

------------------------------------------------------------

Research Focus Areas:
------------------------------------------------------------

  Industry Standards:
    Current architecture patterns for library in 2026

  Language Patterns:
    Python-specific best practices and idioms

  Domain Modeling:
    Domain-driven design patterns for complex business logic
```

### Recommendation

```
============================================================
Architecture Recommendation
============================================================

Primary Paradigm: **Hexagonal**
Secondary Paradigm: Functional Core

Confidence: HIGH

Rationale:
**Selected Based On**: matrix selection
**Team Size**: <5
**Domain Complexity**: complex
**Project Type**: library

Trade-offs:
  - **trade-off**: More boilerplate and indirection through ports/adapters
  - **mitigation**: Use code generation for adapters, keep ports minimal and stable
  - **best-for**: Systems requiring infrastructure flexibility, testability priority
  - **avoid-when**: Simple CRUD applications or very small teams

Alternatives Considered:
  - **Layered**: Less flexible for infrastructure changes
  - **Functional Core**: Functional patterns may be unfamiliar to team
  - **Modular Monolith**: Weak module boundaries for team size

============================================================

Accept this recommendation? [y/n]: y
```

### Generated Project Structure

```
schema-validator/
├── .attune/
│   └── arch-init-session.json
├── .github/
│   └── workflows/
│       ├── test.yml
│       ├── lint.yml
│       ├── typecheck.yml
│       └── publish.yml
├── docs/
│   └── adr/
│       └── 001-architecture-paradigm.md
├── src/
│   └── schema_validator/
│       ├── domain/                 # Core validation logic
│       │   ├── __init__.py
│       │   ├── models.py          # Schema and validation models
│       │   ├── services.py        # Validation services
│       │   └── ports/             # Interfaces
│       │       ├── __init__.py
│       │       ├── input.py       # Use case interfaces
│       │       └── output.py      # Repository interfaces
│       ├── infrastructure/        # External integrations
│       │   ├── __init__.py
│       │   ├── persistence/       # Schema loading
│       │   │   ├── __init__.py
│       │   │   └── repositories.py
│       │   ├── web/               # HTTP validation (optional)
│       │   │   ├── __init__.py
│       │   │   └── controllers.py
│       │   └── messaging/         # Async validation (optional)
│       │       ├── __init__.py
│       │       └── handlers.py
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── domain/
│   │   └── test_validation.py
│   └── infrastructure/
│       └── test_repositories.py
├── .gitignore
├── .pre-commit-config.yaml
├── ARCHITECTURE.md
├── Makefile
├── pyproject.toml
└── README.md
```

## Implementation Guidance

### Domain Models

```python
# src/schema_validator/domain/models.py
from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict
from enum import Enum

class ValidationSeverity(Enum):
    """Severity level for validation errors."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass(frozen=True)
class ValidationError:
    """A single validation error."""
    path: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    code: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"

@dataclass(frozen=True)
class ValidationResult:
    """Result of validating data against a schema."""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    @classmethod
    def success(cls) -> 'ValidationResult':
        """Create a successful validation result."""
        return cls(valid=True)

    @classmethod
    def failure(cls, errors: List[ValidationError]) -> 'ValidationResult':
        """Create a failed validation result."""
        return cls(valid=False, errors=errors)

    def __bool__(self) -> bool:
        return self.valid

@dataclass(frozen=True)
class SchemaField:
    """Definition of a schema field."""
    name: str
    type: str
    required: bool = False
    validators: List[str] = field(default_factory=list)
    default: Any = None
    description: Optional[str] = None

@dataclass(frozen=True)
class Schema:
    """A validation schema."""
    name: str
    version: str
    fields: List[SchemaField]
    strict: bool = False  # Reject unknown fields

    def get_field(self, name: str) -> Optional[SchemaField]:
        """Get field by name."""
        return next((f for f in self.fields if f.name == name), None)
```

### Domain Ports (Interfaces)

```python
# src/schema_validator/domain/ports/input.py
from abc import ABC, abstractmethod
from typing import Any, Dict
from schema_validator.domain.models import Schema, ValidationResult

class ValidateDataUseCase(ABC):
    """Use case for validating data against a schema."""

    @abstractmethod
    def execute(self, data: Dict[str, Any], schema: Schema) -> ValidationResult:
        """Validate data against schema."""
        ...

class ParseSchemaUseCase(ABC):
    """Use case for parsing schema definitions."""

    @abstractmethod
    def execute(self, schema_definition: str, format: str = "json") -> Schema:
        """Parse schema from string definition."""
        ...
```

```python
# src/schema_validator/domain/ports/output.py
from abc import ABC, abstractmethod
from typing import Optional
from schema_validator.domain.models import Schema

class SchemaRepository(ABC):
    """Repository for schema storage and retrieval."""

    @abstractmethod
    def get(self, name: str, version: Optional[str] = None) -> Optional[Schema]:
        """Get schema by name and optional version."""
        ...

    @abstractmethod
    def save(self, schema: Schema) -> None:
        """Save schema to repository."""
        ...

    @abstractmethod
    def list_versions(self, name: str) -> list[str]:
        """List all versions of a schema."""
        ...
```

### Domain Services

```python
# src/schema_validator/domain/services.py
from dataclasses import dataclass
from typing import Any, Dict, List, Callable, Optional
from schema_validator.domain.models import (
    Schema, SchemaField, ValidationResult, ValidationError, ValidationSeverity
)
from schema_validator.domain.ports.input import ValidateDataUseCase

# Type alias for validators
Validator = Callable[[Any, SchemaField], Optional[ValidationError]]

@dataclass
class ValidationService(ValidateDataUseCase):
    """Core validation service."""
    validators: Dict[str, Validator] = None

    def __post_init__(self):
        if self.validators is None:
            self.validators = get_default_validators()

    def execute(self, data: Dict[str, Any], schema: Schema) -> ValidationResult:
        """Validate data against schema."""
        errors: List[ValidationError] = []

        # Check for unknown fields if strict mode
        if schema.strict:
            known_fields = {f.name for f in schema.fields}
            for key in data.keys():
                if key not in known_fields:
                    errors.append(ValidationError(
                        path=key,
                        message=f"Unknown field '{key}' in strict schema",
                        code="UNKNOWN_FIELD"
                    ))

        # Validate each field
        for field in schema.fields:
            value = data.get(field.name)
            field_errors = self._validate_field(field, value)
            errors.extend(field_errors)

        if errors:
            return ValidationResult.failure(errors)
        return ValidationResult.success()

    def _validate_field(
        self,
        field: SchemaField,
        value: Any
    ) -> List[ValidationError]:
        """Validate a single field."""
        errors = []

        # Check required
        if field.required and value is None:
            errors.append(ValidationError(
                path=field.name,
                message=f"Field '{field.name}' is required",
                code="REQUIRED"
            ))
            return errors

        if value is None:
            return errors

        # Check type
        type_error = self._check_type(field.name, value, field.type)
        if type_error:
            errors.append(type_error)
            return errors

        # Run custom validators
        for validator_name in field.validators:
            if validator_name in self.validators:
                error = self.validators[validator_name](value, field)
                if error:
                    errors.append(error)

        return errors

    def _check_type(
        self,
        path: str,
        value: Any,
        expected_type: str
    ) -> Optional[ValidationError]:
        """Check if value matches expected type."""
        type_map = {
            "string": str,
            "integer": int,
            "float": (int, float),
            "boolean": bool,
            "list": list,
            "dict": dict,
        }

        expected = type_map.get(expected_type)
        if expected and not isinstance(value, expected):
            return ValidationError(
                path=path,
                message=f"Expected {expected_type}, got {type(value).__name__}",
                code="TYPE_MISMATCH"
            )
        return None


def get_default_validators() -> Dict[str, Validator]:
    """Get default validators."""
    return {
        "email": validate_email,
        "url": validate_url,
        "min_length": validate_min_length,
        "max_length": validate_max_length,
        "pattern": validate_pattern,
    }

def validate_email(value: Any, field: SchemaField) -> Optional[ValidationError]:
    """Validate email format."""
    import re
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", str(value)):
        return ValidationError(
            path=field.name,
            message="Invalid email format",
            code="INVALID_EMAIL"
        )
    return None

def validate_url(value: Any, field: SchemaField) -> Optional[ValidationError]:
    """Validate URL format."""
    from urllib.parse import urlparse
    try:
        result = urlparse(str(value))
        if not all([result.scheme, result.netloc]):
            raise ValueError()
    except Exception:
        return ValidationError(
            path=field.name,
            message="Invalid URL format",
            code="INVALID_URL"
        )
    return None

def validate_min_length(value: Any, field: SchemaField) -> Optional[ValidationError]:
    """Validate minimum length."""
    min_len = field.context.get("min_length", 0)
    if len(str(value)) < min_len:
        return ValidationError(
            path=field.name,
            message=f"Minimum length is {min_len}",
            code="MIN_LENGTH"
        )
    return None

def validate_max_length(value: Any, field: SchemaField) -> Optional[ValidationError]:
    """Validate maximum length."""
    max_len = field.context.get("max_length", float('inf'))
    if len(str(value)) > max_len:
        return ValidationError(
            path=field.name,
            message=f"Maximum length is {max_len}",
            code="MAX_LENGTH"
        )
    return None

def validate_pattern(value: Any, field: SchemaField) -> Optional[ValidationError]:
    """Validate against regex pattern."""
    import re
    pattern = field.context.get("pattern")
    if pattern and not re.match(pattern, str(value)):
        return ValidationError(
            path=field.name,
            message=f"Does not match pattern: {pattern}",
            code="PATTERN_MISMATCH"
        )
    return None
```

### Infrastructure (File-based Repository)

```python
# src/schema_validator/infrastructure/persistence/repositories.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import json

from schema_validator.domain.models import Schema, SchemaField
from schema_validator.domain.ports.output import SchemaRepository

@dataclass
class FileSchemaRepository(SchemaRepository):
    """File-based schema repository."""
    base_path: Path

    def get(self, name: str, version: Optional[str] = None) -> Optional[Schema]:
        """Load schema from file."""
        if version:
            path = self.base_path / name / f"{version}.json"
        else:
            # Get latest version
            versions = self.list_versions(name)
            if not versions:
                return None
            path = self.base_path / name / f"{versions[-1]}.json"

        if not path.exists():
            return None

        return self._parse_schema(path)

    def save(self, schema: Schema) -> None:
        """Save schema to file."""
        schema_dir = self.base_path / schema.name
        schema_dir.mkdir(parents=True, exist_ok=True)

        path = schema_dir / f"{schema.version}.json"
        path.write_text(json.dumps(self._schema_to_dict(schema), indent=2))

    def list_versions(self, name: str) -> List[str]:
        """List all versions of a schema."""
        schema_dir = self.base_path / name
        if not schema_dir.exists():
            return []

        versions = [p.stem for p in schema_dir.glob("*.json")]
        return sorted(versions)

    def _parse_schema(self, path: Path) -> Schema:
        """Parse schema from JSON file."""
        data = json.loads(path.read_text())
        fields = [
            SchemaField(
                name=f["name"],
                type=f["type"],
                required=f.get("required", False),
                validators=f.get("validators", []),
                default=f.get("default"),
                description=f.get("description"),
            )
            for f in data["fields"]
        ]
        return Schema(
            name=data["name"],
            version=data["version"],
            fields=fields,
            strict=data.get("strict", False)
        )

    def _schema_to_dict(self, schema: Schema) -> dict:
        """Convert schema to dictionary."""
        return {
            "name": schema.name,
            "version": schema.version,
            "strict": schema.strict,
            "fields": [
                {
                    "name": f.name,
                    "type": f.type,
                    "required": f.required,
                    "validators": f.validators,
                    "default": f.default,
                    "description": f.description,
                }
                for f in schema.fields
            ]
        }
```

### Public API

```python
# src/schema_validator/__init__.py
"""Schema Validator - A flexible schema validation library."""

from schema_validator.domain.models import (
    Schema,
    SchemaField,
    ValidationResult,
    ValidationError,
    ValidationSeverity,
)
from schema_validator.domain.services import ValidationService
from schema_validator.infrastructure.persistence.repositories import (
    FileSchemaRepository,
)

__version__ = "0.1.0"

__all__ = [
    # Models
    "Schema",
    "SchemaField",
    "ValidationResult",
    "ValidationError",
    "ValidationSeverity",
    # Services
    "ValidationService",
    # Repositories
    "FileSchemaRepository",
    # Convenience functions
    "validate",
]

def validate(data: dict, schema: Schema) -> ValidationResult:
    """Convenience function to validate data against a schema.

    Args:
        data: Dictionary of data to validate
        schema: Schema to validate against

    Returns:
        ValidationResult with validation outcome

    Example:
        >>> schema = Schema(
        ...     name="user",
        ...     version="1.0",
        ...     fields=[
        ...         SchemaField(name="email", type="string", required=True, validators=["email"]),
        ...         SchemaField(name="age", type="integer", required=False),
        ...     ]
        ... )
        >>> result = validate({"email": "user@example.com", "age": 25}, schema)
        >>> result.valid
        True
    """
    service = ValidationService()
    return service.execute(data, schema)
```

## Why Hexagonal Architecture for Libraries?

For this library project:

1. **Infrastructure Independence**: Users can provide their own storage (files, databases, remote)
2. **Testability**: Core validation logic is pure and easily testable
3. **Extensibility**: New validators can be added without changing core
4. **Clean API**: Public API hides implementation details
5. **Future-Proof**: Can add HTTP/async adapters without breaking existing users

## Testing Strategy

```python
# tests/domain/test_validation.py
import pytest
from schema_validator import Schema, SchemaField, ValidationService

@pytest.fixture
def user_schema():
    return Schema(
        name="user",
        version="1.0",
        fields=[
            SchemaField(name="email", type="string", required=True, validators=["email"]),
            SchemaField(name="age", type="integer", required=False),
            SchemaField(name="name", type="string", required=True),
        ]
    )

class TestValidationService:
    def test_valid_data(self, user_schema):
        service = ValidationService()
        result = service.execute(
            {"email": "test@example.com", "name": "Test User", "age": 25},
            user_schema
        )
        assert result.valid
        assert len(result.errors) == 0

    def test_missing_required_field(self, user_schema):
        service = ValidationService()
        result = service.execute(
            {"email": "test@example.com"},  # Missing 'name'
            user_schema
        )
        assert not result.valid
        assert any(e.code == "REQUIRED" for e in result.errors)

    def test_invalid_email(self, user_schema):
        service = ValidationService()
        result = service.execute(
            {"email": "not-an-email", "name": "Test"},
            user_schema
        )
        assert not result.valid
        assert any(e.code == "INVALID_EMAIL" for e in result.errors)
```

## Next Steps

After initialization:

1. **Set up development environment**:
   ```bash
   cd schema-validator
   make dev-setup
   ```

2. **Run tests**:
   ```bash
   make test
   ```

3. **Build documentation**:
   ```bash
   make docs
   ```

4. **Publish to PyPI**:
   ```bash
   make publish
   ```
