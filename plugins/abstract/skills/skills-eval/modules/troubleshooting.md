# Troubleshooting

## Common Issues and Solutions

### Tool Execution Problems

**Issue**: Tools not found or not executable
```bash
# Solution: Make tools executable and verify paths
chmod +x skills/skills-eval/scripts/*
which skills-auditor
```

**Issue**: Permission denied errors
```bash
# Solution: Check file permissions
ls -la skills/skills-eval/scripts/
chmod +x skills/skills-eval/scripts/skills-auditor
```

**Issue**: Python dependencies missing
```bash
# Solution: Use setup script or install dependencies
python3 skills/skills-eval/scripts/automation/setup.py
pip install -r requirements.txt  # if available
```

### Skill Discovery Issues

**Issue**: No skills found during discovery
```bash
# Solution: Verify Claude configuration and skill locations
ls ~/.claude/skills/
skills/skills-eval/scripts/skills-auditor --discover
```

**Issue**: Skills not loading properly
- Check YAML frontmatter validity
- Verify required fields are present
- Ensure file naming follows conventions
- Check for syntax errors in skill content

### Performance Issues

**Issue**: Slow evaluation performance
```bash
# Solution: Use targeted analysis and caching
skills/skills-eval/scripts/skills-auditor --skill-path specific-skill.md
skills/skills-eval/scripts/token-estimator -f skill.md --cache
```

**Issue**: High memory usage during analysis
- Limit analysis scope with filters
- Use incremental evaluation
- Clear temporary files regularly
- Monitor system resources

### Compliance and Quality Issues

**Issue**: Consistent compliance failures
```bash
# Solution: Use auto-fix and targeted improvements
skills/skills-eval/scripts/compliance-checker --skill-path skill.md --auto-fix
skills/skills-eval/scripts/improvement-suggester --skill-path skill.md --priority critical
```

**Issue**: Quality scores not improving
- Review improvement suggestions carefully
- Focus on high-priority issues first
- Implement changes incrementally
- Re-evaluate after each fix

## Advanced Troubleshooting

### Debug Mode Usage
```bash
# Enable detailed diagnostics for any tool
skills/skills-eval/scripts/skills-auditor --debug --verbose
skills/skills-eval/scripts/compliance-checker --debug --skill-path skill.md
```

### Environment Validation
```bash
# Complete environment check
python3 skills/skills-eval/scripts/automation/validate.py --check-deps --verbose
```

### Performance Analysis
```bash
# Analyze tool performance bottlenecks
skills/skills-eval/scripts/tool-performance-analyzer --skill-path skill.md --metrics all
```

## Error Recovery Strategies

### When Tools Fail
1. **Check Permissions**: Verify executables have correct permissions
2. **Validate Dependencies**: Ensure all required tools and libraries are available
3. **Verify Paths**: Check that file paths are correct and accessible
4. **Test Individually**: Run tools in isolation to isolate issues
5. **Check Logs**: Review error messages and diagnostic output

### When Evaluations Fail
1. **Validate Input**: Check that skill files are properly formatted
2. **Test Simpler Cases**: Start with basic evaluation before advanced features
3. **Incremental Analysis**: Break down complex evaluations into smaller steps
4. **Fallback Methods**: Use alternative tools or manual analysis
5. **Document Issues**: Track recurring problems for future resolution

### Performance Recovery
1. **Resource Monitoring**: Check system memory and CPU usage
2. **Process Management**: Kill hanging processes and clear temporary files
3. **Scope Reduction**: Limit evaluation scope to specific skills or features
4. **Cache Management**: Clear or rebuild evaluation caches
5. **Alternative Approaches**: Use different evaluation strategies

## Getting Help

### Debug Mode
Use `--debug` flag with any tool for detailed diagnostics:
```bash
skills/skills-eval/scripts/skills-auditor --debug --scan-all
```

### Help Output
All tools support `--help` for usage information:
```bash
skills/skills-eval/scripts/skills-auditor --help
skills/skills-eval/scripts/compliance-checker --help
```

### Verbose Mode
Use `--verbose` for detailed process information:
```bash
skills/skills-eval/scripts/improvement-suggester --verbose --skill-path skill.md
```

### Support Channels
- **Documentation**: Check comprehensive guides in `modules/` directory
- **Examples**: Review implementation examples in `examples/` directory
- **Tools**: Use built-in diagnostic tools for troubleshooting
- **Community**: Share issues and solutions with the Claude Skills community

## Preventive Measures

### Regular Maintenance
- Keep tools updated to latest versions
- Regular validation of skill inventory
- Performance monitoring and optimization
- Backup of skill configurations and data

### Quality Assurance
- Implement pre-commit evaluation checks
- Use automated quality gates
- Regular compliance validation
- Continuous improvement processes

### Monitoring
- Track evaluation performance over time
- Monitor resource usage patterns
- Alert on quality degradation
- Document and share best practices