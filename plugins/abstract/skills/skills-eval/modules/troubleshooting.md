# Troubleshooting

## Critical Issues

### Skills Not Triggering (System Prompt Budget Exceeded)

**Issue**: Skills exist but Claude doesn't invoke them, even when obviously relevant

**Root Cause**: Claude Code learns about available skills through a system prompt that includes skill names and descriptions. When you have too many skills or lengthy descriptions, the system prompt becomes too large, and Claude stops receiving information about some skills. Since Claude is instructed never to use skills not listed in the prompt, it simply won't deploy them.

**Symptoms**:
- Skills are installed and visible in file system
- Skills worked previously but stopped triggering
- No error messages or warnings
- Claude appears to "forget" certain skills exist
- More prevalent with large skill ecosystems (10+ skills)

**Technical Limits**:
- **Default budget**: Skill description budget scales at 2% of context window (~20,000 chars for 1M context)
- **No warning system**: There's currently no notification when you exceed this threshold
- **Silent failure**: Skills beyond the budget are simply not included in Claude's system prompt

**Solutions**:

1. **Increase System Prompt Budget** (Recommended immediate fix):
```bash
# Set before launching Claude Code
SLASH_COMMAND_TOOL_CHAR_BUDGET=30000 claude

# Or add to your shell profile
export SLASH_COMMAND_TOOL_CHAR_BUDGET=30000
```

2. **Shorten Skill Descriptions** (Long-term solution):
- Keep `description` field concise (< 200 characters)
- Focus on essential trigger keywords only
- Remove verbose explanations from description field
- Move detailed content to skill body
- Use modular patterns to reduce per-skill overhead

3. **Audit Skill Count and Size**:
```bash
# Count total skills
find ~/.claude/skills -name "SKILL.md" | wc -l

# Measure description field sizes
grep -A 5 "^description:" ~/.claude/skills/*/SKILL.md

# Estimate tokens per skill (run from plugins/abstract)
python3 scripts/token_usage_tracker.py ~/.claude/skills
```

4. **Consolidate Related Skills**:
- Combine underused skills with similar purposes
- Use conditional sections within skills instead of separate skills
- Archive rarely-used skills outside active directory

**Prevention**:
- Monitor skill description lengths during development
- Implement budget tracking in CI/CD pipelines
- Regular skill audits to identify consolidation opportunities
- Follow description-writing best practices (see the Resources section in
  `SKILL.md`)

**References**:
- Blog post: https://blog.fsck.com/2025/12/17/claude-code-skills-not-triggering/
- Related skill: `modular-skills` for creating budget-efficient skill architectures

---

## Common Issues and Solutions

### Tool Execution Problems

**Issue**: Tool not found. The skills-eval tools are Python scripts in
`plugins/abstract/scripts/`, not executables in this skill directory.
Run them with `python3` from `plugins/abstract`:
```bash
ls scripts/*.py
python3 scripts/skills_auditor.py --help
```

**Issue**: Python dependencies missing. `uv run` uses the plugin's own
environment:
```bash
uv run python scripts/skills_auditor.py skills/
```

### Skill Discovery Issues

**Issue**: No skills found during discovery
```bash
# Solution: point the auditor at the directory that holds the skills
ls ~/.claude/skills/
python3 scripts/skills_auditor.py ~/.claude/skills
```

**Issue**: Skills not loading properly
- Check YAML frontmatter validity
- Verify required fields are present
- validate file naming follows conventions
- Check for syntax errors in skill content

### Performance Issues

**Issue**: Slow evaluation performance
```bash
# Solution: analyze one skill file instead of a whole tree
python3 scripts/token_estimator.py --file skills/skills-eval/SKILL.md
python3 scripts/skill_analyzer.py --file skills/skills-eval/SKILL.md
```

**Issue**: High memory usage during analysis
- Limit analysis scope with filters
- Use incremental evaluation
- Clear temporary files regularly
- Monitor system resources

### Compliance and Quality Issues

**Issue**: Consistent compliance failures
```bash
# Solution: list the findings, then plan fixes for one skill
python3 scripts/compliance_checker.py skills/
python3 scripts/improvement_suggester.py skills/skills-eval
```

**Issue**: Quality scores not improving
- Review improvement suggestions carefully
- Focus on high-priority issues first
- Implement changes incrementally
- Re-evaluate after each fix

## Advanced Troubleshooting

### Verbose Output

`skill_analyzer.py` and `token_estimator.py` accept `--verbose` (or
`-v`, repeatable). The other scripts have no debug flag.
```bash
python3 scripts/skill_analyzer.py --file skills/skills-eval/SKILL.md -v
```

### Performance Analysis

`tool_performance_analyzer.py` runs each executable it finds with
`--help`. Point it only at code you trust.
```bash
python3 scripts/tool_performance_analyzer.py skills/skills-eval
```

## Error Recovery Strategies

### When Tools Fail
1. **Check Permissions**: Verify executables have correct permissions
2. **Validate Dependencies**: validate all required tools and libraries are available
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

### Help Output
Every script prints its flags with `--help`:
```bash
python3 scripts/skills_auditor.py --help
python3 scripts/compliance_checker.py --help
```

### Support Channels
- **Documentation**: Check detailed guides in `modules/` directory
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
