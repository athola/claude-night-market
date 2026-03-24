"""Test suite for ProjectTracker.

This module has been split into focused sub-modules for maintainability:

- test_project_tracker_init_persistence.py -- TestProjectTrackerInitialization,
                                              TestDataPersistence
- test_project_tracker_tasks.py            -- TestAddTask, TestUpdateTask
- test_project_tracker_metrics.py          -- TestGetTasksByInitiative,
                                              TestCalculateInitiativeMetrics,
                                              TestCalculateOverallMetrics
- test_project_tracker_output.py           -- TestGetStatusReport,
                                              TestFormatGitHubComment,
                                              TestExportCSV, TestEdgeCases

All tests remain discoverable by pytest via the sub-modules above.
This file is retained for git blame continuity.
"""
