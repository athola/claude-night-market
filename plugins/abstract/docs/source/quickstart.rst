Quick Start
===========

This guide will help you get up and running with the Abstract plugin infrastructure quickly.

First Steps
-----------

1. **Verify Installation**

   .. code-block:: bash

      make check

2. **Explore Available Skills**

   .. code-block:: bash

      ls skills/
      # You should see modular-skills and skills-eval directories

3. **Run a Basic Analysis**

   .. code-block:: bash

      # Check token usage of skills
      python3 scripts/token_estimator.py --directory skills

Using the Skills
----------------

The Abstract plugin provides two main meta-skills that activate automatically:

modular-skills
~~~~~~~~~~~~~~~

Activates when you're working with skill architecture, design patterns, or need to refactor code.

**Example usage:**

User: "I have a large skill that's becoming hard to maintain. How can I break it into modules?"

Claude will automatically use the modular-skills expertise to suggest modularization strategies.

skills-eval
~~~~~~~~~~~

Activates when you need to evaluate, validate, or improve existing skills.

**Example usage:**

User: "Can you review this skill and suggest improvements?"

Claude will use skills-eval to analyze and provide structured feedback.

Manual Tool Usage
------------------

You can also use the analysis tools directly:

Token Analysis
~~~~~~~~~~~~~~

.. code-block:: bash

   # Analyze a single skill
   python3 scripts/token_estimator.py --file skills/modular-skills/SKILL.md

   # Analyze all skills
   python3 scripts/token_estimator.py --directory skills

   # Include dependency analysis
   python3 scripts/token_estimator.py --directory skills --include-dependencies

   # Output as JSON
   python3 scripts/token_estimator.py --directory skills --format json

Context Optimization
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Analyze a specific skill
   python3 scripts/context_optimizer.py analyze skills/my-skill

   # Get statistics for all skills
   python3 scripts/context_optimizer.py stats skills

   # Generate detailed report
   python3 scripts/context_optimizer.py report skills

Skill Validation
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Validate skill structure
   python3 scripts/skill_analyzer.py --file skills/my-skill/SKILL.md

   # Check complexity threshold
   python3 scripts/skill_analyzer.py --directory skills --threshold 200

   # Verbose output
   python3 scripts/skill_analyzer.py --file skills/my-skill/SKILL.md --verbose

Batch Operations
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Generate comprehensive report
   python3 docs/examples/batch_skills_analyzer.py \
       --skills-dir skills \
       --output-dir reports

Common Workflows
----------------

Creating a New Skill
~~~~~~~~~~~~~~~~~~~

1. **Create the basic structure**

   .. code-block:: bash

      mkdir my-new-skill
      touch my-new-skill/SKILL.md

2. **Add frontmatter**

   .. code-block:: markdown

      ---
      name: my-new-skill
      description: Brief description of what this skill does
      category: utility
      version: 1.0.0
      ---

3. **Write the content**

   Follow the progressive disclosure pattern:
   - Overview
   - Quick Start
   - Examples
   - Resources

4. **Validate your skill**

   .. code-block:: bash

      python3 scripts/skill_analyzer.py --file my-new-skill/SKILL.md
      python3 scripts/token_estimator.py --file my-new-skill/SKILL.md

Optimizing Skills
~~~~~~~~~~~~~~~~~

1. **Check token usage**

   .. code-block:: bash

      python3 scripts/token_estimator.py --file my-skill/SKILL.md

2. **Look for optimization opportunities**

   .. code-block:: bash

      python3 scripts/context_optimizer.py analyze my-skill

3. **Consider modularization if needed**

   If your skill exceeds 2000 tokens or has multiple themes:
   - Extract examples to a separate file
   - Create modules for different aspects
   - Use the tools/ directory for scripts

Validating Multiple Skills
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run all checks
   make validate-skills

   # Or manually:
   python3 scripts/abstract_validator.py --directory skills
   python3 scripts/skill_analyzer.py --directory skills --format summary
   python3 scripts/token_estimator.py --directory skills --format summary

Getting Help
------------

- **Documentation**: ``docs/`` directory
- **Examples**: ``docs/examples/`` directory
- **API Reference**: ``docs/source/api/`` directory
- **CLI Help**: Use ``--help`` with any script

.. code-block:: bash

   python3 scripts/token_estimator.py --help
   python3 scripts/context_optimizer.py --help
   python3 scripts/skill_analyzer.py --help

Next Steps
----------

- Read the :doc:`examples/index` for detailed use cases
- Check the :doc:`api/index` for API documentation
- Review the :doc:`examples/skill_development` guide
- See the :doc:`examples/batch_processing` examples for automation