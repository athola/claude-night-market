# Hub Extraction Strategy

## Step 1: Extract Core Hub

Create `api-development/SKILL.md` (45 lines):
```yaml
---
name: api-development
description: Complete API development workflow from design to deployment
category: development
tags: [api, rest, graphql, testing, documentation]
dependencies: [testing-skills, documentation-standards]
scripts: [api-validator, test-generator, doc-generator]
usage_patterns:
  - api-design
  - api-testing
  - api-documentation
  - api-deployment
complexity: intermediate
estimated_tokens: 800
---

# API Development Framework

## Overview
API development workflow covering design, testing, documentation, and deployment.

## Quick Start
1. **Design**: Use `api-validator` to validate API specifications
2. **Test**: Generate tests with `test-generator`
3. **Document**: Create docs with `doc-generator`
4. **Deploy**: Follow deployment checklist

## Available Modules
- `api-design/`: API design patterns and best practices
- `api-testing/`: Testing strategies and automation
- `api-documentation/`: Documentation generation and maintenance
- `api-deployment/`: Deployment patterns and CI/CD

## Detailed Resources
- Implementation guide: `guide.md`
- Examples: `examples/`
- Scripts: `scripts/`
```

## Benefits of Hub-First Approach
- Clear entry point and overview
- Progressive disclosure structure
- Contextual module loading
- Reduced initial token cost

## Key Features
- **Progressive Loading**: Load only needed modules
- **Clear Boundaries**: Each module has specific responsibility
- **Shared Tools**: Common functionality in tools directory
- **Flexible Usage**: Multiple loading patterns supported

## Integration
Continue with **focused-modules** to see the individual module implementations.
