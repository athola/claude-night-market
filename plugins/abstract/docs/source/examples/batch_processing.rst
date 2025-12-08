Batch Processing Examples
=========================

This guide shows how to use Abstract tools for batch processing of multiple skills.

Analyzing Multiple Skills
-------------------------

Basic Batch Analysis
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Analyze all skills in the skills directory
   python3 scripts/token_estimator.py --directory skills --format json > token_analysis.json

   # Get context optimization statistics
   python3 scripts/context_optimizer.py stats skills

   # Check skill complexity across all modules
   python3 scripts/skill_analyzer.py --directory skills --threshold 100 --format table

Using Python for Batch Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """Batch process skills and generate reports."""

   import json
   import sys
   from pathlib import Path
   from abstract.skills_eval import SkillsAuditor, TokenUsageTracker

   def batch_analyze_skills(skills_dir: Path):
       """Analyze all skills and generate comprehensive report."""

       # Initialize analyzers
       auditor = SkillsAuditor(skills_dir)
       token_tracker = TokenUsageTracker(skills_dir)

       # Collect all data
       audit_results = auditor.audit_skills()
       token_stats = token_tracker.get_usage_statistics()

       # Generate report
       report = {
           "summary": {
               "total_skills": audit_results["total_skills"],
               "average_score": audit_results["average_score"],
               "total_tokens": token_stats["total_tokens"],
               "well_structured": audit_results["well_structured"],
               "needs_improvement": audit_results["needs_improvement"]
           },
           "details": {
               "audit_metrics": audit_results["skill_metrics"],
               "token_breakdown": token_stats
           },
           "recommendations": audit_results["recommendations"]
       }

       return report

   if __name__ == "__main__":
       skills_dir = Path("skills")
       if not skills_dir.exists():
           print("Skills directory not found")
           sys.exit(1)

       results = batch_analyze_skills(skills_dir)

       # Save report
       with open("skills_analysis_report.json", "w") as f:
           json.dump(results, f, indent=2, default=str)

       print(f"Analyzed {results['summary']['total_skills']} skills")
       print(f"Average score: {results['summary']['average_score']:.1f}/100")
       print(f"Total tokens: {results['summary']['total_tokens']:,}")

Creating Custom Batch Scripts
-----------------------------

Example: Skill Migration Helper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """Help migrate skills to new standards."""

   import shutil
   from pathlib import Path
   from abstract.cli_framework import AbstractCLI, CLIResult

   class SkillMigratorCLI(AbstractCLI):
       def add_arguments(self, parser):
           parser.add_argument(
               "--source",
               type=Path,
               required=True,
               help="Source directory with old skills"
           )
           parser.add_argument(
               "--target",
               type=Path,
               required=True,
               help="Target directory for new skills"
           )
           parser.add_argument(
               "--dry-run",
               action="store_true",
               help="Show what would be done without making changes"
           )

       def execute(self, args) -> CLIResult:
           source = args.source
           target = args.target
           dry_run = args.dry_run

           if not source.exists():
               return CLIResult(success=False, error=f"Source directory not found: {source}")

           # Find all skill files
           skill_files = list(source.rglob("SKILL.md"))
           migrated = []
           errors = []

           for skill_file in skill_files:
               try:
                   # Calculate relative path
                   rel_path = skill_file.relative_to(source)
                   target_path = target / rel_path

                   # Read and validate
                   content = skill_file.read_text()

                   # Check for required frontmatter
                   if not content.startswith("---\n"):
                       errors.append(f"{skill_file}: Missing frontmatter")
                       continue

                   if not dry_run:
                       # Create target directory
                       target_path.parent.mkdir(parents=True, exist_ok=True)

                       # Copy and potentially modify the file
                       shutil.copy2(skill_file, target_path)

                       # Add module directory if missing
                       module_dir = target_path.parent / "modules"
                       if not module_dir.exists():
                           module_dir.mkdir()
                           (module_dir / ".gitkeep").touch()

                   migrated.append(str(rel_path))

               except Exception as e:
                   errors.append(f"{skill_file}: {e}")

           return CLIResult(
               success=len(errors) == 0,
               data={
                   "migrated": migrated,
                   "errors": errors,
                   "dry_run": dry_run
               }
           )

   if __name__ == "__main__":
       cli_main(SkillMigratorCLI)

Example: Continuous Integration Validator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """Validate all skills for CI/CD pipeline."""

   import json
   import sys
   from pathlib import Path
   from abstract.skills_eval import ComplianceChecker

   def validate_all_skills(skills_dir: Path, output_file: Path):
       """Validate all skills and output results."""

       checker = ComplianceChecker(skills_dir)
       results = checker.check_compliance()

       # Prepare CI-friendly output
       output = {
           "success": results["compliant"],
           "summary": {
               "total_skills": results["total_skills"],
               "compliant_count": results.get("compliant_count", 0),
               "issues_count": len(results["issues"]),
               "warnings_count": len(results["warnings"])
           },
           "details": {
               "issues": results["issues"],
               "warnings": results["warnings"]
           }
       }

       # Write output
       output_file.parent.mkdir(parents=True, exist_ok=True)
       with open(output_file, "w") as f:
           json.dump(output, f, indent=2)

       # Exit with appropriate code
       sys.exit(0 if results["compliant"] else 1)

   if __name__ == "__main__":
       skills_dir = Path("skills")
       output_file = Path("build") / "skill_validation.json"
       validate_all_skills(skills_dir, output_file)

Automation Scripts
-----------------

Shell Script for Weekly Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # Weekly skills analysis script

   set -e

   REPORT_DIR="reports/weekly-$(date +%Y-%m-%d)"
   mkdir -p "$REPORT_DIR"

   echo "Running weekly skills analysis..."

   # Token usage report
   echo "Generating token usage report..."
   python3 scripts/token_estimator.py \
       --directory skills \
       --format json \
       --include-dependencies \
       > "$REPORT_DIR/token_usage.json"

   # Context optimization report
   echo "Generating context optimization report..."
   python3 scripts/context_optimizer.py \
       report skills \
       > "$REPORT_DIR/context_optimization.txt"

   # Skill complexity analysis
   echo "Analyzing skill complexity..."
   python3 scripts/skill_analyzer.py \
       --directory skills \
       --format json \
       > "$REPORT_DIR/complexity_analysis.json"

   # Generate summary
   echo "Generating summary..."
   python3 - << EOF
   import json
   from pathlib import Path

   # Load reports
   token_report = json.loads(Path("$REPORT_DIR/token_usage.json").read_text())
   complexity_report = json.loads(Path("$REPORT_DIR/complexity_analysis.json").read_text())

   # Calculate metrics
   total_tokens = sum(r.get("total_tokens", 0) for r in token_report)
   complex_skills = [r for r in complexity_report if r.get("should_modularize", False)]

   print(f"Weekly Skills Summary - $(date)")
   print("=" * 50)
   print(f"Total skills analyzed: {len(token_report)}")
   print(f"Total tokens: {total_tokens:,}")
   print(f"Skills needing modularization: {len(complex_skills)}")

   if complex_skills:
       print("\nSkills to review:")
       for skill in complex_skills[:5]:
           print(f"  - {skill.get('name', 'Unknown')}")
   EOF

   echo "Reports saved to: $REPORT_DIR"

Make Integration
~~~~~~~~~~~~~~~~

.. code-block:: makefile

   # Add to your Makefile

   .PHONY: analyze-skills validate-skills weekly-report

   analyze-skills:
   	@echo "Analyzing all skills..."
   	python3 scripts/token_estimator.py --directory skills --format table
   	python3 scripts/skill_analyzer.py --directory skills --format summary
   	python3 scripts/context_optimizer.py stats skills

   validate-skills:
   	@echo "Validating skill compliance..."
   	python3 scripts/abstract_validator.py --directory skills
   	@echo "Running compliance checks..."
   	python3 -c "from abstract.skills_eval import ComplianceChecker; import sys; from pathlib import Path; checker = ComplianceChecker(Path('skills')); result = checker.check_compliance(); sys.exit(0 if result['compliant'] else 1)"

   weekly-report:
   	@echo "Generating weekly report..."
   	@./scripts/weekly_analysis.sh

   ci-check: validate-skills analyze-skills
   	@echo "All checks passed!"
