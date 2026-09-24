"""Two review styles that used to be asked for by hand each time.

`--concise` posts inline suggestion comments plus one short summary and
suppresses the test plan, the description update and the educational
paragraphs. `--hold-insights` widens Phase 4.6 so direction and
architecture feedback is presented in chat and posted only when the
reviewer selects it. Both were dictated verbatim in a prompt on
2026-09-22; a flag is how a request stops being retyped.

The seams these tests hold: the command usage line, the enforcement
options block that carves the two flags out of the MANDATORY outputs,
the skill exit criteria, the suggestion-comment module both platforms
post through, and the GitLab positioned-discussion row in leyline that
`/fix-pr` and `/resolve-threads` inherit. Nothing imports anything, so
a rename on any side would otherwise fail silently.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PLUGIN_ROOT.parents[1]

COMMAND = PLUGIN_ROOT / "commands" / "pr-review.md"
ENFORCEMENT = (
    PLUGIN_ROOT
    / "commands"
    / "pr-review"
    / "modules"
    / "review-workflow-enforcement.md"
)
PHASES_1_4 = (
    PLUGIN_ROOT / "commands" / "pr-review" / "modules" / "review-workflow-phases-1-4.md"
)
SKILL = PLUGIN_ROOT / "skills" / "pr-review" / "SKILL.md"
MODULE = PLUGIN_ROOT / "skills" / "pr-review" / "modules" / "suggestion-comments.md"
FIX_PR = PLUGIN_ROOT / "commands" / "fix-pr.md"
LEYLINE_MAPPING = (
    REPO_ROOT
    / "plugins"
    / "leyline"
    / "skills"
    / "git-platform"
    / "modules"
    / "command-mapping.md"
)

FLAGS = ("--concise", "--hold-insights")

# Each section answers a question the others cannot: what the fence
# looks like, how each platform anchors it to a line, when a plain
# comment is the honest shape, and what --concise changes.
MODULE_SECTIONS = (
    "## The Suggestion Fence",
    "## GitHub: Reviews API",
    "## GitLab: Positioned Discussion",
    "## When Not to Use a Suggestion",
    "## Under `--concise`",
)

# Verified against https://docs.gitlab.com/api/discussions/ on 2026-09-22.
GITLAB_POSITION_FIELDS = (
    "position[position_type]",
    "position[base_sha]",
    "position[head_sha]",
    "position[start_sha]",
    "position[new_path]",
    "position[old_path]",
    "position[new_line]",
)


def _usage_line() -> str:
    match = re.search(r"^usage: (.+)$", COMMAND.read_text(encoding="utf-8"), re.M)
    assert match is not None, "pr-review.md has no usage: line"
    return match.group(1)


class TestFlagsAreDeclared:
    @pytest.mark.parametrize("flag", FLAGS)
    def test_command_usage_line_declares_the_flag(self, flag: str) -> None:
        """A flag missing from usage: is one the reader cannot discover."""
        assert flag in _usage_line()

    @pytest.mark.parametrize("flag", FLAGS)
    def test_enforcement_options_block_documents_the_flag(self, flag: str) -> None:
        assert f"`{flag}`" in ENFORCEMENT.read_text(encoding="utf-8")

    @pytest.mark.parametrize("flag", FLAGS)
    def test_skill_exit_criteria_name_the_flag(self, flag: str) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        exit_criteria = skill.split("## Exit Criteria", 1)[1]
        assert f"With `{flag}`" in exit_criteria

    def test_no_insights_is_untouched_on_both_commands(self) -> None:
        """The Discussions flag stays, on by default, as confirmed 2026-09-22."""
        assert "--no-insights" in _usage_line()
        assert "--no-insights" in FIX_PR.read_text(encoding="utf-8")

    def test_the_new_flag_is_not_spelled_as_the_opposite_of_no_insights(self) -> None:
        """`--insights` beside `--no-insights` reads as a toggle. It is not."""
        assert re.search(r"(?<![-\w])--insights(?![-\w])", _usage_line()) is None


class TestConciseCarveOut:
    def test_enforcement_says_which_mandatory_outputs_concise_suppresses(self) -> None:
        """The checklist calls a review INCOMPLETE without three outputs.

        The flag has to say which of them it drops, or the checklist and
        the flag contradict each other and the reader picks one.
        """
        text = ENFORCEMENT.read_text(encoding="utf-8")
        concise = text.split("`--concise`", 1)[1]
        assert "test plan" in concise.lower()
        assert "description update" in concise.lower()

    def test_command_checklist_carves_concise_out_of_incomplete(self) -> None:
        """The command file calls a review INCOMPLETE without three outputs.

        Under --concise two of them are absent by design, so both the
        MANDATORY OUTPUTS line and the verification checklist must say so
        or the file contradicts the flag it documents.
        """
        text = COMMAND.read_text(encoding="utf-8")
        summary = text.split("**MANDATORY OUTPUTS:**", 1)[1].split("\n\n", 1)[0]
        checklist = text.split("### Verification Checklist", 1)[1].split("\n## ", 1)[0]
        assert "--concise" in summary
        assert "--concise" in checklist

    def test_skill_states_the_clarification_only_rule(self) -> None:
        """The dictated rule, kept as a sentence rather than a paraphrase."""
        assert "only for clarification" in SKILL.read_text(encoding="utf-8")

    def test_phase_4_routes_concise_through_the_suggestion_module(self) -> None:
        text = PHASES_1_4.read_text(encoding="utf-8")
        assert "--concise" in text
        assert "suggestion-comments.md" in text


class TestHoldInsightsExtendsPhase46:
    def test_skill_anchors_hold_insights_to_the_invariant_escalation(self) -> None:
        """One escalation path, widened, rather than a second one beside it."""
        skill = SKILL.read_text(encoding="utf-8")
        phase = skill.split("### Phase 4.6", 1)[1].split("### Phase 5", 1)[0]
        assert "--hold-insights" in phase

    def test_held_insights_reuse_the_backlog_prompt(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        phase = skill.split("### Phase 4.6", 1)[1].split("### Phase 5", 1)[0]
        assert "[y/n/select]" in phase


class TestSuggestionModule:
    def test_module_is_registered_in_skill_frontmatter(self) -> None:
        assert "modules/suggestion-comments.md" in SKILL.read_text(encoding="utf-8")

    @pytest.mark.parametrize("section", MODULE_SECTIONS)
    def test_module_carries_each_required_section(self, section: str) -> None:
        assert section in MODULE.read_text(encoding="utf-8")

    def test_module_shows_both_fence_spellings(self) -> None:
        """GitLab's fence carries a line-range suffix; GitHub's does not."""
        text = MODULE.read_text(encoding="utf-8")
        assert "```suggestion:-0+0" in text
        assert re.search(r"```suggestion\n", text) is not None

    @pytest.mark.parametrize("field", GITLAB_POSITION_FIELDS)
    def test_gitlab_section_names_each_position_field(self, field: str) -> None:
        text = MODULE.read_text(encoding="utf-8")
        gitlab = text.split("## GitLab: Positioned Discussion", 1)[1]
        assert field in gitlab

    def test_gitlab_section_says_where_the_shas_come_from(self) -> None:
        text = MODULE.read_text(encoding="utf-8")
        gitlab = text.split("## GitLab: Positioned Discussion", 1)[1]
        assert "merge_requests/" in gitlab
        assert "/versions" in gitlab
        assert "base_commit_sha" in gitlab


class TestGlabApiInvocations:
    def test_no_glab_api_command_in_sanctum_docs_uses_jq_flag(self) -> None:
        """`glab api` has no --jq flag, unlike `gh api`; pipe to jq instead.

        Continuation lines are joined first so a flag on the line after
        the endpoint is still seen as part of the command.
        """
        offenders = []
        for doc in sorted(PLUGIN_ROOT.rglob("*.md")):
            joined = re.sub(r"\\\n\s*", " ", doc.read_text(encoding="utf-8"))
            offenders.extend(
                f"{doc.relative_to(PLUGIN_ROOT)}: {line.strip()}"
                for line in joined.splitlines()
                if "glab api" in line and "--jq" in line
            )
        assert offenders == []


class TestLeylineInheritsThePositionedDiscussion:
    def test_command_mapping_has_a_positioned_mr_discussion_row(self) -> None:
        """`/fix-pr` and `/resolve-threads` map through leyline, not sanctum."""
        text = LEYLINE_MAPPING.read_text(encoding="utf-8")
        assert "merge_requests/N/discussions" in text
        assert "position[new_line]" in text
