# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Contract tests for Sanctum agents.

The agents are markdown definitions that the harness loads, so their
behavior is what the definitions say. These tests pin the claims that
callers and sibling skills depend on: the tools an agent may use, the
skill it loads, the conventions it shares with that skill, and the
sections it promises to return.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
AGENTS = PLUGIN_ROOT / "agents"
SKILLS = PLUGIN_ROOT / "skills"


def _load(path: Path) -> tuple[dict, str]:
    """Split an agent or skill file into its frontmatter and body."""
    _, frontmatter, body = path.read_text().split("---\n", 2)
    return yaml.safe_load(frontmatter), body


def _section(body: str, heading: str) -> str:
    """Return the text under a markdown heading, up to the next heading."""
    match = re.search(
        rf"^#+ {re.escape(heading)}\n(.*?)(?=^#+ |\Z)", body, re.DOTALL | re.MULTILINE
    )
    assert match, f"heading {heading!r} not found"
    return match.group(1)


@pytest.fixture(scope="module")
def workspace_agent() -> tuple[dict, str]:
    return _load(AGENTS / "git-workspace-agent.md")


@pytest.fixture(scope="module")
def commit_agent() -> tuple[dict, str]:
    return _load(AGENTS / "commit-agent.md")


@pytest.fixture(scope="module")
def pr_agent() -> tuple[dict, str]:
    return _load(AGENTS / "pr-agent.md")


class TestGitWorkspaceAgent:
    """BDD tests for the Git Workspace agent."""

    def test_workspace_agent_tool_list_is_read_only(
        self, workspace_agent: tuple[dict, str]
    ) -> None:
        """GIVEN the agent promises read-only analysis.

        WHEN its tool list is read
        THEN it can read and run commands but has no tool that edits files.
        """
        meta, _body = workspace_agent
        assert "read-only analysis" in meta["description"]
        assert set(meta["tools"]) == {"Read", "Bash", "Glob", "Grep"}

    def test_workspace_agent_documents_branch_status_and_upstream_check(
        self, workspace_agent: tuple[dict, str]
    ) -> None:
        """GIVEN the agent's capabilities and output contract.

        WHEN they are read
        THEN it verifies branch, status and upstream and returns that summary.
        """
        _meta, body = workspace_agent
        assert "branch, status, and upstream" in _section(body, "Capabilities")
        assert "Repository state summary (branch, upstream, clean/dirty)" in _section(
            body, "Output"
        )

    def test_workspace_agent_documents_staged_unstaged_separation_and_file_breakdown(
        self, workspace_agent: tuple[dict, str]
    ) -> None:
        """GIVEN a repository with various types of changes.

        WHEN the agent analyzes the changes
        THEN it separates staged from unstaged and returns a per-file breakdown.
        """
        _meta, body = workspace_agent
        assert "Staged vs. unstaged change separation" in _section(
            body, "Git State Analysis"
        )
        assert "Change statistics with file breakdown" in _section(body, "Output")

    def test_workspace_agent_skill_exists_and_lists_its_progress_items(
        self, workspace_agent: tuple[dict, str]
    ) -> None:
        """GIVEN the agent loads a skill for its procedure.

        WHEN that skill is resolved
        THEN it exists and carries the progress items the agent works through.
        """
        meta, _body = workspace_agent
        plugin, name = meta["skills"].split(":")
        assert plugin == "sanctum"
        _skill_meta, skill_body = _load(SKILLS / name / "SKILL.md")
        tracking = _section(skill_body, "Required Progress Tracking")
        assert "`git-review:repo-confirmed`" in tracking
        assert "`git-review:diff-stat`" in tracking

    def test_workspace_agent_skill_documents_merge_abort_and_forbids_no_verify(
        self, workspace_agent: tuple[dict, str]
    ) -> None:
        """GIVEN a failing hook or a merge conflict during the review.

        WHEN the agent's skill is consulted
        THEN it names the recovery and rules out bypassing the hook.
        """
        meta, _body = workspace_agent
        _skill_meta, skill_body = _load(
            SKILLS / meta["skills"].split(":")[1] / "SKILL.md"
        )
        troubleshooting = _section(skill_body, "Troubleshooting")
        assert "`git merge --abort`" in troubleshooting
        assert re.search(r"instead\s+of using `--no-verify`", troubleshooting)

    def test_workspace_agent_documents_downstream_intent_and_next_step_output(
        self, workspace_agent: tuple[dict, str]
    ) -> None:
        """GIVEN a repository state analysis.

        WHEN the agent provides recommendations
        THEN they follow the downstream intent the caller declared.
        """
        _meta, body = workspace_agent
        assert "Downstream intent (commit, PR, review, exploration)" in _section(
            body, "Usage"
        )
        assert "Recommendations for next steps" in _section(body, "Output")

    def test_agent_returns_early_for_a_single_git_command(
        self, workspace_agent: tuple[dict, str]
    ) -> None:
        """GIVEN a request that one git command answers.

        WHEN the agent runs its complexity check
        THEN it hands the command back to the parent instead of analyzing.
        """
        _meta, body = workspace_agent
        check = _section(body, "Step 0: Complexity Check (MANDATORY)")
        assert '"SIMPLE: Parent runs command directly"' in check


class TestCommitAgent:
    """BDD tests for the Commit agent."""

    def test_commit_agent_types_match_commit_messages_skill(
        self, commit_agent: tuple[dict, str]
    ) -> None:
        """The agent picks from the same commit types as the commit-messages skill."""
        _meta, body = commit_agent
        agent_types = re.search(
            r"Type selection \(([a-z, ]+)\)", _section(body, "Conventional Commits")
        )
        assert agent_types
        skill = (SKILLS / "commit-messages" / "SKILL.md").read_text()
        classify = re.search(r"\*\*Classify\*\*.*?(?=\n\d\. )", skill, re.DOTALL)
        assert classify
        assert set(agent_types.group(1).split(", ")) == set(
            re.findall(r"`([a-z]+)`", classify.group(0))
        )

    def test_commit_agent_documents_50_char_subject_and_72_char_body(
        self, commit_agent: tuple[dict, str]
    ) -> None:
        """The agent holds the subject to 50 characters and the body to 72."""
        _meta, body = commit_agent
        conventions = _section(body, "Conventional Commits")
        assert "Subject line formatting (imperative, ≤50 chars)" in conventions
        assert "Body wrapping at 72 characters" in conventions

    def test_commit_agent_documents_breaking_change_and_split_guidance(
        self, commit_agent: tuple[dict, str]
    ) -> None:
        """A breaking change maps to a major bump, and a broad change gets split."""
        _meta, body = commit_agent
        assert "Breaking change detection → major bump" in _section(
            body, "Semantic Versioning"
        )
        assert "Format BREAKING CHANGE footers" in _section(body, "Capabilities")
        assert "Suggestions for splitting if changes are too broad" in _section(
            body, "Output"
        )


class TestPRAgent:
    """BDD tests for the Pull Request agent."""

    def test_agent_prepares_pr_with_the_template_sections(
        self, pr_agent: tuple[dict, str]
    ) -> None:
        """Every prose section the agent fills is a heading in pr-prep's template."""
        _meta, body = pr_agent
        agent_template = _section(body, "PR Template")
        assert "sanctum:pr-prep/modules/pr-template.md" in agent_template
        template = (SKILLS / "pr-prep" / "modules" / "pr-template.md").read_text()
        # The structure is a fenced example whose own headings would end a
        # heading-bounded section early, so slice up to the next section.
        structure = template.split("## The structure", 1)[1].split(
            "## Section guidance", 1
        )[0]
        for section in ("Why", "What and how", "Test plan", "Checklist"):
            assert section in agent_template, section
            assert f"## {section}\n" in structure, section

    def test_pr_agent_documents_quality_gates_and_reports_each_result(
        self, pr_agent: tuple[dict, str]
    ) -> None:
        """The agent runs format, lint and tests, and reports each gate's result."""
        _meta, body = pr_agent
        assert "**Quality Execution**: Run formatting, linting, and tests" in body
        assert "Quality gate results (pass/fail for each)" in _section(body, "Output")
        assert (SKILLS / "pr-prep" / "modules" / "quality-gates.md").is_file()

    def test_agent_names_reviewers_only_outside_codeowners_routing(
        self, pr_agent: tuple[dict, str]
    ) -> None:
        """The facts table's Who row names a reviewer only when codeowners will not."""
        _meta, body = pr_agent
        assert "Facts table: Who, Where (internal and external), When" in _section(
            body, "PR Template"
        )
        template = (SKILLS / "pr-prep" / "modules" / "pr-template.md").read_text()
        assert "Codeowners handle routine reviewer assignment" in _section(
            template, "The facts table"
        )
