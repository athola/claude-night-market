---
name: code-review
description: Best practices for code review process, pull request guidelines, and team collaboration quality standards
version: 1.0.0
created_by: abstract-examples
tags: [code-review, pull-request, collaboration, quality, best-practices]
category: development
type: module
estimated_tokens: 100
dependencies: []
companion_skills: []
modules: []
tools:
  - pr-validator
  - quality-checker
  - review-checklist
---

# Code Review

Comprehensive code review framework that ensures consistent quality, knowledge sharing, and effective team collaboration through structured review processes and clear guidelines.

## Overview

Master code review practices with this comprehensive framework:

**🚀 Quick Start**: Get your team reviewing code effectively in 15 minutes
- Set up PR template and review checklist
- Define quality standards and acceptance criteria
- Start using structured feedback process

**📚 Progressive Learning**: Build review expertise gradually
1. **Foundation** → Basic review process + checklist + feedback patterns
2. **Quality Focus** → Security review + performance review + testing coverage
3. **Team Scaling** → Review automation + metrics + mentorship patterns

**🎯 Use Case-Based**: Jump directly to what you need right now
- New team? → Focus on review process + feedback guidelines
- Quality issues? → Apply security review + performance analysis
- Slow reviews? → Use automation + templates + review metrics
- Knowledge sharing? → Implement mentorship + pair review patterns

## Review Process

### Pre-Review Preparation
- Ensure code is self-contained and well-documented
- Run all tests and quality checks locally
- Provide clear context and problem statement
- Include relevant design documents or requirements

### Review Structure
1. **High-Level Review**: Architecture, design decisions, overall approach
2. **Implementation Review**: Code quality, style, patterns, best practices
3. **Testing Review**: Test coverage, edge cases, test quality
4. **Documentation Review**: Comments, README, API docs, changelog

### Review Categories

#### Functionality Review
- Does code solve the intended problem?
- Are edge cases properly handled?
- Is the implementation correct and complete?
- Are there potential bugs or issues?

#### Code Quality Review
- Is code readable and maintainable?
- Are appropriate design patterns used?
- Is code properly structured and organized?
- Are naming conventions followed?

#### Performance Review
- Are there performance bottlenecks?
- Is resource usage optimized?
- Are algorithms efficient for the problem scale?
- Are caching strategies appropriate?

#### Security Review
- Are input validation and sanitization implemented?
- Are authentication and authorization proper?
- Are sensitive data handled securely?
- Are common security vulnerabilities avoided?

## Feedback Guidelines

### Constructive Feedback
- Be specific and actionable
- Explain the "why" behind suggestions
- Offer solutions or alternatives
- Focus on code, not the person

### Review Response
- Address all feedback points
- Explain decisions when disagreeing
- Update code and documentation
- Thank reviewers for their time

### Review Etiquette
- Ask questions when unclear
- Assume good intentions
- Be respectful and professional
- Focus on improvement, not criticism

## Automation and Tools

### Review Checklists
```yaml
# .github/pull_request_template.md
## Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] Security implications considered
- [ ] Performance impact assessed
```

### Automated Checks
- Linting and formatting validation
- Unit and integration test execution
- Code coverage analysis
- Security vulnerability scanning
- Performance benchmarking

## Quality Metrics

### Review Effectiveness
- Review turnaround time
- Number of review iterations
- Bug detection rate
- Code quality improvement

### Team Metrics
- Review participation rate
- Knowledge sharing effectiveness
- Code quality trends
- Team velocity impact

## Best Practices

### For Reviewers
- Set aside dedicated review time
- Review in manageable chunks
- Use structured feedback approach
- Follow up on implemented suggestions

### For Authors
- Request early feedback on design
- Keep PRs focused and small
- Provide clear context and rationale
- Be responsive to review feedback

### For Teams
- Establish clear review guidelines
- Use consistent review criteria
- Track review metrics and improve
- Rotate reviewers for knowledge sharing

This code review framework helps teams maintain high code quality while fostering collaboration and continuous improvement through structured review processes and clear quality standards.