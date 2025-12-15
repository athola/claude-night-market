Changelog
=========

All notable changes to this project are documented in the file :doc:`../CHANGELOG`.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

Recent Changes
--------------

.. raw:: html

   <details>
   <summary>Latest Release (1.1.0)</summary>

### Added
- Standardized CLI patterns using AbstractCLI base class
- Pre-commit hook for mypy type checking
- Tests for script permissions and deleted tool references
- Migration guide for tools → scripts transition

### Changed
- Moved distributed tools to centralized scripts directory
- Improved error handling with specific exception types
- Updated all CLI help outputs for consistency

### Fixed
- Unused imports in ``src/abstract/base.py``
- Permission issues with executable scripts

### Security
- Added ``# nosec`` comments for validated subprocess usage
- Improved exception handling to avoid bare except clauses

   </details>

Updating the Changelog
---------------------

The changelog can be updated automatically:

.. code-block:: bash

   # Generate from git commits since last tag
   python3 scripts/update_changelog.py

   # Generate for a specific version
   python3 scripts/update_changelog.py --version 1.2.0

   # Validate changelog format
   python3 scripts/update_changelog.py --validate-only

The script categorizes commits automatically:
- ``Added`` for new features
- ``Fixed`` for bug fixes
- ``Changed`` for modifications
- ``Security`` for security changes
- ``Deprecated`` for deprecations
- ``Removed`` for removals
