# Plugin Development Guide

Welcome to the comprehensive guide for developing Claude Night Market plugins. This guide consolidates all development resources, best practices, and tools to help you create high-quality plugins.

## 🎯 Quick Start

1. **[Developer Portal](../developer-portal/)** - Complete developer experience
2. **[Getting Started](../developer-portal/getting-started/)** - Set up and first plugin
3. **[Templates](../developer-portal/templates/)** - Ready-to-use starting points
4. **[Examples](../developer-portal/examples/)** - Learn from real implementations

## 📚 Navigation

### 🚀 Getting Started
New to plugin development? Start here:

- [Development Environment Setup](../developer-portal/getting-started/environment-setup.md)
- [Architecture Overview](../developer-portal/getting-started/architecture-overview.md)
- [Build Your First Plugin](../developer-portal/getting-started/first-plugin.md)

### 📖 Guidelines & Standards
Follow these guidelines to create high-quality plugins:

- [Plugin Development Best Practices](../developer-portal/guidelines/plugin-development.md)
- [Code Quality Standards](../developer-portal/guidelines/code-quality.md)
- [Testing Strategies](../developer-portal/guidelines/testing.md)
- [Security Guidelines](../developer-portal/guidelines/security.md)
- [API Design Guidelines](../developer-portal/guidelines/api-design.md)

### 🛠️ Templates & Tools
Accelerate development with templates and automation:

- [Plugin Templates](../developer-portal/templates/)
- [Plugin Generator](../developer-portal/automation/plugin-generator.py)
- [Automation Scripts](../developer-portal/automation/)

### 📚 Examples & Patterns
Learn from real-world implementations:

- [Example Implementations](../developer-portal/examples/)
- [Pattern Library](../developer-portal/patterns/)

### 🔗 Integration
Integrate with the ecosystem:

- [Marketplace Submission](../developer-portal/guidelines/marketplace-submission.md)
- [Version Compatibility](../developer-portal/guidelines/version-compatibility.md)
- [Inter-plugin Communication](../developer-portal/guidelines/inter-plugin-communication.md)

## 🏗️ Plugin Architecture

### Core Components
```
Plugin Structure
├── Skills          - Interactive capabilities
├── Commands        - Slash commands
├── Agents          - Specialized AI assistants
├── Hooks           - Event-driven automation
├── Scripts         - Python utilities
└── Configuration   - Plugin metadata
```

### Design Principles
1. **User Experience First** - Clear, predictable behavior
2. **Developer Experience** - Consistent patterns, good tooling
3. **Ecosystem Health** - Interoperability, security, performance

## 📊 Success Metrics

### Quality Standards
- ✅ Test coverage > 80%
- ✅ All linting passes
- ✅ Security scan clean
- ✅ Documentation complete
- ✅ Performance optimized

### User Experience
- ✅ Clear purpose and value
- ✅ Easy discovery and use
- ✅ Helpful error messages
- ✅ Good examples and docs

### Ecosystem Fit
- ✅ Follows established patterns
- ✅ Integrates well with others
- ✅ Backward compatible
- ✅ Proper versioning

## 🛣️ Development Path

### Phase 1: Foundation
1. Set up development environment
2. Understand the architecture
3. Build a simple plugin
4. Learn the patterns

### Phase 2: Expansion
1. Add multiple skills
2. Implement commands
3. Include automation
4. Add comprehensive tests

### Phase 3: Production
1. Optimize performance
2. Add security measures
3. Document thoroughly
4. Submit to marketplace

### Phase 4: Maintenance
1. Monitor usage
2. Fix issues
3. Add features
4. Keep dependencies updated

## 🔧 Essential Tools

### Development
- **Python 3.10+** - Primary language
- **uv** - Package manager
- **Git** - Version control
- **VS Code/PyCharm** - IDE (recommended)

### Quality Assurance
- **pytest** - Testing framework
- **ruff** - Linting and formatting
- **mypy** - Type checking
- **bandit** - Security scanning

### Automation
- **pre-commit** - Git hooks
- **GitHub Actions** - CI/CD
- **Plugin Generator** - Template scaffolding

## 📋 Checklists

### Before Release
- [ ] All tests passing (>80% coverage)
- [ ] Code formatted and linted
- [ ] Security scan passed
- [ ] Documentation complete
- [ ] Examples provided
- [ ] Performance evaluated
- [ ] Version tagged
- [ ] Changelog updated

### Code Review
- [ ] Follows style guidelines
- [ ] Clear commit messages
- [ ] Adequate tests
- [ ] Handles edge cases
- [ ] Error handling robust
- [ ] No hardcoded secrets

### Documentation
- [ ] README with examples
- [ ] Skill descriptions clear
- [ ] API documented
- [ ] Installation instructions
- [ ] Contributing guidelines

## 🎯 Common Patterns

### Skill Pattern
```markdown
---
name: skill-name
description: Clear description with "Use when..." clause
category: workflow|analysis|generation|utility
---
# Skill Title
## Overview
## What It Does
## When to Use
## How to Use
## Examples
```

### Command Pattern
```yaml
---
name: command-name
description: Action-oriented description
parameters:
  - name: required-param
    type: string
    required: true
examples:
  - "command-name --value example"
---
```

### Error Handling Pattern
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.warning(f"Expected error: {e}")
    result = fallback_value
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise PluginError("Operation failed") from e
```

## 🔍 Debugging Guide

### Common Issues

#### Plugin Not Loading
1. Check `.claude-plugin/plugin.json` syntax
2. Verify paths are correct
3. Check marketplace.json configuration
4. Review Claude Code logs

#### Tests Failing
1. Install dependencies: `make install`
2. Check Python version: `python3 --version`
3. Clear cache: `make clean`
4. Run specific test: `pytest tests/test_specific.py -v`

#### Performance Issues
1. Profile with: `python -m cProfile script.py`
2. Check token usage estimates
3. Implement caching
4. Use lazy loading

### Debug Tools
```bash
# Validate plugin structure
make validate

# Run with debug output
uv run python -m debugpy --listen 5678 script.py

# Check dependencies
uv pip list

# Analyze complexity
uv run python scripts/complexity_calculator.py
```

## 📚 Resources

### Official Documentation
- [Claude Code Documentation](https://docs.anthropic.com/claude/docs/claude-code)
- [Agent Skills Best Practices](https://docs.anthropic.com/claude/docs/agent-skills-best-practices)
- [Plugin Development API](https://docs.anthropic.com/claude/docs/plugin-api)

### Community
- [GitHub Repository](https://github.com/athola/claude-night-market)
- [Issue Tracker](https://github.com/athola/claude-night-market/issues)
- [Discussions](https://github.com/athola/claude-night-market/discussions)

### Learning Resources
- [Abstract Plugin](../plugins/abstract/) - Meta-infrastructure and patterns
- [Existing Plugins](../plugins/) - Real-world implementations
- [Test Examples](../plugins/*/tests/) - Testing patterns

## 🤝 Contributing

### Ways to Contribute
1. **Report Issues** - Found a bug? Create an issue
2. **Submit PRs** - Fix bugs or add features
3. **Improve Docs** - Help make documentation better
4. **Share Examples** - Add useful examples
5. **Review PRs** - Help maintain quality

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Run quality checks
5. Submit pull request

## ❓ Getting Help

### Self-Service
- Check existing [issues](https://github.com/athola/claude-night-market/issues)
- Review [documentation](../developer-portal/)
- Examine [examples](../developer-portal/examples/)
- Try [templates](../developer-portal/templates/)

### Community Support
- Create a discussion for questions
- Ask for help in issues
- Share your progress

### Reporting Bugs
1. Check if already reported
2. Use bug report template
3. Include minimal reproduction
4. Provide environment details

## 🚀 Next Steps

Ready to build your plugin?

1. **[Set up environment](../developer-portal/getting-started/environment-setup.md)**
2. **[Use a template](../developer-portal/templates/)**
3. **[Follow guidelines](../developer-portal/guidelines/)**
4. **[Learn from examples](../developer-portal/examples/)**
5. **[Submit your plugin](../developer-portal/guidelines/marketplace-submission.md)**

Remember: Good plugins are:
- **Useful** - Solve real problems
- **Usable** - Easy to understand and use
- **Reliable** - Work consistently
- **Maintainable** - Well-structured and documented

Happy coding! 🎉
