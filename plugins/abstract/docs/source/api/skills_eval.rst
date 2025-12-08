Skills Evaluation
=================

.. automodule:: abstract.skills_eval
   :members:
   :member-order: bysource
   :show-inheritance:
   :special-members: __init__

Key Classes
-----------

ComplianceChecker
~~~~~~~~~~~~~~~~~

.. autoclass:: abstract.skills_eval.ComplianceChecker
   :members:
   :inherited-members:
   :show-inheritance:

ImprovementSuggester
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: abstract.skills_eval.ImprovementSuggester
   :members:
   :inherited-members:
   :show-inheritance:

TokenUsageTracker
~~~~~~~~~~~~~~~~

.. autoclass:: abstract.skills_eval.TokenUsageTracker
   :members:
   :inherited-members:
   :show-inheritance:

SkillsAuditor
~~~~~~~~~~~~~

.. autoclass:: abstract.skills_eval.SkillsAuditor
   :members:
   :inherited-members:
   :show-inheritance:

Data Structures
---------------

ComplianceIssue
~~~~~~~~~~~~~~~

.. autoclass:: abstract.skills_eval.ComplianceIssue
   :members:
   :inherited-members:
   :show-inheritance:

ComplianceReport
~~~~~~~~~~~~~~~~

.. autoclass:: abstract.skills_eval.ComplianceReport
   :members:
   :inherited-members:
   :show-inheritance:

SkillMetrics
~~~~~~~~~~~~

.. autoclass:: abstract.skills_eval.SkillMetrics
   :members:
   :inherited-members:
   :show-inheritance:

Improvement
~~~~~~~~~~~

.. autoclass:: abstract.skills_eval.Improvement
   :members:
   :inherited-members:
   :show-inheritance:

Example Usage
------------

.. code-block:: python

   from abstract.skills_eval import (
       ComplianceChecker,
       TokenUsageTracker,
       SkillsAuditor
   )
   from pathlib import Path

   skills_dir = Path("skills")

   # Check compliance
   checker = ComplianceChecker(skills_dir)
   results = checker.check_compliance()
   print(f"Compliant: {results['compliant']}")

   # Track token usage
   tracker = TokenUsageTracker(skills_dir)
   stats = tracker.get_usage_statistics()
   print(f"Total tokens: {stats['total_tokens']}")

   # Audit skills
   auditor = SkillsAuditor(skills_dir)
   audit_results = auditor.audit_skills()
   print(f"Average score: {audit_results['average_score']}")