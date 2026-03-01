"""
Tests for continuous improvement integration.

Tests the integration between /update-plugins, /fix-workflow, and proof-of-work
to ensure automatic improvement tracking works correctly.
"""

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def test_update_plugins_has_phase_2():
    """Verify /update-plugins references Phase 2 (content in module)."""
    main_path = PROJECT_ROOT / "plugins/sanctum/commands/update-plugins.md"
    main_content = main_path.read_text()

    # Main doc references Phase 2 module
    assert "phase2-performance" in main_content, (
        "/update-plugins missing Phase 2 module reference"
    )
    assert "skill-review" in main_content, (
        "/update-plugins missing skill-review reference"
    )

    # Phase 2 detail lives in the module file
    module_path = (
        PROJECT_ROOT
        / "plugins/sanctum/commands/update-plugins/modules/phase2-performance.md"
    )
    module_content = module_path.read_text()
    assert "stability_gap" in module_content, (
        "Phase 2 module missing stability_gap mention"
    )
    assert "TodoWrite" in module_content or "improvement" in module_content, (
        "Phase 2 module missing improvement documentation"
    )


def test_fix_workflow_has_phase_0():
    """Verify /fix-workflow includes Phase 0 context gathering."""
    file_path = PROJECT_ROOT / "plugins/sanctum/commands/fix-workflow.md"
    content = file_path.read_text()

    assert "Phase 0: Gather Improvement Context" in content, (
        "/fix-workflow missing Phase 0 section"
    )
    assert "/skill-logs" in content, "/fix-workflow missing /skill-logs reference"
    assert "git log" in content, "/fix-workflow missing git history analysis"
    assert "stability_gap" in content or "stability gap" in content, (
        "/fix-workflow missing stability_gap mention"
    )


def test_workflow_improvement_skill_enhanced():
    """Verify workflow-improvement skill includes Steps 0 and 7."""
    file_path = PROJECT_ROOT / "plugins/sanctum/skills/workflow-improvement/SKILL.md"
    content = file_path.read_text()

    assert "Step 0: Gather Improvement Context" in content, (
        "workflow-improvement skill missing Step 0"
    )
    assert "Step 7: Close the Loop" in content, (
        "workflow-improvement skill missing Step 7"
    )
    assert "fix-workflow:context-gathered" in content, (
        "workflow-improvement skill missing context-gathered TodoWrite"
    )
    assert "fix-workflow:lesson-stored" in content, (
        "workflow-improvement skill missing lesson-stored TodoWrite"
    )
    assert "/skill-logs" in content, (
        "workflow-improvement skill missing /skill-logs reference"
    )
    assert "skill-review" in content, (
        "workflow-improvement skill missing skill-review reference"
    )


def test_proof_of_work_integration():
    """Verify proof-of-work integration with improvement workflows."""
    file_path = PROJECT_ROOT / "plugins/imbue/skills/proof-of-work/SKILL.md"
    content = file_path.read_text()

    assert "With Improvement Workflows" in content, (
        "proof-of-work missing improvement workflows section"
    )
    assert "/update-plugins" in content, "proof-of-work missing /update-plugins mention"
    assert "/fix-workflow" in content, "proof-of-work missing /fix-workflow mention"

    # Check for improvement-related triggers anywhere in the file
    assert (
        "improvement validated" in content
        or "workflow optimized" in content
        or "performance improved" in content
    ), "proof-of-work missing improvement-related triggers"


def test_changelog_documents_changes():
    """Verify CHANGELOG documents continuous improvement integration."""
    file_path = PROJECT_ROOT / "CHANGELOG.md"
    content = file_path.read_text()

    assert "Continuous Improvement Integration" in content, (
        "CHANGELOG missing continuous improvement section"
    )
    assert "Phase 2" in content, "CHANGELOG missing Phase 2 documentation"
    assert "Phase 0" in content, "CHANGELOG missing Phase 0 documentation"
    assert "proof-of-work integration" in content.lower(), (
        "CHANGELOG missing proof-of-work integration"
    )


def test_automatic_execution_documented():
    """Verify automatic execution is documented (no flags required)."""
    update_plugins = (
        PROJECT_ROOT / "plugins/sanctum/commands/update-plugins.md"
    ).read_text()
    fix_workflow = (
        PROJECT_ROOT / "plugins/sanctum/commands/fix-workflow.md"
    ).read_text()

    assert "automatic" in update_plugins.lower(), (
        "/update-plugins doesn't document automatic execution"
    )
    assert "automatic" in fix_workflow.lower(), (
        "/fix-workflow doesn't document automatic execution"
    )


def test_infrastructure_accessible():
    """Verify required infrastructure is accessible."""
    skill_logs_dir = Path.home() / ".claude/skills/logs"

    assert skill_logs_dir.exists(), "Skill logs directory does not exist"
    assert skill_logs_dir.is_dir(), "Skill logs path is not a directory"

    history_file = skill_logs_dir / ".history.json"
    assert history_file.exists(), "History file does not exist"

    # Verify it's valid JSON
    import json

    with open(history_file) as f:
        data = json.load(f)
    assert isinstance(data, dict), "History file is not a valid JSON object"


def test_feedback_loop_documented():
    """Verify continuous improvement feedback loop is documented."""
    file_path = PROJECT_ROOT / "plugins/sanctum/commands/update-plugins.md"
    content = file_path.read_text()

    assert (
        "Improvement Integration Loop" in content or "feedback loop" in content.lower()
    ), "/update-plugins missing feedback loop documentation"


if __name__ == "__main__":
    # Run all tests
    import sys

    tests = [
        test_update_plugins_has_phase_2,
        test_fix_workflow_has_phase_0,
        test_workflow_improvement_skill_enhanced,
        test_proof_of_work_integration,
        test_changelog_documents_changes,
        test_automatic_execution_documented,
        test_infrastructure_accessible,
        test_feedback_loop_documented,
    ]

    print("Running continuous improvement integration tests...\n")

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} total")
    print(f"{'=' * 60}")

    sys.exit(0 if failed == 0 else 1)
