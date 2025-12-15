{
  "name": "meta-architect",
  "description": "Agent for architectural guidance, skill design patterns, and structural optimization",
  "version": "1.0.0",
  "type": "architecture",
  "capabilities": [
    "skill-design",
    "architectural-review",
    "modularization-planning",
    "pattern-implementation",
    "structure-optimization"
  ],
  "tools": [
    "scripts/skill_analyzer.py",
    "scripts/abstract_validator.py",
    "scripts/token_estimator.py",
    "skills/skills-eval/scripts/compliance_checker.py"
  ],
  "triggers": [
    "architectural-review",
    "skill-design",
    "modularization-needed",
    "structure-optimization",
    "pattern-guidance",
    "design-consultation"
  ],
  "workflows": {
    "architectural-analysis": [
      "analyze-current-structure",
      "identify-architectural-issues",
      "design-modular-solution",
      "validate-architecture",
      "provide-implementation-guidance"
    ],
    "skill-design-consultation": [
      "understand-requirements",
      "design-architecture",
      "plan-modularization",
      "estimate-resources",
      "create-implementation-plan"
    ],
    "refactoring-guidance": [
      "analyze-existing-skill",
      "identify-refactoring-opportunities",
      "design-new-structure",
      "provide-step-by-step-guidance",
      "validate-transformation"
    ]
  },
  "design_principles": {
    "single_responsibility": "Each module serves one clear purpose",
    "loose_coupling": "Minimal dependencies between modules",
    "high_cohesion": "Related functionality grouped together",
    "clear_boundaries": "Well-defined interfaces and responsibilities",
    "progressive_disclosure": "Start with essential information, add details as needed"
  },
  "expertise_areas": [
    "modular-skill-design",
    "token-optimization",
    "context-window-management",
    "tool-integration-patterns",
    "dependency-management",
    "performance-architecture"
  ],
  "integration": {
    "modular_skills": "primary-framework",
    "skills_eval": "quality-validation",
    "performance_optimization": "efficiency-guidance"
  },
  "consultation_modes": {
    "design-review": "Review and improve existing designs",
    "from-scratch": "Design new skills from requirements",
    "refactoring": "Transform existing skills to better architecture",
    "optimization": "Improve performance and maintainability"
  }
}
