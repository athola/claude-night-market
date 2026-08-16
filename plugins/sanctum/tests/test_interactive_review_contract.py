"""Test: the interactive review loop stays wired to gauntlet's learning store.

`/pr-review --interactive` runs a socratic comprehension loop: the reviewer
states their understanding or asks a question, the agent answers from the
diff, then probes the gaps that answer revealed. Probe results are written
to gauntlet's progress store so a weak answer during review steers both
later probes and later gauntlet challenges.

That cross-plugin seam is the fragile part. It holds only while three
things agree: the categories the module tells the agent to tag probes with,
the categories gauntlet's selector weights on, and the CLI flag that
carries a record between them. Nothing imports anything, so a rename on
either side would otherwise fail silently and the two systems would drift
into separate, non-interacting trackers.

These tests name that agreement. Feature: probes that teach.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

PR_REVIEW = PLUGIN_ROOT / "skills" / "pr-review"
MODULE = PR_REVIEW / "modules" / "interactive-review.md"
SKILL = PR_REVIEW / "SKILL.md"
COMMAND = PLUGIN_ROOT / "commands" / "pr-review.md"

GAUNTLET_TRACKER = (
    REPO_ROOT / "plugins" / "gauntlet" / "scripts" / "progress_tracker.py"
)
GAUNTLET_PROGRESS = (
    REPO_ROOT / "plugins" / "gauntlet" / "src" / "gauntlet" / "progress.py"
)

# The sections a reader needs to run the loop. Each answers a question the
# reader cannot resolve from the others, so dropping one drops a capability.
REQUIRED_SECTIONS = (
    "## Turn Order",
    "## The Loop",
    "## Probe Categories",
    "## Recording Answers",
    "## Gate Policy",
    "## Without a Knowledge Base",
)


def _read(path: Path) -> str:
    assert path.exists(), f"missing required file: {path}"
    return path.read_text()


def _gauntlet_constant(path: Path, name: str) -> object:
    """Read a module-level constant without importing across plugins."""
    tree = ast.parse(_read(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if name in [t.id for t in node.targets if isinstance(t, ast.Name)]:
            return ast.literal_eval(node.value)
    pytest.fail(f"{path.name} no longer defines {name}")
    return None


def _gauntlet_categories() -> list[str]:
    """Extract _ALL_CATEGORIES from gauntlet without importing across plugins."""
    tree = ast.parse(_read(GAUNTLET_TRACKER))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "_ALL_CATEGORIES" in targets:
            return [ast.literal_eval(e) for e in node.value.elts]
    pytest.fail("gauntlet progress_tracker.py no longer defines _ALL_CATEGORIES")
    return []


class TestInteractiveReviewModule:
    """
    Feature: the interactive review module documents a runnable loop

    As a reviewer running /pr-review --interactive
    I want the module to specify turn order, scoring, and recording
    So that the loop behaves the same way on every PR
    """

    @pytest.mark.unit
    def test_module_exists(self) -> None:
        """
        Scenario: The module backing the flag is present
        Given the pr-review skill directory
        Then modules/interactive-review.md exists and is non-trivial
        """
        assert len(_read(MODULE).split()) > 200

    @pytest.mark.unit
    @pytest.mark.parametrize("section", REQUIRED_SECTIONS)
    def test_module_has_required_section(self, section: str) -> None:
        """
        Scenario: Every capability of the loop is documented
        Given the interactive review module
        Then each required section heading is present
        """
        assert section in _read(MODULE), f"module dropped section: {section}"

    @pytest.mark.unit
    def test_user_speaks_first(self) -> None:
        """
        Scenario: Turn order puts the reviewer first
        Given the module's turn order section
        Then it states the reviewer opens each round

        The whole point of the mode is that the reviewer's own
        understanding and questions steer what gets probed. An
        agent-first loop is a quiz, not a socratic exchange.
        """
        text = _read(MODULE).lower()
        assert "reviewer speaks first" in text

    @pytest.mark.unit
    def test_gate_policy_warns_and_never_blocks(self) -> None:
        """
        Scenario: A failed probe never changes the merge verdict
        Given the module's gate policy section
        Then it states probes never block the recommendation

        A probe that can block is a probe reviewers learn to game.
        """
        text = _read(MODULE).lower()
        assert "never block" in text
        assert "recommendation" in text


class TestGauntletSeam:
    """
    Feature: probe results reach gauntlet's adaptive selector

    As a developer whose weak areas should follow me between tools
    I want PR probes recorded in the same store gauntlet reads
    So that review and challenge sessions compound
    """

    @pytest.mark.unit
    def test_module_uses_gauntlet_category_taxonomy(self) -> None:
        """
        Scenario: Categories agree across the plugin boundary
        Given gauntlet's _ALL_CATEGORIES list
        Then the module tells the agent to tag probes with those same values

        gauntlet's select_entry() weights by category. A category the
        selector does not know is dead weight: it records, but never
        steers anything.
        """
        text = _read(MODULE)
        missing = [cat for cat in _gauntlet_categories() if cat not in text]
        assert not missing, f"module omits gauntlet categories: {missing}"

    @pytest.mark.unit
    def test_module_invokes_the_record_flag(self) -> None:
        """
        Scenario: The documented command is the one that exists
        Given the module's recording section
        Then it invokes progress_tracker.py with --record
        """
        text = _read(MODULE)
        assert "progress_tracker.py" in text
        assert "--record" in text

    @pytest.mark.unit
    def test_documented_interpreter_exists(self) -> None:
        """
        Scenario: The documented command is runnable as written
        Given the module's shell snippets
        Then they invoke python3, never bare python

        Bare `python` is absent on this repo's supported environments,
        so a snippet using it fails with `command not found` for anyone
        who copies it. The slop rules treat an unresolvable recommended
        command as a merge blocker.
        """
        for line in _read(MODULE).splitlines():
            stripped = line.strip()
            assert not stripped.startswith("python "), (
                f"snippet uses bare python, which does not resolve: {stripped}"
            )

    @pytest.mark.unit
    def test_record_flag_exists_in_gauntlet(self) -> None:
        """
        Scenario: The recording flag is real
        Given gauntlet's progress_tracker CLI
        Then it defines a --record argument

        Guards the module against citing a flag a gauntlet refactor removed.
        """
        assert '"--record"' in _read(GAUNTLET_TRACKER)

    @pytest.mark.unit
    def test_module_states_the_real_weak_threshold(self) -> None:
        """
        Scenario: The grading advice cites gauntlet's actual threshold
        Given gauntlet's _WEAK_CATEGORY_ACCURACY_THRESHOLD
        Then the module quotes that same number

        The module tells reviewers a lone `partial` earns no adaptive
        follow-up. That advice is only true at this exact threshold:
        measured at 0.5, a failed category is selected ~18% of the time
        against a ~13% baseline, while a `partial` scores exactly 0.5
        and clears nothing. Retuning gauntlet without updating the
        module would leave reviewers grading to a stale rule.
        """
        threshold = _gauntlet_constant(
            GAUNTLET_PROGRESS, "_WEAK_CATEGORY_ACCURACY_THRESHOLD"
        )
        assert f"`{threshold}`" in _read(MODULE), (
            f"module does not cite the real weak threshold {threshold}"
        )

    @pytest.mark.unit
    def test_module_degrades_without_knowledge_base(self) -> None:
        """
        Scenario: No .gauntlet knowledge base present
        Given the module's degradation section
        Then it states probes are still recorded
        """
        text = _read(MODULE).lower()
        assert "knowledge base" in text
        assert "still record" in text


class TestConsumersWired:
    """
    Feature: the flag is reachable from the command and the skill

    As a reviewer typing the command
    I want --interactive documented where I look for options
    So that the mode is discoverable rather than buried in a module
    """

    @pytest.mark.unit
    def test_command_documents_the_flag(self) -> None:
        """
        Scenario: The command file advertises --interactive
        Given commands/pr-review.md
        Then --interactive appears with an explanation
        """
        assert "--interactive" in _read(COMMAND)

    @pytest.mark.unit
    def test_skill_references_the_module(self) -> None:
        """
        Scenario: The skill routes to the module
        Given the pr-review SKILL.md
        Then it references modules/interactive-review.md
        """
        assert "interactive-review.md" in _read(SKILL)

    @pytest.mark.unit
    def test_skill_declares_exit_criteria(self) -> None:
        """
        Scenario: Modified SKILL.md carries exit criteria
        Given .claude/rules/skill-exit-criteria.md applies to every edit
        Then SKILL.md has an Exit Criteria section with checkboxes
        """
        text = _read(SKILL)
        assert "## Exit Criteria" in text
        head = text.split("## Exit Criteria", 1)[1]
        assert head.count("- [ ]") >= 3
