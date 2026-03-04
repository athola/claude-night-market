{
  "name": "skill-auditor",
  "description": "Agent for detailed skill quality auditing and improvement recommendations",
  "version": "1.0.0",
  "type": "evaluation",
  "capabilities": [
    "skill-analysis",
    "quality-assessment",
    "improvement-planning",
    "standards-compliance",
    "performance-evaluation"
  ],
  "tools": [
    "plugins/abstract/scripts/skills_auditor.py",
    "plugins/abstract/scripts/improvement_suggester.py",
    "plugins/abstract/scripts/compliance_checker.py",
    "plugins/abstract/scripts/tool_performance_analyzer.py",
    "plugins/abstract/scripts/skill_analyzer.py",
    "plugins/abstract/scripts/token_estimator.py"
  ],
  "triggers": [
    "skill-quality-review",
    "audit-request",
    "quality-assessment",
    "skill-improvement",
    "standards-check"
  ],
  "workflows": {
    "detailed-audit": [
      "discover-skills",
      "analyze-structure",
      "evaluate-quality",
      "generate-improvements",
      "create-report"
    ],
    "targeted-review": [
      "analyze-skill",
      "check-compliance",
      "suggest-improvements",
      "validate-fixes"
    ]
  },
  "output_formats": [
    "markdown-report",
    "json-analysis",
    "quality-score",
    "improvement-plan"
  ],
  "quality_metrics": {
    "structure_compliance": 25,
    "content_quality": 25,
    "token_efficiency": 20,
    "activation_reliability": 20,
    "tool_integration": 10
  },
  "integration": {
    "skills_eval": "primary",
    "modular_skills": "architectural-analysis",
    "performance_optimization": "efficiency-metrics"
  }
}
