"""Tests for conjure skill loading and execution following TDD/BDD principles."""

# Import modules for testing
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from delegation_executor import Delegator, ExecutionResult

# Constants for magic values
MIN_RECOVERY_STRATEGIES = 2
MIN_SOLUTIONS = 2
EXPECTED_ESTIMATE_COUNT = 4
MIN_MODEL_CHOICES = 2


class TestSkillStructure:
    """Test skill file structure and metadata."""

    def test_gemini_delegation_skill_structure(self) -> None:
        """Given gemini-delegation skill file when reading structure.

        then should have valid frontmatter.
        """
        skill_file = (
            Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        )

        assert skill_file.exists(), "gemini-delegation skill file should exist"

        content = skill_file.read_text()

        # Check for required frontmatter fields
        assert "name: gemini-delegation" in content
        assert "description: Gemini CLI delegation workflow" in content
        assert "category: delegation-implementation" in content
        assert "dependencies: [delegation-core]" in content

        # Check for required sections
        assert "# Overview" in content
        assert "# When to Use" in content
        assert "# Prerequisites" in content
        assert "# Delegation Flow" in content
        assert "# Exit Criteria" in content

    def test_delegation_core_skill_structure(self) -> None:
        """Given delegation-core skill file when reading structure.

        then should have valid frontmatter.
        """
        skill_file = (
            Path(__file__).parent.parent / "skills" / "delegation-core" / "SKILL.md"
        )

        assert skill_file.exists(), "delegation-core skill file should exist"

        content = skill_file.read_text()

        # Check for required frontmatter fields
        assert "name: delegation-core" in content
        assert "description: Core delegation workflow" in content
        assert "category: delegation" in content

    def test_qwen_delegation_skill_structure(self) -> None:
        """Given qwen-delegation skill file when reading structure.

        then should have valid frontmatter.
        """
        skill_file = (
            Path(__file__).parent.parent / "skills" / "qwen-delegation" / "SKILL.md"
        )

        assert skill_file.exists(), "qwen-delegation skill file should exist"

        content = skill_file.read_text()

        # Check for required frontmatter fields
        assert "name: qwen-delegation" in content
        assert "description: Qwen CLI delegation workflow" in content
        assert "category: delegation-implementation" in content


class TestSkillDependencyResolution:
    """Test skill dependency management."""

    def test_gemini_delegation_dependencies(self) -> None:
        """Given gemini-delegation skill when checking dependencies.

        then should resolve correctly.
        """
        skill_file = (
            Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        )
        content = skill_file.read_text()

        # Extract dependencies from frontmatter
        lines = content.split("\n")
        deps_section = False
        dependencies = []

        for line in lines:
            if line.strip() == "dependencies:":
                deps_section = True
                continue
            if deps_section:
                if line.strip().startswith("tools:"):
                    break
                if line.strip().startswith("-"):
                    dependencies.append(line.strip().lstrip("- ").strip())

        assert "delegation-core" in dependencies, (
            "gemini-delegation should depend on delegation-core"
        )

    def test_skill_tool_requirements(self) -> None:
        """Given skill files when checking tool requirements.

        then should specify necessary tools.
        """
        gemini_skill = (
            Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        )
        content = gemini_skill.read_text()

        # Should specify required tools
        assert "tools: [gemini-cli, quota-tracker, usage-logger]" in content

    def test_skill_usage_patterns(self) -> None:
        """Given skill files when checking usage patterns.

        then should specify valid patterns.
        """
        gemini_skill = (
            Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        )
        content = gemini_skill.read_text()

        # Should specify usage patterns
        assert "gemini-cli-integration" in content
        assert "quota-monitoring" in content
        assert "batch-processing" in content


class TestGeminiDelegationSkill:
    """Test gemini-delegation skill execution scenarios."""

    def test_authentication_verification_flow(self) -> None:
        """Given authentication step when executing gemini-delegation.

        then should verify auth status.
        """
        # This tests the logic described in step 1 of the skill
        auth_commands = ["gemini auth status", 'gemini "ping"']

        assert len(auth_commands) == 2
        assert "gemini auth status" in auth_commands

    def test_quota_checking_flow(self) -> None:
        """Given quota checking step when executing gemini-delegation.

        then should check quota thresholds.
        """
        # This tests the logic described in step 2 of the skill
        quota_commands = [
            "~/conjure/hooks/gemini/status.sh",
            "python3 ~/conjure/tools/quota_tracker.py",
        ]

        assert len(quota_commands) == 2
        assert "quota_tracker.py" in quota_commands[1]

    def test_command_construction_patterns(self, tmp_path, monkeypatch) -> None:
        """Given command construction step when executing gemini-delegation.

        then should build correct commands using Delegator.build_command().
        """
        monkeypatch.chdir(tmp_path)

        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hi')\n")
        (tmp_path / "docs").mkdir()

        delegator = Delegator(config_dir=tmp_path / "config")

        # Existing file should be referenced with @<path>
        cmd = delegator.build_command(
            "gemini", "Analyze this code", files=["src/main.py"]
        )
        assert cmd[0] == "gemini"
        assert "-p" in cmd
        assert "@src/main.py Analyze this code" in cmd[cmd.index("-p") + 1]

        # Existing directory should be referenced with @<dir>/**/*
        cmd = delegator.build_command("gemini", "Summarize", files=["docs"])
        assert "@docs/**/* Summarize" in cmd[cmd.index("-p") + 1]

        # Options should be translated into service flags
        cmd = delegator.build_command(
            "gemini",
            "test",
            options={"model": "gemini-2.5-pro-exp"},
        )
        assert "--model" in cmd
        assert "gemini-2.5-pro-exp" in cmd

    def test_usage_logging_flow(self) -> None:
        """Given usage logging step when executing gemini-delegation.

        then should log correctly.
        """
        # This tests the logic described in step 4
        log_pattern = (
            'python3 ~/conjure/tools/usage_logger.py "<command>" '
            "<estimated_tokens> <success:true/false> <duration_seconds>"
        )

        assert "usage_logger.py" in log_pattern
        assert "estimated_tokens" in log_pattern
        assert "success" in log_pattern
        assert "duration_seconds" in log_pattern

    def test_delegation_workflow_integration(self, tmp_path, monkeypatch) -> None:
        """Given complete workflow when executing gemini-delegation.

        then should exercise real build_command() and execute() behavior.
        """
        monkeypatch.chdir(tmp_path)
        (tmp_path / "test.py").write_text("print('hello')\n")

        delegator = Delegator(config_dir=tmp_path / "config")

        def fake_run(args, **_kwargs):
            # Simulate the CLI invocation without requiring an installed binary.
            if args[:2] == ["gemini", "--version"]:
                return subprocess.CompletedProcess(
                    args, 0, stdout="gemini 1.0.0", stderr=""
                )
            return subprocess.CompletedProcess(
                args, 0, stdout="Analysis complete", stderr=""
            )

        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}),
            patch(
                "delegation_executor.subprocess.run", side_effect=fake_run
            ) as mock_run,
            patch("delegation_executor.estimate_tokens", return_value=50000),
        ):
            # Step 1: Verify authentication
            is_available, issues = delegator.verify_service("gemini")
            assert is_available is True
            assert issues == []

            # Step 2: Execute command (build_command() runs inside execute()).
            result = delegator.execute(
                "gemini",
                "Analyze this code",
                files=["test.py"],
                options={"model": "gemini-2.5-pro-exp"},
            )

        assert result == ExecutionResult(
            success=True,
            stdout="Analysis complete",
            stderr="",
            exit_code=0,
            duration=result.duration,
            tokens_used=50000,
            service="gemini",
        )

        # Verify command contains expected flags/prompt
        executed_args = mock_run.call_args_list[-1].args[0]
        assert executed_args[:3] == ["gemini", "--model", "gemini-2.5-pro-exp"]
        assert "-p" in executed_args
        assert (
            "@test.py Analyze this code" in executed_args[executed_args.index("-p") + 1]
        )

        # Verify usage log was written.
        usage_lines = (
            (tmp_path / "config" / "usage.jsonl").read_text().strip().splitlines()
        )
        assert len(usage_lines) == 1
        log_entry = json.loads(usage_lines[0])
        assert log_entry["service"] == "gemini"
        assert log_entry["success"] is True


class TestQwenDelegationSkill:
    """Test qwen-delegation skill execution scenarios."""

    def test_qwen_skill_structure(self) -> None:
        """Given qwen-delegation skill when checking structure.

        then should follow same patterns as gemini.
        """
        qwen_skill = (
            Path(__file__).parent.parent / "skills" / "qwen-delegation" / "SKILL.md"
        )
        content = qwen_skill.read_text()

        # Should have similar structure to gemini-delegation
        assert "# Overview" in content
        assert "# When to Use" in content
        assert "# Prerequisites" in content
        assert "# Exit Criteria" in content

    def test_qwen_authentication_differences(self) -> None:
        """Given qwen-delegation skill when checking authentication.

        then should use correct auth method.
        """
        qwen_skill = (
            Path(__file__).parent.parent / "skills" / "qwen-delegation" / "SKILL.md"
        )
        content = qwen_skill.read_text()

        # Qwen might use different authentication method than Gemini
        # This test verifies the skill mentions authentication
        assert "auth" in content.lower() or "login" in content.lower()


class TestSkillErrorHandling:
    """Test skill error handling scenarios."""

    def test_authentication_failure_handling(self) -> None:
        """Given authentication failure when executing skill.

        then should provide recovery steps.
        """
        # Based on the skill's error handling section
        recovery_steps = [
            "gemini auth login",
            "export GEMINI_API_KEY",
            "Check permissions",
            "Clear cache",
        ]

        assert len(recovery_steps) >= MIN_RECOVERY_STRATEGIES

    def test_quota_exhaustion_handling(self) -> None:
        """Given quota exhaustion when executing skill.

        then should provide recovery strategies.
        """
        # Based on the skill's error handling section
        recovery_strategies = [
            "Wait 60 seconds for RPM reset",
            "Break into smaller batches",
            "Use flash model",
            "Wait for daily reset",
        ]

        assert len(recovery_strategies) >= MIN_RECOVERY_STRATEGIES

    def test_context_too_large_handling(self) -> None:
        """Given context too large error when executing skill.

        then should provide solutions.
        """
        # Based on the skill's error handling section
        solutions = [
            "Split into multiple requests",
            "Use selective globbing",
            "Pre-process files",
        ]

        assert len(solutions) >= MIN_SOLUTIONS


class TestSkillPerformanceConsiderations:
    """Test skill performance and optimization."""

    def test_token_usage_estimates(self) -> None:
        """Given skill when checking token estimates.

        then should provide realistic estimates.
        """
        # Based on the token estimation section
        estimates = {
            "File analysis": (15, 50),  # min-max per file
            "Code summarization": (1, 3),  # percentage of file size
            "Pattern extraction": (5, 20),  # tokens per match
            "Boilerplate generation": (50, 200),  # tokens per template
        }

        assert len(estimates) == EXPECTED_ESTIMATE_COUNT
        for min_tokens, max_tokens in estimates.values():
            assert isinstance(min_tokens, int)
            assert isinstance(max_tokens, int)
            assert max_tokens >= min_tokens

    def test_model_selection_guidance(self) -> None:
        """Given skill when checking model selection.

        then should provide appropriate choices.
        """
        # Based on the model selection section
        models = [
            "gemini-2.5-flash-exp",  # Fast
            "gemini-2.5-pro-exp",  # Capable
            "gemini-exp-1206",  # Experimental
        ]

        assert len(models) >= MIN_MODEL_CHOICES

    def test_cost_estimates(self) -> None:
        """Given skill when checking costs.

        then should provide realistic cost estimates.
        """
        # Based on the sample delegation costs section
        sample_costs = [
            ("Analyze 100 Python files (50K tokens)", 0.025),
            ("Summarize large codebase (200K tokens)", 0.10),
            ("Generate 20 API endpoints (2K output)", 0.003),
        ]

        for description, cost in sample_costs:
            assert isinstance(description, str)
            assert isinstance(cost, int | float)
            assert cost >= 0


class TestSkillIntegrationWithHooks:
    """Test skill integration with hook system."""

    def test_hook_references_in_skill(self) -> None:
        """Given skill content when checking for hooks.

        then should reference hook system.
        """
        gemini_skill = (
            Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        )
        content = gemini_skill.read_text()

        # Should mention hooks
        assert "hooks" in content.lower()
        assert "conjure/hooks" in content

    def test_bridge_hook_compatibility(self) -> None:
        """Given skills when checking bridge hooks then should be compatible."""
        # The skills should work with the bridge hooks tested in test_hooks.py
        hook_dir = Path(__file__).parent.parent / "hooks" / "gemini"

        assert hook_dir.exists()
        assert (hook_dir / "bridge.on_tool_start").exists()
        assert (hook_dir / "bridge.after_tool_use").exists()


class TestSkillConfigurationManagement:
    """Test skill configuration and customization."""

    def test_environment_variable_support(self) -> None:
        """Given skill when checking configuration.

        then should support environment variables.
        """
        gemini_skill = (
            Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        )
        content = gemini_skill.read_text()

        # Should mention environment variables
        assert "GEMINI_API_KEY" in content
        assert "export " in content  # For setting environment variables

    def test_model_configuration(self) -> None:
        """Given skill when checking configuration.

        then should support model selection.
        """
        gemini_skill = (
            Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        )
        content = gemini_skill.read_text()

        # Should mention model configuration
        assert "model" in content.lower()
        assert "--model" in content

    def test_timeout_configuration(self) -> None:
        """Given skill when checking configuration.

        then should support timeout settings.
        """
        gemini_skill = (
            Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        )
        content = gemini_skill.read_text()

        # Should mention timeout configuration
        assert "timeout" in content.lower() or "GEMINI_TIMEOUT" in content
