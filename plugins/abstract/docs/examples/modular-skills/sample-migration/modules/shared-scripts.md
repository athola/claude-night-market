# Shared Scripts Implementation

## Script 1: `scripts/api-validator`
```bash
#!/bin/bash
# Validates API specifications against best practices
python3 scripts/validate_openapi.py --input "$1" --strict
```

**Features:**
- OpenAPI specification validation
- Best practices enforcement
- Security pattern checking
- Schema consistency verification

**Usage:**
```bash
./api-validator petstore.yaml
./api-validator --strict api-spec.json
```

## Script 2: `scripts/test-generator`
```python
#!/usr/bin/env python3
# Generates integration tests from OpenAPI specifications
from openapi_test_generator import generate_tests
generate_tests.from_spec(args.input, args.output)
```

**Features:**
- Automated test case generation
- Multiple framework support
- Mock data generation
- Contract test creation

**Usage:**
```python
./test-generator --input petstore.yaml --output tests/
./test-generator --framework pytest --input api.json
```

## Script 3: `scripts/doc-generator`
```python
#!/usr/bin/env python3
# Generates documentation from API specifications
from swagger_doc_generator import generate_docs
generate_docs.from_openapi(args.input, args.output_dir)
```

**Features:**
- Interactive API documentation
- Code example generation
- Multiple format outputs
- API explorer integration

**Usage:**
```python
./doc-generator --input petstore.yaml --output docs/
./doc-generator --format html --input api.json
```

## Script Benefits
- **Automation**: Replaces manual processes
- **Consistency**: Standardized outputs
- **Integration**: Works across all modules
- **Efficiency**: Reduces repetitive tasks

## Script Integration
- All scripts executable from command line
- Shared configuration across modules
- Consistent output formats
- Error handling and validation

## Quick Start
1. Make scripts executable: `chmod +x scripts/*`
2. Test with example files: `./api-validator examples/petstore.yaml`
3. Generate detailed workflow: `./doc-generator && ./test-generator`

## Integration
Continue with **migration-results** to see the overall improvements achieved.
