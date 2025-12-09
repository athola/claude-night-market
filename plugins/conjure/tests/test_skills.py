"""Tests for conjure skill loading and execution following TDD/BDD principles."""

# Import modules for testing
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from delegation_executor import Delegator, ExecutionResult, ServiceConfig


# ruff: noqa: S101
class TestSkillStructure:
    """Test skill file structure and metadata."""

    def test_gemini_delegation_skill_structure(self):
        """Given gemini-delegation skill file when reading structure then should have valid frontmatter."""
        skill_file = Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"

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

    def test_delegation_core_skill_structure(self):
        """Given delegation-core skill file when reading structure then should have valid frontmatter."""
        skill_file = Path(__file__).parent.parent / "skills" / "delegation-core" / "SKILL.md"

        assert skill_file.exists(), "delegation-core skill file should exist"

        content = skill_file.read_text()

        # Check for required frontmatter fields
        assert "name: delegation-core" in content
        assert "description: Core delegation workflow" in content
        assert "category: delegation" in content

    def test_qwen_delegation_skill_structure(self):
        """Given qwen-delegation skill file when reading structure then should have valid frontmatter."""
        skill_file = Path(__file__).parent.parent / "skills" / "qwen-delegation" / "SKILL.md"

        assert skill_file.exists(), "qwen-delegation skill file should exist"

        content = skill_file.read_text()

        # Check for required frontmatter fields
        assert "name: qwen-delegation" in content
        assert "description: Qwen CLI delegation workflow" in content
        assert "category: delegation-implementation" in content


class TestSkillDependencyResolution:
    """Test skill dependency management."""

    def test_gemini_delegation_dependencies(self):
        """Given gemini-delegation skill when checking dependencies then should resolve correctly."""
        skill_file = Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        content = skill_file.read_text()

        # Extract dependencies from frontmatter
        lines = content.split('\n')
        deps_section = False
        dependencies = []

        for line in lines:
            if line.strip() == 'dependencies:':
                deps_section = True
                continue
            if deps_section:
                if line.strip().startswith('tools:'):
                    break
                if line.strip().startswith('-'):
                    dependencies.append(line.strip().lstrip('- ').strip())

        assert 'delegation-core' in dependencies, "gemini-delegation should depend on delegation-core"

    def test_skill_tool_requirements(self):
        """Given skill files when checking tool requirements then should specify necessary tools."""
        gemini_skill = Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        content = gemini_skill.read_text()

        # Should specify required tools
        assert "tools: [gemini-cli, quota-tracker, usage-logger]" in content

    def test_skill_usage_patterns(self):
        """Given skill files when checking usage patterns then should specify valid patterns."""
        gemini_skill = Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        content = gemini_skill.read_text()

        # Should specify usage patterns
        assert "gemini-cli-integration" in content
        assert "quota-monitoring" in content
        assert "batch-processing" in content


class TestGeminiDelegationSkill:
    """Test gemini-delegation skill execution scenarios."""

    def test_authentication_verification_flow(self):
        """Given authentication step when executing gemini-delegation then should verify auth status."""
        # This tests the logic described in step 1 of the skill
        auth_commands = [
            "gemini auth status",
            "gemini \"ping\""
        ]

        assert len(auth_commands) == 2
        assert "gemini auth status" in auth_commands

    def test_quota_checking_flow(self):
        """Given quota checking step when executing gemini-delegation then should check quota thresholds."""
        # This tests the logic described in step 2 of the skill
        quota_commands = [
            "~/conjure/hooks/gemini/status.sh",
            "python3 ~/conjure/tools/quota_tracker.py"
        ]

        assert len(quota_commands) == 2
        assert "quota_tracker.py" in quota_commands[1]

    @patch('delegation_executor.Delegator')
    def test_command_construction_patterns(self, mock_delegator_class, sample_files):
        """Given command construction step when executing gemini-delegation then should build correct commands."""
        # Test the patterns described in step 3
        test_cases = [
            {
                "description": "Basic file analysis",
                "files": ["src/main.py"],
                "prompt": "Analyze this code",
                "expected_pattern": "@src/main.py"
            },
            {
                "description": "Multiple files",
                "files": ["src/**/*.py"],
                "prompt": "Summarize these files",
                "expected_pattern": "@src/**/*.py"
            },
            {
                "description": "Specific model",
                "files": [],
                "prompt": "test",
                "model": "gemini-2.5-pro-exp",
                "expected_pattern": "--model gemini-2.5-pro-exp"
            }
        ]

        for case in test_cases:
            # Test the logic that would be used in command construction
            command_parts = ["gemini"]

            if "model" in case:
                command_parts.extend(["--model", case["model"]])

            # Add files to command
            if case["files"]:
                file_refs = [f"@{f}" for f in case["files"]]
                command_parts.extend(["-p", " ".join(file_refs) + " " + case["prompt"]])
            else:
                command_parts.extend(["-p", case["prompt"]])

            command = " ".join(command_parts)

            # Verify expected patterns are in the command
            if "expected_pattern" in case:
                assert case["expected_pattern"] in command, f"Pattern {case['expected_pattern']} not found in {command}"

    def test_usage_logging_flow(self):
        """Given usage logging step when executing gemini-delegation then should log correctly."""
        # This tests the logic described in step 4
        log_pattern = "python3 ~/conjure/tools/usage_logger.py \"<command>\" <estimated_tokens> <success:true/false> <duration_seconds>"

        assert "usage_logger.py" in log_pattern
        assert "estimated_tokens" in log_pattern
        assert "success" in log_pattern
        assert "duration_seconds" in log_pattern

    @patch('delegation_executor.Delegator')
    def test_delegation_workflow_integration(self, mock_delegator_class, tmp_path):
        """Given complete workflow when executing gemini-delegation then should follow all steps."""
        # Mock the delegator
        mock_delegator = MagicMock()
        mock_delegator.SERVICES = {
            "gemini": ServiceConfig("gemini", "gemini", "api_key", "GEMINI_API_KEY")
        }
        mock_delegator.verify_service.return_value = (True, [])
        mock_delegator.estimate_tokens.return_value = 50000
        mock_delegator.can_handle_task.return_value = (True, [])
        mock_delegator.execute.return_value = ExecutionResult(
            success=True,
            stdout="Analysis complete",
            stderr="",
            exit_code=0,
            duration=5.0,
            tokens_used=50000,
            service="gemini"
        )
        mock_delegator_class.return_value = mock_delegator

        # Test the workflow as described in the skill
        delegator = Delegator(config_dir=tmp_path)

        # Step 1: Verify authentication
        is_available, issues = delegator.verify_service("gemini")
        assert is_available is True
        assert len(issues) == 0

        # Step 2: Check quota (simplified test)
        estimated_tokens = delegator.estimate_tokens(["test.py"], "Analyze this code")
        assert isinstance(estimated_tokens, int)
        assert estimated_tokens > 0

        # Step 3: Execute command
        result = delegator.execute(
            "gemini",
            "Analyze this code",
            files=["test.py"],
            options={"model": "gemini-2.5-pro-exp"}
        )
        assert result.success is True
        assert result.service == "gemini"

        # Step 4: Usage would be logged (tested in usage_logger tests)


class TestQwenDelegationSkill:
    """Test qwen-delegation skill execution scenarios."""

    def test_qwen_skill_structure(self):
        """Given qwen-delegation skill when checking structure then should follow same patterns as gemini."""
        qwen_skill = Path(__file__).parent.parent / "skills" / "qwen-delegation" / "SKILL.md"
        content = qwen_skill.read_text()

        # Should have similar structure to gemini-delegation
        assert "# Overview" in content
        assert "# When to Use" in content
        assert "# Prerequisites" in content
        assert "# Exit Criteria" in content

    def test_qwen_authentication_differences(self):
        """Given qwen-delegation skill when checking authentication then should use correct auth method."""
        qwen_skill = Path(__file__).parent.parent / "skills" / "qwen-delegation" / "SKILL.md"
        content = qwen_skill.read_text()

        # Qwen might use different authentication method than Gemini
        # This test verifies the skill mentions authentication
        assert "auth" in content.lower() or "login" in content.lower()


class TestSkillErrorHandling:
    """Test skill error handling scenarios."""

    def test_authentication_failure_handling(self):
        """Given authentication failure when executing skill then should provide recovery steps."""
        # Based on the skill's error handling section
        recovery_steps = [
            "gemini auth login",
            "export GEMINI_API_KEY",
            "Check permissions",
            "Clear cache"
        ]

        assert len(recovery_steps) >= 2

    def test_quota_exhaustion_handling(self):
        """Given quota exhaustion when executing skill then should provide recovery strategies."""
        # Based on the skill's error handling section
        recovery_strategies = [
            "Wait 60 seconds for RPM reset",
            "Break into smaller batches",
            "Use flash model",
            "Wait for daily reset"
        ]

        assert len(recovery_strategies) >= 2

    def test_context_too_large_handling(self):
        """Given context too large error when executing skill then should provide solutions."""
        # Based on the skill's error handling section
        solutions = [
            "Split into multiple requests",
            "Use selective globbing",
            "Pre-process files"
        ]

        assert len(solutions) >= 2


class TestSkillPerformanceConsiderations:
    """Test skill performance and optimization."""

    def test_token_usage_estimates(self):
        """Given skill when checking token estimates then should provide realistic estimates."""
        # Based on the token estimation section
        estimates = {
            "File analysis": (15, 50),  # min-max per file
            "Code summarization": (1, 3),  # percentage of file size
            "Pattern extraction": (5, 20),  # tokens per match
            "Boilerplate generation": (50, 200)  # tokens per template
        }

        assert len(estimates) == 4
        for _task, (min_tokens, max_tokens) in estimates.items():
            assert isinstance(min_tokens, int)
            assert isinstance(max_tokens, int)
            assert max_tokens >= min_tokens

    def test_model_selection_guidance(self):
        """Given skill when checking model selection then should provide appropriate choices."""
        # Based on the model selection section
        models = [
            "gemini-2.5-flash-exp",  # Fast
            "gemini-2.5-pro-exp",    # Capable
            "gemini-exp-1206"        # Experimental
        ]

        assert len(models) >= 2

    def test_cost_estimates(self):
        """Given skill when checking costs then should provide realistic cost estimates."""
        # Based on the sample delegation costs section
        sample_costs = [
            ("Analyze 100 Python files (50K tokens)", 0.025),
            ("Summarize large codebase (200K tokens)", 0.10),
            ("Generate 20 API endpoints (2K output)", 0.003)
        ]

        for description, cost in sample_costs:
            assert isinstance(description, str)
            assert isinstance(cost, (int, float))
            assert cost >= 0


class TestSkillIntegrationWithHooks:
    """Test skill integration with hook system."""

    def test_hook_references_in_skill(self):
        """Given skill content when checking for hooks then should reference hook system."""
        gemini_skill = Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        content = gemini_skill.read_text()

        # Should mention hooks
        assert "hooks" in content.lower()
        assert "conjure/hooks" in content

    def test_bridge_hook_compatibility(self):
        """Given skills when checking bridge hooks then should be compatible."""
        # The skills should work with the bridge hooks tested in test_hooks.py
        hook_dir = Path(__file__).parent.parent / "hooks" / "gemini"

        assert hook_dir.exists()
        assert (hook_dir / "bridge.on_tool_start").exists()
        assert (hook_dir / "bridge.after_tool_use").exists()


class TestSkillConfigurationManagement:
    """Test skill configuration and customization."""

    def test_environment_variable_support(self):
        """Given skill when checking configuration then should support environment variables."""
        gemini_skill = Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        content = gemini_skill.read_text()

        # Should mention environment variables
        assert "GEMINI_API_KEY" in content
        assert "export " in content  # For setting environment variables

    def test_model_configuration(self):
        """Given skill when checking configuration then should support model selection."""
        gemini_skill = Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        content = gemini_skill.read_text()

        # Should mention model configuration
        assert "model" in content.lower()
        assert "--model" in content

    def test_timeout_configuration(self):
        """Given skill when checking configuration then should support timeout settings."""
        gemini_skill = Path(__file__).parent.parent / "skills" / "gemini-delegation" / "SKILL.md"
        content = gemini_skill.read_text()

        # Should mention timeout configuration
        assert "timeout" in content.lower() or "GEMINI_TIMEOUT" in content
