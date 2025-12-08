API Stability Policy
===================

This document outlines the API stability policy for the Abstract plugin infrastructure.

Core Principles
---------------

No Backward Compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Abstract does NOT guarantee backward compatibility between versions.**

This is a deliberate design choice that enables:

- Rapid iteration and improvement
- Breaking changes to fix design issues
- Clean evolution without legacy constraints
- Simpler, more maintainable codebase

Semantic Versioning (SemVer)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We follow Semantic Versioning (https://semver.org/) strictly:

- **MAJOR** version increments indicate BREAKING CHANGES
- **MINOR** version increments add new features (compatible within the same major version)
- **PATCH** version increments fix bugs (compatible within the same major version)

**Important**: Even MINOR and PATCH versions may introduce changes that require user updates. Always check the changelog.

Version Compatibility
~~~~~~~~~~~~~~~~~~~

- **1.0.x to 1.1.x**: May require updates to configuration or scripts
- **1.x.x to 2.0.0**: Will require updates - breaking changes expected

What Can Change
---------------

Between any versions (including PATCH releases), the following may change:

Public APIs
~~~~~~~~~~~

- Function signatures
- Class definitions
- Module structure
- Import paths
- Configuration formats
- CLI arguments and options
- Default behaviors

Internal Implementation
~~~~~~~~~~~~~~~~~~~~~~

All internal implementation details may change at any time without notice.

Data Formats
~~~~~~~~~~~~

- YAML configuration structure
- JSON output formats
- File layouts
- Naming conventions

Upgrade Process
---------------

Users should expect to:

1. **Read the Changelog**

   Always review :doc:`changelog` before upgrading:

   .. code-block:: bash

      # Check what changed between versions
      git log v1.0.0..v1.1.0 --oneline

2. **Update Integration Code**

   Update any code that uses Abstract APIs, CLI tools, or configurations.

3. **Run Validation**

   .. code-block:: bash

      make test  # Run all checks after upgrade

4. **Monitor for Deprecation Warnings**

   When we implement deprecation (in the future), update affected code promptly.

Breaking Changes Examples
-------------------------

Here are examples of changes that are considered breaking:

API Changes
~~~~~~~~~~~

.. code-block:: python

   # Before
   from abstract.utils import analyze_skill

   # After (breaking change)
   from abstract.analysis import SkillAnalyzer

CLI Changes
~~~~~~~~~~~

.. code-block:: bash

   # Before
   python3 scripts/analyze.py --input file.md

   # After (breaking change)
   python3 scripts/skill_analyzer.py --file file.md

Configuration Changes
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # Before
   skills:
     directory: "skills"

   # After (breaking change)
   skills_dir: "skills"

Migration Guides
-----------------

For major version bumps, we provide:

1. **Migration Guide**: Step-by-step instructions
2. **Compatibility Checker**: Script to identify needed changes
3. **Example Migrations**: Before/after code examples

Example: v1 to v2 Migration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If moving from v1.x to v2.x:

1. Check the migration guide in ``docs/migrations/v2.md``
2. Run the compatibility checker:

   .. code-block:: bash

      python3 scripts/migration_check.py --from-version 1.0 --to-version 2.0

3. Update identified issues
4. Re-run tests to verify

Developer Responsibility
-----------------------

As a user of Abstract:

- **You are responsible for maintaining compatibility with your chosen version**
- **Test upgrades before deploying to production**
- **Pin versions in your environments**

Recommended practice:

.. code-block:: toml

   # pyproject.toml
   [dependencies]
   abstract = "~=1.1.0"  # Allow patch updates within 1.1.x
   # OR exact version for maximum stability
   abstract = "==1.1.2"

Internal APIs
------------

All APIs not explicitly documented in :doc:`api/index` are considered internal and may change without notice.

Marking Internal APIs
~~~~~~~~~~~~~~~~~~~~~

Internal APIs use leading underscores:

.. code-block:: python

   class SkillAnalyzer:
       def public_method(self):  # Public API
           pass

       def _internal_method(self):  # Internal API - may change
           pass

Plugin Interface
---------------

The Claude Code plugin interface (how skills are detected and loaded) is considered part of the public API but follows different rules:

- Skill file formats (``SKILL.md``) aim for stability
- Frontmatter fields maintain backward compatibility within major versions
- Core skill loading behavior is stable

However, the internal implementation of how skills are processed may change.

Security Updates
----------------

Critical security updates may be released as PATCH versions but may still contain breaking changes if necessary to address the security issue.

Feedback Process
----------------

If a breaking change causes significant disruption:

1. **File an issue** describing the impact
2. **Provide context** about your use case
3. **Suggest improvements** to the change process

We evaluate all feedback but prioritize the long-term health and maintainability of the project.

Future Considerations
--------------------

While we currently don't support backward compatibility, this may evolve as the project matures. Factors that might influence future policy:

- Project adoption and use patterns
- Stability requirements from users
- Maintenance overhead
- Community feedback

Any policy changes will be announced well in advance and documented thoroughly.
