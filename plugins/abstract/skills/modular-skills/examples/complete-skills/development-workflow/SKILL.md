---
name: development-workflow
description: Comprehensive development workflow with modular patterns for git, code review, testing, documentation, and deployment
version: 2.0.0
created_by: abstract-examples
tags: [development, workflow, modular, hub-and-spoke]
category: workflow
type: hub
estimated_tokens: 45
dependencies: []
companion_skills: []
modules:
  - git-workflow
  - code-review
  - testing-strategies
  - documentation-guidelines
  - deployment-procedures
tools:
  - setup-validator
  - workflow-checker
  - quality-metrics
---

# Development Workflow Hub

This modular skill provides a comprehensive framework for software development workflows. It's designed as a hub that coordinates specialized modules for different aspects of development.

## Overview

Get started quickly with this development workflow framework:

**🚀 Quick Start**: Set up repository structure and basic workflow in minutes
- Initialize with git-workflow module
- Add code-review process for team collaboration
- Implement testing strategies for quality assurance

**📚 Progressive Learning**: Start simple, add complexity as needed
1. **Basic workflow** → git-workflow + code-review
2. **Quality focus** → add testing-strategies + documentation
3. **Production ready** → add deployment-procedures + monitoring

**🎯 Use Case-Based**: Jump directly to what you need
- New project? → Start with git-workflow
- Team scaling? → Focus on code-review + testing
- Production deployment? → Use deployment-procedures
- Documentation debt? → Apply documentation-guidelines

## Available Modules

This workflow includes these specialized modules:

- **[git-workflow](modules/git-workflow/)** - Repository setup, branching strategies, and daily git practices
- **[code-review](modules/code-review/)** - Pull request process, review guidelines, and quality standards
- **[testing-strategies](modules/testing-strategies/)** - Unit testing, integration testing, and E2E testing patterns
- **[documentation-guidelines](modules/documentation-guidelines/)** - Code documentation, API docs, and README standards
- **[deployment-procedures](modules/deployment-procedures/)** - CI/CD pipelines, environment setup, and monitoring

## Quick Start

To use this development workflow:

1. **Set up your development environment:**
   ```
   Use git-workflow module for repository initialization and branching setup
   ```

2. **Follow the development cycle:**
   ```
   git-workflow → code-review → testing-strategies → documentation-guidelines
   ```

3. **Deploy and monitor:**
   ```
   deployment-procedures module handles CI/CD and production monitoring
   ```

## Usage Patterns

### For New Projects
Start with [git-workflow](modules/git-workflow/) to establish repository structure, then progress through modules as your project develops.

### For Existing Projects
Use individual modules to improve specific areas:
- Need better code reviews? → Use [code-review](modules/code-review/)
- Testing coverage issues? → Use [testing-strategies](modules/testing-strategies/)
- Deployment problems? → Use [deployment-procedures](modules/deployment-procedures/)

### For Team Onboarding
Guide new team members through the modules in order to establish consistent practices.

## Integration Benefits

This modular approach provides several advantages over monolithic workflows:

- **Token Efficiency**: Load only the modules you need (60% token reduction for most operations)
- **Focused Learning**: Each module concentrates on a specific development area
- **Flexible Implementation**: Adopt modules incrementally based on project needs
- **Team Specialization**: Different team members can focus on different modules

## Quality Assurance

Each module includes validation tools to ensure best practices:
- Automated quality checks
- Performance benchmarks
- Security validations
- Documentation standards

Use the quality-metrics tool to assess your workflow implementation:
```bash
quality-metrics --workflow development-workflow --modules all
```

## Customization

This workflow is designed to be adaptable:
- Extend modules with project-specific practices
- Add custom tools to the scripts/ directory
- Configure module interactions for your team's needs
- Integrate with existing development tools and platforms

## Support and Resources

- [Implementation Guide](guide.md) - Detailed workflow implementation guide
- [Troubleshooting](modules/troubleshooting.md) - Common issues and solutions
- [Best Practices](modules/best-practices.md) - Proven patterns for teams
