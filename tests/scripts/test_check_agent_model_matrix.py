"""Tests for the agent model/effort matrix gate.

``scripts/check_agent_model_matrix.py`` enforces that every agent
definition under ``plugins/*/agents/`` pins an explicit model tier and
reasoning effort in its frontmatter. Omitting ``model`` makes a subagent
inherit the session model, so a search agent dispatched from an Opus
session silently runs on Opus. Pinning a dated model ID (for example
``claude-sonnet-4-6``) ties the agent to a model generation that will be
retired.

The gate is a hard failure rather than a ratchet: the backlog is zero as
of the change that introduced it, so the illegal state is unrepresentable
rather than merely capped.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_agent_model_matrix as gate
from check_agent_model_matrix import (
    MATRIX_DOC,
    VALID_EFFORTS,
    VALID_MODELS,
    AgentViolation,
    agent_slug,
    check_agent,
    check_roster_drift,
    check_skill,
    iter_agent_files,
    iter_skill_files,
    parse_frontmatter,
    parse_matrix_roster,
)


def write_agent(tmp_path: Path, body: str) -> Path:
    """Write an agent definition file and return its path."""
    path = tmp_path / "sample-agent.md"
    path.write_text(body, encoding="utf-8")
    return path


class TestParseFrontmatter:
    """Frontmatter extraction handles the shapes present in this repo."""

    def test_parses_simple_scalar_fields(self, tmp_path: Path) -> None:
        """
        Scenario: A plain frontmatter fence is read
        Given an agent file with top-level ``model`` and ``effort`` keys
        When its frontmatter is parsed
        Then the model value is returned
        And the effort value is returned alongside it
        """
        path = write_agent(
            tmp_path,
            "---\nname: demo\nmodel: sonnet\neffort: medium\n---\n\nBody.\n",
        )
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert fm["model"] == "sonnet"
        assert fm["effort"] == "medium"

    def test_ignores_model_mentions_in_the_body(self, tmp_path: Path) -> None:
        """
        Scenario: The body repeats a model key after the fence closes
        Given an agent pinned to haiku whose prose contains "model: opus"
        When its frontmatter is parsed
        Then the frontmatter value wins
        And the body mention is discarded
        """
        path = write_agent(
            tmp_path,
            "---\nname: demo\nmodel: haiku\neffort: low\n---\n\nmodel: opus\n",
        )
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert fm["model"] == "haiku"

    def test_survives_block_scalar_description(self, tmp_path: Path) -> None:
        """
        Scenario: A block-scalar description contains a key-like line
        Given a description block whose indented text reads "model: opus"
        When its frontmatter is parsed
        Then the indented line is not read as a top-level key
        And the real top-level model and effort are returned
        """
        path = write_agent(
            tmp_path,
            "---\nname: demo\ndescription: |\n  Multi line.\n  model: opus\n"
            "model: sonnet\neffort: high\n---\n\nBody.\n",
        )
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert fm["model"] == "sonnet"
        assert fm["effort"] == "high"

    @pytest.mark.parametrize("quote", ['"', "'"])
    def test_strips_quotes_from_values(self, tmp_path: Path, quote: str) -> None:
        """
        Scenario: An author quotes the frontmatter values
        Given an agent whose model and effort are written as quoted strings
        When its frontmatter is parsed
        Then the quotes are stripped
        And the quoted spelling is accepted by the vocabulary check
        """
        path = write_agent(
            tmp_path,
            f"---\nname: demo\nmodel: {quote}sonnet{quote}\n"
            f"effort: {quote}medium{quote}\n---\n\nBody.\n",
        )
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert fm["model"] == "sonnet"
        assert check_agent(path) == []

    def test_returns_empty_mapping_without_frontmatter(self, tmp_path: Path) -> None:
        """
        Scenario: The file has no frontmatter fence at all
        Given a markdown file that opens with a heading
        When its frontmatter is parsed
        Then an empty mapping is returned
        And no exception is raised
        """
        path = write_agent(tmp_path, "# No frontmatter here\n")
        assert parse_frontmatter(path.read_text(encoding="utf-8")) == {}


class TestCheckAgent:
    """A single agent file is judged against the matrix rules."""

    def test_accepts_a_fully_pinned_agent(self, tmp_path: Path) -> None:
        """
        Scenario: An agent pins both fields correctly
        Given an agent declaring a valid tier alias
        And a valid effort level
        When the agent is checked
        Then no violation is reported
        """
        path = write_agent(
            tmp_path,
            "---\nname: demo\nmodel: sonnet\neffort: medium\n---\n\nBody.\n",
        )
        assert check_agent(path) == []

    def test_rejects_missing_model(self, tmp_path: Path) -> None:
        """
        Scenario: An agent omits its model
        Given an agent whose frontmatter declares effort but no model
        When the agent is checked
        Then a missing-model violation is reported
        And the message names the inheritance hazard
        """
        path = write_agent(tmp_path, "---\nname: demo\neffort: medium\n---\n\nB.\n")
        violations = check_agent(path)
        assert [v.rule for v in violations] == ["missing-model"]
        assert "inherit" in violations[0].message

    def test_rejects_missing_effort(self, tmp_path: Path) -> None:
        """
        Scenario: An agent omits its effort level
        Given an agent declaring a model and no effort
        When the agent is checked
        Then a missing-effort violation is reported
        And reasoning depth is flagged as untuned
        """
        path = write_agent(tmp_path, "---\nname: demo\nmodel: sonnet\n---\n\nB.\n")
        assert [v.rule for v in check_agent(path)] == ["missing-effort"]

    @pytest.mark.parametrize("dated", ["claude-sonnet-4-6", "claude-opus-4-1"])
    def test_rejects_dated_model_ids(self, tmp_path: Path, dated: str) -> None:
        """
        Scenario: An agent pins a specific model generation
        Given an agent whose model is a dated ID
        When the agent is checked
        Then a dated-model-id violation is reported
        And the offending ID appears in the message
        """
        path = write_agent(
            tmp_path,
            f"---\nname: demo\nmodel: {dated}\neffort: medium\n---\n\nB.\n",
        )
        violations = check_agent(path)
        assert [v.rule for v in violations] == ["dated-model-id"]
        assert dated in violations[0].message

    def test_rejects_unknown_model_alias(self, tmp_path: Path) -> None:
        """
        Scenario: An agent invents a tier name
        Given an agent whose model is "turbo"
        And "turbo" is not a documented alias
        When the agent is checked
        Then an invalid-model violation is reported
        """
        path = write_agent(
            tmp_path,
            "---\nname: demo\nmodel: turbo\neffort: medium\n---\n\nB.\n",
        )
        assert [v.rule for v in check_agent(path)] == ["invalid-model"]

    def test_rejects_unknown_effort_level(self, tmp_path: Path) -> None:
        """
        Scenario: An agent invents an effort level
        Given an agent whose effort is "extreme"
        And "extreme" is outside the documented range
        When the agent is checked
        Then an invalid-effort violation is reported
        """
        path = write_agent(
            tmp_path,
            "---\nname: demo\nmodel: sonnet\neffort: extreme\n---\n\nB.\n",
        )
        assert [v.rule for v in check_agent(path)] == ["invalid-effort"]

    def test_rejects_inherit_as_an_explicit_value(self, tmp_path: Path) -> None:
        """
        Scenario: An agent spells out the default it was meant to replace
        Given an agent whose model is "inherit"
        And inherit is the behavior this gate exists to eliminate
        When the agent is checked
        Then an invalid-model violation is reported
        """
        path = write_agent(
            tmp_path,
            "---\nname: demo\nmodel: inherit\neffort: medium\n---\n\nB.\n",
        )
        assert [v.rule for v in check_agent(path)] == ["invalid-model"]

    def test_reports_every_violation_not_just_the_first(self, tmp_path: Path) -> None:
        """
        Scenario: An agent declares neither field
        Given an agent with only a name in its frontmatter
        When the agent is checked
        Then the missing model is reported
        And the missing effort is reported in the same pass
        """
        path = write_agent(tmp_path, "---\nname: demo\n---\n\nBody.\n")
        assert {v.rule for v in check_agent(path)} == {
            "missing-model",
            "missing-effort",
        }

    def test_violation_carries_the_offending_path(self, tmp_path: Path) -> None:
        """
        Scenario: A reader needs to find the file to fix
        Given an agent that violates a rule
        When the violation is inspected
        Then it is an AgentViolation
        And it names the file it came from
        """
        path = write_agent(tmp_path, "---\nname: demo\n---\n\nBody.\n")
        violation = check_agent(path)[0]
        assert isinstance(violation, AgentViolation)
        assert violation.path.name == "sample-agent.md"


class TestVocabulary:
    """The accepted vocabulary matches Claude Code's documented aliases."""

    def test_model_aliases_are_the_three_tiers(self) -> None:
        """
        Scenario: The tier vocabulary is fixed
        Given the Lightweight, Standard, and Deep tiers
        When the accepted model values are read
        Then they are exactly haiku, sonnet, and opus
        And no other alias is accepted
        """
        assert VALID_MODELS == frozenset({"haiku", "sonnet", "opus"})

    def test_effort_levels_cover_the_documented_range(self) -> None:
        """
        Scenario: The effort vocabulary is fixed
        Given the effort levels agent frontmatter supports
        When the accepted effort values are read
        Then they are exactly low, medium, and high
        And no other level is accepted
        """
        assert VALID_EFFORTS == frozenset({"low", "medium", "high"})


class TestRepositoryIsClean:
    """The live repository satisfies the gate."""

    def test_discovers_agent_files(self) -> None:
        """
        Scenario: Discovery runs over the plugins tree
        Given the agents shipped by every plugin
        When agent files are enumerated
        Then the full roster is found
        And every discovered path is a markdown file
        """
        files = iter_agent_files()
        assert len(files) >= 50, f"expected the full agent roster, got {len(files)}"
        assert all(p.suffix == ".md" for p in files)

    def test_excludes_vendored_virtualenvs(self) -> None:
        """
        Scenario: A vendored venv contains markdown that looks like an agent
        Given plugin directories that carry .venv trees
        When agent files are enumerated
        Then no path from a .venv is included
        And vendored code is never judged by this gate
        """
        assert not any(".venv" in p.parts for p in iter_agent_files())

    def test_every_agent_pins_model_and_effort(self) -> None:
        """
        Scenario: The shipped agents are compliant today
        Given every agent file in this repository
        When each is checked against the matrix rules
        Then no violation is reported
        And no agent inherits its model silently
        """
        violations = [v for path in iter_agent_files() for v in check_agent(path)]
        assert violations == [], "\n".join(
            f"{v.path}: [{v.rule}] {v.message}" for v in violations
        )


class TestAgentSlug:
    """An agent file maps to the ``plugin:name`` slug used in the docs."""

    def test_builds_slug_from_plugin_and_filename(self) -> None:
        """
        Scenario: A slug is derived for a roster comparison
        Given an agent file inside a plugin's agents directory
        When its slug is computed
        Then it reads as ``plugin:agent-name``
        And the plugin directory supplies the prefix
        """
        path = REPO_ROOT / "plugins" / "pensive" / "agents" / "code-reviewer.md"
        assert agent_slug(path) == "pensive:code-reviewer"

    def test_every_discovered_agent_yields_a_slug(self) -> None:
        """
        Scenario: The whole roster is slugged
        Given every agent file on disk
        When each is slugged
        Then all slugs carry exactly one colon separator
        And each is comparable against a matrix roster entry
        """
        slugs = [agent_slug(path) for path in iter_agent_files()]
        assert all(slug.count(":") == 1 for slug in slugs)


class TestParseMatrixRoster:
    """The matrix document's roster tables are machine-readable."""

    def test_extracts_slugs_from_roster_rows(self) -> None:
        """
        Scenario: A roster table is parsed
        Given a markdown table whose first cell is a backticked slug
        When the roster is parsed
        Then every slug is returned
        And the surrounding table header contributes nothing
        """
        doc = (
            "| Agent | Why |\n"
            "|-------|-----|\n"
            "| `pensive:code-reviewer` | Pattern matching |\n"
            "| `tome:triz-analyst` | Analogical reasoning |\n"
        )
        assert parse_matrix_roster(doc) == {
            "pensive:code-reviewer",
            "tome:triz-analyst",
        }

    def test_ignores_prose_mentions_of_agents(self) -> None:
        """
        Scenario: An agent is named in a paragraph, not a table
        Given prose that backticks an agent slug mid-sentence
        When the roster is parsed
        Then that mention is not counted as a roster entry
        And the roster stays empty
        """
        doc = "Note that `pensive:code-reviewer` moved down a tier.\n"
        assert parse_matrix_roster(doc) == set()

    def test_returns_empty_set_for_a_doc_with_no_tables(self) -> None:
        """
        Scenario: The document has no roster
        Given markdown containing only headings
        When the roster is parsed
        Then the result is empty rather than an error
        And a doc without tables is treated as documenting nothing
        """
        assert parse_matrix_roster("# Title\n\nSome text.\n") == set()


class TestRosterDrift:
    """The documented roster and the agents on disk stay in lockstep."""

    def test_reports_an_agent_missing_from_the_doc(self) -> None:
        """
        Scenario: A new agent ships without a matrix row
        Given a disk roster containing an agent the doc omits
        When drift is checked
        Then the undocumented agent is reported
        And its slug appears in the message
        """
        violations = check_roster_drift(
            documented={"a:one"}, on_disk={"a:one", "a:two"}
        )
        assert [v.rule for v in violations] == ["agent-undocumented"]
        assert "a:two" in violations[0].message

    def test_reports_a_doc_row_with_no_agent_on_disk(self) -> None:
        """
        Scenario: An agent is deleted but its matrix row survives
        Given a doc roster naming an agent that no longer exists
        When drift is checked
        Then the stale row is reported
        And the departed agent is named
        """
        violations = check_roster_drift(
            documented={"a:one", "a:gone"}, on_disk={"a:one"}
        )
        assert [v.rule for v in violations] == ["roster-stale"]
        assert "a:gone" in violations[0].message

    def test_reports_both_directions_at_once(self) -> None:
        """
        Scenario: The doc is stale in both directions
        Given a roster that both omits and over-claims agents
        When drift is checked
        Then both rules fire
        """
        violations = check_roster_drift(documented={"a:gone"}, on_disk={"a:new"})
        assert {v.rule for v in violations} == {"agent-undocumented", "roster-stale"}

    def test_passes_when_the_sets_match(self) -> None:
        """
        Scenario: The doc is accurate
        Given identical documented and on-disk rosters
        When drift is checked
        Then nothing is reported
        """
        assert check_roster_drift(documented={"a:one"}, on_disk={"a:one"}) == []

    def test_live_matrix_document_matches_the_agents_on_disk(self) -> None:
        """
        Scenario: The shipped matrix is accurate today
        Given docs/agent-model-matrix.md and the agents on disk
        When drift is checked
        Then the roster documents exactly the agents that exist

        This is the invariant that model-optimization-guide.md violated:
        a hand-maintained agent list with nothing checking it against
        reality drifts silently until it actively misinforms.
        """
        doc_text = (REPO_ROOT / MATRIX_DOC).read_text(encoding="utf-8")
        violations = check_roster_drift(
            documented=parse_matrix_roster(doc_text),
            on_disk={agent_slug(path) for path in iter_agent_files()},
        )
        assert violations == [], "\n".join(
            f"[{v.rule}] {v.message}" for v in violations
        )


class TestSkillModelIds:
    """Skills may omit a model, but never pin a dated one."""

    def test_allows_a_skill_with_no_model(self, tmp_path: Path) -> None:
        """
        Scenario: A skill declares no model
        Given a SKILL.md with no ``model`` field
        When it is checked
        Then nothing is reported
        And the omission is treated as deliberate

        A skill spawns no subagent, so omitting ``model`` carries none of
        the inheritance hazard that makes it a violation for an agent.
        """
        path = tmp_path / "SKILL.md"
        path.write_text("---\nname: demo\n---\n\nBody.\n", encoding="utf-8")
        assert check_skill(path) == []

    def test_allows_a_skill_pinning_a_tier_alias(self, tmp_path: Path) -> None:
        """
        Scenario: A skill pins a tier alias
        Given a SKILL.md with ``model: sonnet``
        And the alias is one the gate recognizes
        When it is checked
        Then nothing is reported
        """
        path = tmp_path / "SKILL.md"
        path.write_text("---\nname: demo\nmodel: sonnet\n---\n\nB.\n", encoding="utf-8")
        assert check_skill(path) == []

    def test_rejects_a_skill_pinning_a_dated_model_id(self, tmp_path: Path) -> None:
        """
        Scenario: A skill pins a generation-specific ID
        Given a SKILL.md with ``model: claude-sonnet-4-6``
        When it is checked
        Then the dated ID is reported
        And the message offers dropping the field as an alternative
        """
        path = tmp_path / "SKILL.md"
        path.write_text(
            "---\nname: demo\nmodel: claude-sonnet-4-6\n---\n\nB.\n", encoding="utf-8"
        )
        violations = check_skill(path)
        assert [v.rule for v in violations] == ["dated-model-id"]

    def test_discovers_skill_files(self) -> None:
        """
        Scenario: Skill discovery runs over the repository
        Given the plugins tree
        When skill files are enumerated
        Then many are found and none come from a vendored venv
        """
        files = iter_skill_files()
        assert len(files) >= 50
        assert not any(".venv" in path.parts for path in files)

    def test_no_skill_in_this_repository_pins_a_dated_model_id(self) -> None:
        """
        Scenario: The shipped skills are clean
        Given every SKILL.md under plugins/
        When each is checked
        Then no dated model ID survives
        And the four skills fixed by this change stay fixed
        """
        violations = [v for path in iter_skill_files() for v in check_skill(path)]
        assert violations == [], "\n".join(
            f"{v.path}: [{v.rule}] {v.message}" for v in violations
        )


class TestEnforcementIsWired:
    """The gate and the hook are actually invoked, not merely present.

    Every other test in this file imports the guard modules directly and
    would keep passing if the harness stopped calling them. These tests
    encode the invariant that the enforcement is connected.
    """

    def test_gate_runs_as_a_pre_commit_hook(self) -> None:
        """
        Scenario: Someone removes the gate from pre-commit
        Given .pre-commit-config.yaml
        When it is searched for the matrix gate entry
        Then the gate is wired in
        And a commit cannot bypass it

        Without this, deleting the pre-commit entry silently disables the
        gate while every unit test in this file still passes.
        """
        config = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        assert "scripts/check_agent_model_matrix.py" in config

    def test_dispatch_guard_is_registered_in_abstract_hooks(self) -> None:
        """
        Scenario: Someone removes the hook registration
        Given plugins/abstract/hooks/hooks.json
        When it is searched for the dispatch guard
        Then the guard is registered on PreToolUse for Agent dispatch
        And the harness will actually invoke it

        The hook's own tests import the module directly, so they cannot
        detect an unregistered hook.
        """

        hooks = json.loads(
            (REPO_ROOT / "plugins/abstract/hooks/hooks.json").read_text(
                encoding="utf-8"
            )
        )
        commands = [
            hook["command"]
            for entry in hooks["hooks"]["PreToolUse"]
            for hook in entry["hooks"]
        ]
        assert any("agent_dispatch_guard.py" in command for command in commands)

    def test_dispatch_guard_matches_the_agent_dispatch_tools(self) -> None:
        """
        Scenario: The registration exists but matches the wrong tool
        Given the PreToolUse entry carrying the dispatch guard
        When its matcher is read
        Then it matches both the Agent and legacy Task tool names
        """

        hooks = json.loads(
            (REPO_ROOT / "plugins/abstract/hooks/hooks.json").read_text(
                encoding="utf-8"
            )
        )
        matchers = [
            entry["matcher"]
            for entry in hooks["hooks"]["PreToolUse"]
            if any(
                "agent_dispatch_guard.py" in hook["command"] for hook in entry["hooks"]
            )
        ]
        assert matchers, "dispatch guard is not registered on PreToolUse"
        assert "Agent" in matchers[0]
        assert "Task" in matchers[0]

    def test_dispatch_guard_is_executable(self) -> None:
        """
        Scenario: The hook is registered but not executable
        Given the dispatch guard script
        When its permissions are read
        Then the owner execute bit is set

        Claude Code invokes the hook as a command, so a non-executable
        file fails at dispatch time rather than at test time.
        """

        path = REPO_ROOT / "plugins/abstract/hooks/agent_dispatch_guard.py"
        assert os.access(path, os.X_OK)

    def test_gate_triggers_on_every_file_kind_it_polices(self) -> None:
        """
        Scenario: The gate checks more file kinds than it watches
        Given the pre-commit entry's ``files`` pattern
        When a SKILL.md path and the matrix document are matched against it
        Then both trigger the gate
        And no policed file can change without the gate running

        The gate enforces three rules: agent frontmatter, dated model IDs
        in SKILL.md, and matrix roster drift. A ``files`` pattern covering
        only ``plugins/*/agents/*.md`` lets the other two be broken by a
        commit that never runs the gate.
        """
        config = yaml.safe_load(
            (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        )
        entries = [
            hook
            for repo in config["repos"]
            for hook in repo.get("hooks", [])
            if "check_agent_model_matrix.py" in str(hook.get("entry", ""))
        ]
        assert entries, "the matrix gate is not wired into pre-commit"
        pattern = re.compile(entries[0]["files"])

        policed = [
            "plugins/pensive/agents/code-reviewer.md",
            "plugins/sanctum/skills/test-updates/SKILL.md",
            MATRIX_DOC,
        ]
        unwatched = [path for path in policed if not pattern.search(path)]
        assert unwatched == [], (
            f"the gate checks these but does not run when they change: {unwatched}"
        )


class TestMain:
    """The command-line entry point reports and exits correctly.

    Every other test calls the check functions directly. These exercise
    ``main`` itself, which is what pre-commit actually runs: the exit
    code is the whole contract.
    """

    @staticmethod
    def build_repo(root: Path, *, agent: str, matrix: str | None) -> None:
        """Lay out a miniature repository for the gate to scan."""
        agents_dir = root / "plugins" / "demo" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "one.md").write_text(agent, encoding="utf-8")

        skill_dir = root / "plugins" / "demo" / "skills" / "thing"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: thing\n---\n\nBody.\n", encoding="utf-8"
        )

        if matrix is not None:
            doc = root / MATRIX_DOC
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text(matrix, encoding="utf-8")

    @pytest.fixture
    def sandbox(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """Point the gate's roots at a temporary repository."""

        def build(*, agent: str, matrix: str | None) -> None:
            self.build_repo(tmp_path, agent=agent, matrix=matrix)
            monkeypatch.setattr(gate, "REPO_ROOT", tmp_path)
            monkeypatch.setattr(gate, "PLUGINS_ROOT", tmp_path / "plugins")

        return build

    def test_exits_zero_when_everything_is_pinned(
        self, sandbox, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Scenario: A clean tree is scanned
        Given one agent pinning a valid model and effort
        And a matrix documenting exactly that agent
        When the gate runs
        Then it exits zero
        And the summary reports the counts it checked
        """
        sandbox(
            agent="---\nname: one\nmodel: sonnet\neffort: medium\n---\n\nB.\n",
            matrix="| Agent | Why |\n|--|--|\n| `demo:one` | Pattern work |\n",
        )
        assert gate.main() == 0
        assert "1 agents" in capsys.readouterr().out

    def test_exits_nonzero_and_names_the_offender(
        self, sandbox, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Scenario: An agent omits its model
        Given an agent whose frontmatter pins effort but no model
        When the gate runs
        Then it exits non-zero
        And stderr names the rule, the file, and the inheritance hazard
        """
        sandbox(
            agent="---\nname: one\neffort: medium\n---\n\nB.\n",
            matrix="| Agent | Why |\n|--|--|\n| `demo:one` | Pattern work |\n",
        )
        assert gate.main() == 1
        err = capsys.readouterr().err
        assert "missing-model" in err
        assert "one.md" in err
        assert "inherit" in err

    def test_reports_a_missing_matrix_document(
        self, sandbox, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Scenario: The matrix document is deleted
        Given a compliant agent and no matrix document on disk
        When the gate runs
        Then it exits non-zero with a matrix-missing violation
        And deleting the rationale is not a way to silence the gate

        Without this the document could be removed and every remaining
        test in this file would keep passing.
        """
        sandbox(
            agent="---\nname: one\nmodel: haiku\neffort: low\n---\n\nB.\n",
            matrix=None,
        )
        assert gate.main() == 1
        err = capsys.readouterr().err
        assert "matrix-missing" in err
        assert MATRIX_DOC in err

    def test_reports_roster_drift_through_the_entry_point(
        self, sandbox, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Scenario: A compliant agent is missing from the matrix
        Given an agent that pins both fields
        And a matrix document listing a different agent
        When the gate runs
        Then it exits non-zero
        And both drift directions are reported in one pass
        """
        sandbox(
            agent="---\nname: one\nmodel: opus\neffort: high\n---\n\nB.\n",
            matrix="| Agent | Why |\n|--|--|\n| `demo:other` | Stale row |\n",
        )
        assert gate.main() == 1
        err = capsys.readouterr().err
        assert "agent-undocumented" in err
        assert "roster-stale" in err

    def test_runs_as_a_subprocess_with_a_real_exit_code(self) -> None:
        """
        Scenario: pre-commit invokes the gate as a command
        Given this repository as it stands
        When the script runs as a subprocess
        Then it exits zero
        And the contract pre-commit depends on is exercised for real
        """
        completed = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts/check_agent_model_matrix.py")],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
            cwd=REPO_ROOT,
        )
        assert completed.returncode == 0, completed.stderr


class TestMatrixTierSectionsMatchFrontmatter:
    """The tier an agent is documented under matches the tier it pins.

    Roster drift compares slug sets, so an agent can sit in the wrong
    tier section forever: documented, present, and wrong. That is the
    exact rot ``model-optimization-guide.md`` died of, one level down.

    If this test breaks, the document and the frontmatter disagree about
    an agent's tier. Do not silently edit either one. Present three
    options to a human:

    1. Preserve: the document is right, fix the frontmatter.
    2. Layer: the frontmatter is right, move the row to its tier section.
    3. Revise: the tier boundaries themselves changed, which needs a
       rationale update in the "Placement rules" section.
    """

    # A roster heading names its tier: "### Standard (`sonnet` / `medium`)".
    _SECTION_RE = re.compile(r"^###\s+.*\(`([a-z]+)`\s*/\s*`([a-z]+)`\)")

    @classmethod
    def documented_tiers(cls) -> dict[str, tuple[str, str]]:
        """Map each documented slug to the (model, effort) of its section."""
        text = (REPO_ROOT / MATRIX_DOC).read_text(encoding="utf-8")
        tiers: dict[str, tuple[str, str]] = {}
        current: tuple[str, str] | None = None
        for line in text.splitlines():
            heading = cls._SECTION_RE.match(line)
            if heading:
                current = (heading.group(1), heading.group(2))
                continue
            row = re.match(r"^\|\s*`([a-z0-9-]+:[a-z0-9-]+)`\s*\|", line)
            if row and current is not None:
                tiers[row.group(1)] = current
        return tiers

    def test_every_roster_row_sits_under_a_tier_heading(self) -> None:
        """
        Scenario: The roster is parsed by section
        Given the matrix document's tier headings and roster rows
        When each row is attributed to the heading above it
        Then every documented slug lands under a tier
        And the section parse agrees with the gate's own roster parse
        """
        assert self.documented_tiers().keys() == parse_matrix_roster(
            (REPO_ROOT / MATRIX_DOC).read_text(encoding="utf-8")
        )

    def test_documented_tier_matches_the_pinned_frontmatter(self) -> None:
        """
        Scenario: An agent is moved between tiers in only one place
        Given the tier section each agent is documented under
        And the model and effort each agent pins in its frontmatter
        When the two are compared
        Then they agree for every agent
        And the document cannot quietly misinform about cost
        """
        documented = self.documented_tiers()
        mismatches = []
        for path in iter_agent_files():
            slug = agent_slug(path)
            if slug not in documented:
                continue
            fm = parse_frontmatter(path.read_text(encoding="utf-8"))
            actual = (fm.get("model"), fm.get("effort"))
            if actual != documented[slug]:
                mismatches.append(
                    f"{slug}: documented {documented[slug]}, pinned {actual}"
                )
        assert mismatches == [], "\n".join(mismatches)
