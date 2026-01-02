---
name: documentation-guidelines
description: Best practices for code documentation, API documentation, README standards, and technical writing for developers
version: 1.0.0
created_by: abstract-examples
tags: [documentation, technical-writing, api-docs, readme, best-practices]
category: development
type: module
estimated_tokens: 100
dependencies: []
companion_skills: []
modules: []
tools:
  - doc-validator
  - api-generator
  - readme-checker
---

# Documentation Guidelines

detailed documentation framework that validates clear, maintainable, and user-friendly documentation for code, APIs, and project documentation.

## Overview

Master documentation practices with this detailed framework:

** Quick Start**: Get your documentation working effectively in 10 minutes
- Set up README template and API docs structure
- Define documentation standards and review process
- Start documenting with clear examples and usage guides

**Progressive Learning**: Build documentation expertise gradually
1. **Foundation** → README basics + inline comments + simple examples
2. **Developer Focus** → API documentation + architecture guides + tutorials
3. **User Focus** → User guides + troubleshooting + detailed examples

** Use Case-Based**: Jump directly to what you need right now
- New project? → Focus on README template + documentation structure
- API development? → Apply API docs + code examples + integration guides
- User onboarding? → Create getting-started guides + tutorials
- Legacy code? → Document architecture + add inline comments + examples

## Documentation Types

### README Files
Project README files should include:

#### Essential Sections
```markdown
# Project Name

Brief description of what the project does.

## Quick Start
Minimal steps to get the project running.

## Installation
Detailed installation instructions with prerequisites.

## Usage
Basic usage examples and common scenarios.

## API Reference
Link to detailed API documentation.

## Contributing
Guidelines for contributing to the project.

## License
Project license information.
```

#### README Best Practices
- Start with a clear, concise description
- Include installation and usage examples
- Add badges for build status, coverage, etc.
- Provide links to detailed documentation
- Keep README focused on getting started

### Code Documentation

#### Inline Comments
```python
def process_user_data(user_input):
    """
    Process user input and return validated response.

    Args:
        user_input (str): Raw user input to process

    Returns:
        dict: Processed and validated user data

    Raises:
        ValidationError: If input is invalid or malformed
    """
    # Validate input format and structure
    if not validate_input_format(user_input):
        raise ValidationError("Invalid input format")

    # Process input through validation pipeline
    processed_data = validation_pipeline(user_input)

    return processed_data
```

#### Documentation Standards
- Document all public functions and classes
- Include parameter types, return types, and exceptions
- Provide usage examples for complex functions
- Explain the "why" behind implementation decisions
- Keep comments current with code changes

### API Documentation

#### API Endpoint Documentation
```yaml
# /api/users endpoint
endpoint: /api/users
method: POST
description: Create a new user account

parameters:
  - name: email
    type: string
    required: true
    description: User's email address
  - name: password
    type: string
    required: true
    description: User's password (min 8 characters)

responses:
  201:
    description: User created successfully
    schema:
      type: object
      properties:
        id:
          type: integer
          description: User ID
        email:
          type: string
          description: User email
  400:
    description: Invalid input data
    schema:
      $ref: '#/components/schemas/Error'
```

#### API Documentation Best Practices
- Document all endpoints, parameters, and responses
- Include example requests and responses
- Provide authentication and authorization information
- Include error codes and handling guidance
- Show integration examples

### Architecture Documentation

#### System Architecture
```markdown
# System Architecture

## Components
- **API Gateway**: Routes requests to appropriate services
- **User Service**: Handles user authentication and data
- **Data Service**: Manages data persistence and retrieval
- **Cache Layer**: Redis for session and data caching

## Data Flow
1. Client request → API Gateway
2. Authentication → User Service
3. Data operations → Data Service
4. Response caching → Cache Layer
5. Final response → Client

## Technology Stack
- Backend: Node.js with Express
- Database: PostgreSQL with connection pooling
- Cache: Redis with TTL management
- Monitoring: Prometheus + Grafana
```

#### Architecture Documentation Guidelines
- Use diagrams to visualize system components
- Document data flow and interactions
- Include technology stack and versions
- Explain design decisions and trade-offs
- Keep documentation updated with architecture changes

## Documentation Tools

### Documentation Generators
- **Sphinx**: For Python projects with auto-generated API docs
- **JSDoc**: For JavaScript API documentation
- **Swagger/OpenAPI**: For REST API documentation
- **MkDocs**: For static site documentation

### Documentation Quality Tools
- **Grammar and spelling checkers**: validate writing quality
- **Link checkers**: Validate internal and external links
- **Example testers**: Verify code examples work correctly
- **Documentation coverage**: Track undocumented components

## Writing Guidelines

### Technical Writing Best Practices
- Use clear, concise language
- Define technical terms and acronyms
- Use active voice and present tense
- Include relevant examples and use cases
- Structure information logically

### Documentation Structure
1. **Overview**: High-level introduction
2. **Prerequisites**: Required setup and knowledge
3. **Getting Started**: Quick start guide
4. **Detailed Usage**: detailed guide
5. **Examples**: Practical use cases
6. **Reference**: Complete technical reference
7. **Troubleshooting**: Common issues and solutions

### Examples and Tutorials
- Provide working code examples
- Show common use cases and patterns
- Include step-by-step tutorials
- Demonstrate error handling
- Keep examples updated and tested

## Documentation Review

### Review Checklist
- [ ] Installation instructions work correctly
- [ ] Code examples are tested and functional
- [ ] API documentation is complete and accurate
- [ ] Common use cases are covered
- [ ] Troubleshooting section addresses frequent issues
- [ ] Links and references are valid
- [ ] Documentation follows style guidelines

### Review Process
- Technical accuracy validation
- User testing of documentation
- Peer review for clarity and completeness
- Regular updates and maintenance

This documentation framework helps teams create detailed, maintainable documentation that serves both developers and users effectively through clear standards and practical guidelines.
