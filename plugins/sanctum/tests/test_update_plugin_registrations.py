#!/usr/bin/env python3
"""Tests for update_plugin_registrations.py script.

This module has been split into focused sub-modules for maintainability:

- test_update_plugin_registrations_core.py     -- TestPluginAuditor
                                                   (scan_disk_files,
                                                   compare_registrations,
                                                   fix_plugin basics)
- test_update_plugin_registrations_hooks.py    -- TestHooksJsonResolution
                                                   (hooks.json parsing,
                                                   _extract_script_path,
                                                   resolve_hooks_json)
- test_update_plugin_registrations_modules.py  -- TestExtractModuleRefsFromFile,
                                                   TestAuditSkillModules,
                                                   TestScanPluginForModuleRefs,
                                                   TestExtractModuleRefsEdgeCases,
                                                   TestAuditSkillModulesAdvanced
- test_update_plugin_registrations_advanced.py -- TestFixPluginAdvanced,
                                                   TestScanSkillModules,
                                                   TestReadModuleDescription,
                                                   TestPrintModuleIssuesEnriched

All tests remain discoverable by pytest via the sub-modules above.
This file is retained for git blame continuity.
"""
