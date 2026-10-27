# Evaluation Workflows and Techniques

## Detailed Implementation Steps

Commands run from `plugins/abstract`.

### Phase 1: Discovery and Assessment
1. **Inventory and scan**: Run `python3 scripts/skills_auditor.py skills/`
   to list and score every skill under the directory
2. **Identify patterns**: Look for common issues and improvement opportunities
3. **Set baselines**: Establish quality metrics and improvement targets

### Phase 2: Detailed Analysis
1. **Deep analysis**: Run
   `python3 scripts/skill_analyzer.py --file <skill>/SKILL.md --verbose`
2. **Token evaluation**: Run
   `python3 scripts/token_estimator.py --file <skill>/SKILL.md`
3. **Compliance checking**: Run `python3 scripts/compliance_checker.py skills/`
4. **Gap analysis**: Compare against best practices and standards

### Phase 3: Improvement Planning
1. **Generate recommendations**: Run
   `python3 scripts/improvement_suggester.py <skill>/SKILL.md`
2. **Prioritize improvements**: Focus on critical and high-priority items first
3. **Create action plans**: Break improvements into manageable tasks
4. **Schedule implementation**: Plan improvement work in logical phases

### Phase 4: Implementation and Validation
1. **Apply improvements**: Implement changes based on recommendations
2. **Test functionality**: Verify tools and examples work correctly
3. **Validate compliance**: Re-run compliance checks
4. **Measure results**: Compare before/after quality scores

## Advanced Analysis Techniques

### Comparative Analysis
- Benchmark skills against best-in-class examples
- Identify patterns in high-performing skills
- Learn from structural and content differences

### Trend Tracking
- Run periodic audits to monitor quality over time
- Track improvement implementation success rates
- Identify recurring issues and systemic problems

### Gap Analysis
- Identify missing skill categories in your library
- Find opportunities for new skill development
- Balance skill coverage across domains and use cases

### Dependency Mapping
- Understand skill relationships and interactions
- Identify potential circular dependencies
- Optimize skill loading patterns and efficiency
