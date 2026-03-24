"""Test suite for attune_init module.

This module has been split into focused sub-modules for maintainability:

- test_attune_init_git_templates.py  -- TestInitializeGit, TestCopyTemplates
                                        (basic), TestAttuneInitBehavior (BDD)
- test_attune_init_structure.py      -- TestCreateProjectStructure, TestMain,
                                        TestCopyTemplatesDryRun,
                                        TestCopyTemplatesBackup,
                                        TestCreateProjectStructureDryRun,
                                        TestMainDryRunAndBackupFlags

All tests remain discoverable by pytest via the sub-modules above.
This file is retained for git blame continuity.
"""
