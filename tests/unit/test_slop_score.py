"""The CI slop gate scores from the YAML, not from a copy of it.

`slop-check.yml` carried its own inline `TIER1=`/`TIER2=` grep
alternations. `data/languages/en.yaml` is documented as the single
pattern source that `Skill(scribe:slop-detector)` loads at runtime, so
the gate was enforcing a snapshot of it: every Tier 5 category added
since -- spatial copula, negative parallelism, performative honesty and
the rest -- was invisible to CI, and a new one would be too.

These tests pin the property that fixes it. The scorer reads the YAML,
so adding a category to the YAML changes what CI catches with no
workflow edit.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "slop_score.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "plugins" / "scribe" / "src"))

from slop_score import (  # noqa: E402 - scripts/ must join sys.path above before this resolves
    _legible,
    audit_text,
    load_allowlist,
    load_exclude_patterns,
    score_text,
)


class TestScoringSourcesFromTheYaml:
    """Feature: the gate and the skill read one pattern source."""

    @pytest.mark.unit
    def test_a_tier1_word_scores(self) -> None:
        """Scenario: the vocabulary tiers still count."""
        assert score_text("This is a comprehensive guide. " * 5).score > 0

    @pytest.mark.unit
    def test_a_tier5_category_scores(self) -> None:
        """Scenario: a structural category the old grep could not see.

        The inline alternation held single words. A regex category like
        litotes cannot be expressed that way, which is why the gate
        never saw one.
        """
        clean = "The parser accepts flat blocks. " * 10
        slopped = clean + "This failure is not uncommon."
        assert score_text(slopped).score > score_text(clean).score

    @pytest.mark.unit
    def test_the_new_negation_categories_reach_the_gate(self) -> None:
        """Scenario: both high-confidence negation categories count."""
        base = "The exporter emits JSON. " * 10
        for phrase in ("This is not uncommon.", "Its value cannot be overstated."):
            assert score_text(base + phrase).score > score_text(base).score

    @pytest.mark.unit
    def test_clean_prose_scores_zero(self) -> None:
        """Scenario: plain technical prose is not penalized."""
        text = "The cache stores one entry per transcript path. " * 8
        assert score_text(text).score == 0

    @pytest.mark.unit
    def test_findings_name_their_category(self) -> None:
        """Scenario: the report says which rule fired, not just a number."""
        result = score_text("This failure is not uncommon. " * 10)
        assert "litotes" in {finding.category for finding in result.findings}

    @pytest.mark.unit
    def test_empty_text_is_zero_rather_than_a_division_error(self) -> None:
        """Guard: a file with no words has no score."""
        assert score_text("").score == 0


class TestCodeIsExcluded:
    """Feature: patterns inside code blocks are syntax, not prose."""

    @pytest.mark.unit
    def test_fenced_code_does_not_score(self) -> None:
        """Scenario: a fence mentioning a slop word is not slop."""
        text = "The parser accepts flat blocks. " * 10
        fenced = text + "\n```python\n# comprehensive not uncommon\n```\n"
        assert score_text(fenced).score == score_text(text).score


class TestCommandLine:
    """Feature: the workflow can call it and read a threshold verdict."""

    @pytest.mark.integration
    def test_exits_zero_on_clean_input(self, tmp_path: Path) -> None:
        """Scenario: a clean file passes the gate."""
        doc = tmp_path / "clean.md"
        doc.write_text("The cache stores one entry per transcript path.\n" * 8)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--threshold", "3.0", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    @pytest.mark.integration
    def test_exits_nonzero_when_a_file_is_over_threshold(self, tmp_path: Path) -> None:
        """Scenario: a slopped file fails the gate and is named."""
        doc = tmp_path / "slop.md"
        doc.write_text(
            "This comprehensive tapestry cannot be overstated. "
            "It is not uncommon to delve into the intricate.\n"
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--threshold", "3.0", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 1
        assert "slop.md" in result.stdout


class TestLowConfidenceDoesNotGate:
    """Feature: a merge fails only on findings the repo calls actionable.

    `.claude/rules/slop-scan-for-docs.md` says a `confidence: low`
    finding is surfaced for human decision and never auto-applied.
    Gating on one contradicts that. Measured on this repository, six
    files under `docs/` and `book/src/` sit above the threshold on
    low-confidence categories alone.
    """

    @pytest.mark.unit
    def test_a_low_confidence_category_adds_no_score(self) -> None:
        """Scenario: a semicolon splice is reported and costs nothing."""
        clean = "The exporter emits JSON. " * 10
        spliced = clean + "The system is fast; it scales."
        assert score_text(spliced).score == score_text(clean).score

    @pytest.mark.unit
    def test_a_low_confidence_category_is_still_reported(self) -> None:
        """Scenario: not scoring it is not the same as hiding it."""
        spliced = "The exporter emits JSON. " * 10 + "The system is fast; it scales."
        categories = {finding.category for finding in score_text(spliced).findings}
        assert "semicolon_splice" in categories

    @pytest.mark.unit
    def test_a_high_confidence_category_still_gates(self) -> None:
        """Guard: the exemption is scoped to low confidence only."""
        clean = "The exporter emits JSON. " * 10
        assert (
            score_text(clean + "This is not uncommon.").score > score_text(clean).score
        )


class TestProjectAllowlist:
    """Feature: a word used correctly in this domain can be exempted.

    `Skill(scribe:slop-detector)` module `config-file.md` documents
    `.slop-config.yaml` with an `allowlist` field, for the case its own
    example names: a marker word that is a term of art here. The
    archetypes plugin is built around the word "paradigm", which tier 2
    carries for "paradigm shift".

    `allowlist` and `exclude_patterns` are read. The rest of the
    documented schema is not implemented by this scorer, and a config
    that sets it gets no error and no effect, which is worth knowing
    before relying on it.
    """

    @pytest.mark.unit
    def test_an_allowlisted_word_stops_scoring(self, tmp_path: Path) -> None:
        """Scenario: the exempted word costs nothing."""
        config = tmp_path / ".slop-config.yaml"
        config.write_text("allowlist:\n  - paradigm\n")
        allow = load_allowlist(config)
        text = "The paradigm selector runs first. " * 8
        assert score_text(text, allowlist=allow).score < score_text(text).score

    @pytest.mark.unit
    def test_a_missing_config_is_an_empty_allowlist(self, tmp_path: Path) -> None:
        """Guard: no config file is not an error."""
        assert load_allowlist(tmp_path / "absent.yaml") == frozenset()

    @pytest.mark.unit
    def test_allowlisting_does_not_exempt_other_words(self, tmp_path: Path) -> None:
        """Guard: the exemption is per word, not a blanket off switch."""
        config = tmp_path / ".slop-config.yaml"
        config.write_text("allowlist:\n  - paradigm\n")
        allow = load_allowlist(config)
        assert score_text("This comprehensive guide. " * 8, allowlist=allow).score > 0

    @pytest.mark.unit
    def test_the_repository_config_documents_every_exemption(self) -> None:
        """Scenario: each allowlisted word carries a written reason.

        An allowlist without reasons becomes a place to silence
        findings. A trailing comment per entry keeps the next reader
        able to challenge one.
        """
        config = REPO_ROOT / ".slop-config.yaml"
        assert config.is_file()
        entries = [
            line
            for line in config.read_text().splitlines()
            if line.strip().startswith("- ")
        ]
        assert entries
        for line in entries:
            assert "#" in line, f"allowlist entry has no reason: {line.strip()!r}"


class TestAuditMode:
    """Feature: every named pattern reports a file and a line.

    The gate answers "does this merge". Audit mode answers "where is
    it", which is the question a person fixing slop actually has. The
    default output names a category with no location, so locating each
    hit fell back on reading the repository by hand.

    Audit reports low-confidence and opt-in categories too. Reporting
    is not gating: the score and the exit code are unchanged, so a
    judgment call still costs no merge.
    """

    @pytest.mark.integration
    def test_audit_names_the_file_the_line_and_the_category(
        self, tmp_path: Path
    ) -> None:
        """Scenario: a semicolon splice is located, not just counted."""
        doc = tmp_path / "spliced.md"
        doc.write_text("The exporter emits JSON.\nThe system is fast; it scales.\n")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "spliced.md:2" in result.stdout, result.stdout
        assert "semicolon_splice" in result.stdout

    @pytest.mark.integration
    def test_audit_reports_opt_in_categories(self, tmp_path: Path) -> None:
        """Scenario: negative definition is off by default and still audited.

        The operator asked for "doesn't do this" prose to be findable.
        The category exists and stays out of the default sweep because
        contracts are written in negation. Audit mode is where it runs.
        """
        doc = tmp_path / "negative.md"
        doc.write_text("The parser doesn't handle nested blocks.\n")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert "negative_definition" in result.stdout, result.stdout

    @pytest.mark.integration
    def test_audit_exits_zero_on_a_slopped_file(self, tmp_path: Path) -> None:
        """Guard: auditing reports, it does not gate."""
        doc = tmp_path / "slop.md"
        doc.write_text(
            "This comprehensive tapestry cannot be overstated. "
            "It is not uncommon to delve into the intricate.\n"
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, result.stdout

    @pytest.mark.integration
    def test_audit_reports_negation_density(self, tmp_path: Path) -> None:
        """Scenario: over-reliance on the negative is a document property.

        No single sentence is the defect. `check_negation_density` was
        written for this and was called by nothing outside its own
        tests before audit mode existed.
        """
        doc = tmp_path / "negative.md"
        doc.write_text(
            "The daemon does not retry. The probe cannot reach the host. "
            "The parser will not accept a partial write. "
            "The cache is not warmed at boot. "
            "The exporter does not emit CSV. "
            "The hook never gates the write. "
            "The scheduler does not preempt. "
            "The client cannot resume a dropped stream.\n"
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert "negation density" in result.stdout.lower(), result.stdout

    @pytest.mark.integration
    def test_line_numbers_survive_a_code_fence(self, tmp_path: Path) -> None:
        """Guard: blanking code must not shift the lines that follow.

        `_prose_only` substitutes code spans with a single space, so an
        offset computed on the cleaned text points at the wrong line
        once a fence has been collapsed.
        """
        doc = tmp_path / "fenced.md"
        doc.write_text(
            "Intro line.\n\n```python\nx = 1\ny = 2\nz = 3\n```\n\n"
            "The system is fast; it scales.\n"
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert "fenced.md:9" in result.stdout, result.stdout

    @pytest.mark.integration
    def test_audit_accepts_a_file_path_not_only_a_directory(
        self, tmp_path: Path
    ) -> None:
        """Scenario: auditing the files a branch changed.

        The gate scans two fixed directories. Auditing a changed-file
        list means passing files, so a directory-only argument would
        send the operator back to copying files into a scratch tree.
        """
        doc = tmp_path / "one.md"
        doc.write_text("The system is fast; it scales.\n")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(doc)],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert "one.md:1" in result.stdout, result.stdout


class TestInvisibleMatchesAreNamed:
    """Feature: a finding you cannot see is a finding you cannot fix.

    Every other category matches text a reader can read back, so the
    report echoes the match and the reader knows what to delete.
    ``invisible_unicode`` matches characters that render as nothing, so
    echoing them prints a blank where the evidence should be, and the
    line number alone does not say which of the 200 columns is wrong or
    which codepoint it is.

    The escape covers any category: a non-printing character reaching
    the report through some other pattern gets named the same way.
    """

    @pytest.mark.unit
    def test_a_zero_width_match_is_reported_as_its_codepoint(self) -> None:
        """Scenario: the match is unreadable, so the report names it."""
        hits = audit_text("The gate\u200b holds.")
        invisible = [h for h in hits if h.category == "invisible_unicode"]
        assert len(invisible) == 1, hits
        assert invisible[0].match == "<U+200B>", invisible[0].match

    @pytest.mark.unit
    def test_a_bidi_override_is_named_in_the_report(self) -> None:
        """Scenario: Trojan Source is legible in the output that finds it."""
        hits = audit_text("total = 1\u202e // benign")
        assert any(h.match == "<U+202E>" for h in hits), hits

    @pytest.mark.unit
    def test_an_astral_tag_character_is_named(self) -> None:
        """Guard: a codepoint above the BMP formats to five hex digits."""
        hits = audit_text("Prompt\U000e0041 carrier.")
        assert any(h.match == "<U+E0041>" for h in hits), hits

    @pytest.mark.unit
    def test_visible_matches_are_left_alone(self) -> None:
        """Guard: escaping applies to non-printing characters only."""
        hits = audit_text("The system is fast; it scales.")
        spliced = [h for h in hits if h.category == "semicolon_splice"]
        assert spliced, hits
        assert "<U+" not in spliced[0].match, spliced[0].match

    @pytest.mark.integration
    def test_the_command_line_prints_the_codepoint(self, tmp_path: Path) -> None:
        """Scenario: the reader of the report sees the name, not a blank."""
        doc = tmp_path / "invisible.md"
        doc.write_text("A line.\nA zero\u200bwidth space hides here.\n")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "invisible.md:2" in result.stdout, result.stdout
        assert "invisible_unicode" in result.stdout, result.stdout
        assert "<U+200B>" in result.stdout, result.stdout


class TestInvisibleUnicodeIsFoundInsideCode:
    """Feature: code spans are where the bidi attack actually lives.

    Every other category is scored on prose only, and correctly: a slop
    word inside a fence is a symbol, not writing. That reasoning does
    not carry to a character with no glyph. A right-to-left override in
    a fenced block is Trojan Source, source that renders in one order
    and compiles in another, and blanking the fence before scanning
    hides the one place it matters most.

    So this category reads the raw document while the rest read prose.
    The line number still has to be right, which is why the raw text is
    scanned rather than the blanked copy the other rules use.
    """

    @pytest.mark.unit
    def test_a_bidi_override_in_a_fence_is_reported(self) -> None:
        """Scenario: Trojan Source hides in the block the scanner skips."""
        doc = "Prose.\n\n```python\ntotal = 1  # \u202e benign\n```\n"
        hits = [h for h in audit_text(doc) if h.category == "invisible_unicode"]
        assert len(hits) == 1, hits
        assert hits[0].match == "<U+202E>"
        assert hits[0].line == 4, hits[0].line

    @pytest.mark.unit
    def test_a_zero_width_space_in_inline_code_is_reported(self) -> None:
        """Scenario: an identifier that greps as one thing and is another."""
        hits = [
            h
            for h in audit_text("Call `foo\u200bbar` to start.")
            if h.category == "invisible_unicode"
        ]
        assert len(hits) == 1, hits

    @pytest.mark.unit
    def test_other_categories_still_ignore_code(self) -> None:
        """Guard: widening the scan for one category widens only that one."""
        doc = "Prose is fine.\n\n```\nThe system is fast; it scales.\n```\n"
        assert not [h for h in audit_text(doc) if h.category == "semicolon_splice"]


class TestTheGateAlsoReadsInsideCode:
    """Feature: the gate and the audit agree on where the hazard is.

    Audit mode answers "where is it" and the gate answers "does this
    merge". If only the audit reads inside a fence, a bidi override in
    a code block is reported to a person who runs `--audit` by hand and
    passes the check that runs on every commit, which is the wrong way
    round for the one category that carries a security defect.
    """

    @pytest.mark.unit
    def test_a_fenced_bidi_override_is_scored(self) -> None:
        """Scenario: the merge gate counts what the audit found."""
        doc = "Prose here to give the document some words.\n\n"
        doc += "```python\ntotal = 1  # \u202e benign\n```\n"
        found = score_text(doc).findings
        assert [f for f in found if f.category == "invisible_unicode"], found

    @pytest.mark.unit
    def test_a_clean_fence_scores_zero(self) -> None:
        """Guard: ordinary code does not become a finding."""
        doc = "Prose here to give the document some words.\n\n"
        doc += "```python\ntotal = 1  # benign\n```\n"
        found = score_text(doc).findings
        assert not [f for f in found if f.category == "invisible_unicode"], found


class TestNamingSurvivesWhitespaceCollapse:
    """Feature: a character is named before anything can swallow it.

    The match display collapses runs of whitespace so a multi-line hit
    prints on one line. `str.split()` counts U+00A0 and the U+2000
    block as whitespace, so collapsing first turns an exotic space into
    an ASCII one and the name never gets a chance to be printed. The
    current category matches no such character, which is exactly why
    this needs a test: the next category that does would inherit a
    silent hole.
    """

    @pytest.mark.unit
    def test_a_non_breaking_space_is_named_not_collapsed(self) -> None:
        """Guard: naming runs before the collapse, not after."""
        assert _legible("\u00a0") == "<U+00A0>"

    @pytest.mark.unit
    def test_ordinary_text_passes_through(self) -> None:
        """Guard: printable characters are untouched."""
        assert _legible("The system is fast; it scales.") == (
            "The system is fast; it scales."
        )

    @pytest.mark.unit
    def test_a_multi_line_match_still_collapses_to_one_line(self) -> None:
        """Guard: the display stays single-line, which is why it collapses.

        `three_fragment_burst` separates its fragments with `\\s+`, so a
        burst written across three lines is one match carrying two
        newlines. Naming first must not cost the collapse.
        """
        hits = [
            h
            for h in audit_text("Focused.\nAligned.\nMeasurable.\n")
            if h.category == "three_fragment_burst"
        ]
        assert hits, "expected a three-fragment burst"
        assert "\n" not in hits[0].match, repr(hits[0].match)
        assert hits[0].match == "Focused. Aligned. Measurable.", hits[0].match


class TestAMissingPathIsLoud:
    """Feature: a path that does not exist fails instead of passing.

    Found by dogfooding this on zsh, which does not word-split an
    unquoted parameter. `--audit $FILES` arrived as one argument holding
    thirteen newline-separated paths, matched no file, and printed
    "audited 0 files, 0 findings": a clean bill of health for a list
    nothing had read. A reporting tool that answers "nothing here" when
    it means "I found no input" is worse than one that crashes.
    """

    @pytest.mark.integration
    def test_a_nonexistent_root_exits_nonzero(self, tmp_path: Path) -> None:
        """Scenario: a typo'd path is an error, not an all-clear."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(tmp_path / "absent.md")],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert result.returncode != 0
        assert "absent.md" in result.stdout + result.stderr

    @pytest.mark.integration
    def test_a_newline_joined_argument_is_split(self, tmp_path: Path) -> None:
        """Scenario: a shell handed the whole list as one argument.

        Splitting it is the difference between reading every file and
        silently reading none.
        """
        first = tmp_path / "a.md"
        second = tmp_path / "b.md"
        first.write_text("The system is fast; it scales.\n")
        second.write_text("The result is clear, not clever.\n")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", f"{first}\n{second}"],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "a.md:1" in result.stdout
        assert "b.md:1" in result.stdout

    @pytest.mark.integration
    def test_the_gate_also_rejects_a_missing_root(self, tmp_path: Path) -> None:
        """Guard: the same trap would silently pass CI."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(tmp_path / "no-such-dir")],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert result.returncode != 0


class TestGateIsUnchangedByAuditMode:
    """Guard: adding a reporting mode must not move the merge bar."""

    @pytest.mark.unit
    def test_opt_in_categories_still_score_nothing(self) -> None:
        """Scenario: negative definition is auditable and never gates."""
        clean = "The exporter emits JSON. " * 10
        negative = clean + "The parser doesn't handle nested blocks."
        assert score_text(negative).score == score_text(clean).score


def _run(args: list, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )


class TestExcludePatterns:
    """Feature: a document that defines a pattern is not gated on it.

    `config-file.md` documents `exclude_patterns` and the scorer ignored
    it, so the gate could only ever run on `docs` and `book/src`: any
    wider root pulled in the slop-detector modules, the rule files and
    the hookify catalog, each of which quotes every tell it describes.
    The exclusion applies to the gate and the ratchet. Audit mode still
    scans everything, because it exits 0 and has nothing to protect.
    """

    DEFINITION_DOC = "plugins/scribe/skills/slop-detector/SKILL.md"

    @pytest.mark.unit
    def test_exclude_patterns_are_read_from_the_config(self, tmp_path: Path) -> None:
        config = tmp_path / ".slop-config.yaml"
        config.write_text("exclude_patterns:\n  - 'plugins/*/agents/*'\n")
        assert load_exclude_patterns(config) == ("plugins/*/agents/*",)

    @pytest.mark.unit
    def test_a_missing_config_excludes_nothing(self, tmp_path: Path) -> None:
        assert load_exclude_patterns(tmp_path / "absent.yaml") == ()

    @pytest.mark.integration
    def test_the_gate_skips_a_pattern_defining_document(self) -> None:
        """Scenario: the repository config exempts its own definitions."""
        result = _run(["--threshold", "3.0", self.DEFINITION_DOC])
        assert result.returncode == 0, result.stdout
        assert "excluded 1" in result.stdout

    @pytest.mark.integration
    def test_audit_still_reads_an_excluded_document(self) -> None:
        """Guard: "where is it" is answered for every file asked about."""
        result = _run(["--audit", self.DEFINITION_DOC])
        assert result.returncode == 0
        assert f"{self.DEFINITION_DOC}:" in result.stdout


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        env={
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t",
            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
            "HOME": str(repo),
        },
    )


SLOP = (
    "This comprehensive tapestry cannot be overstated. "
    "It is not uncommon to delve into the intricate.\n"
)
CLEAN = "The cache stores one entry per transcript path.\n"


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    return tmp_path


class TestRatchet:
    """Feature: a commit may not make a file worse than it already is.

    About twenty files outside the definition documents already sit over
    the threshold. A whole-file gate on every touched markdown file would
    block an unrelated one-line edit to any of them until someone cleaned
    the whole file, so the commit-time and PR-time gates compare against
    the committed version instead: fail only when the score is over the
    threshold and higher than it was.
    """

    @pytest.mark.integration
    def test_fails_when_slop_is_added_to_a_clean_file(self, repo: Path) -> None:
        doc = repo / "doc.md"
        doc.write_text(CLEAN * 8)
        _git(repo, "add", "doc.md")
        _git(repo, "commit", "-qm", "clean")
        doc.write_text(CLEAN * 8 + SLOP * 4)
        result = _run(["--ratchet", "HEAD", "doc.md"], cwd=repo)
        assert result.returncode == 1, result.stdout
        assert "doc.md" in result.stdout

    @pytest.mark.integration
    def test_passes_when_a_slopped_file_gets_no_worse(self, repo: Path) -> None:
        """Scenario: the one-line edit to a legacy file goes through."""
        doc = repo / "doc.md"
        doc.write_text(SLOP * 4)
        _git(repo, "add", "doc.md")
        _git(repo, "commit", "-qm", "legacy")
        doc.write_text(SLOP * 4 + CLEAN)
        result = _run(["--ratchet", "HEAD", "doc.md"], cwd=repo)
        assert result.returncode == 0, result.stdout

    @pytest.mark.integration
    def test_a_new_file_is_held_to_the_threshold(self, repo: Path) -> None:
        """Scenario: nothing to ratchet against, so the plain gate applies."""
        (repo / "new.md").write_text(SLOP * 4)
        result = _run(["--ratchet", "HEAD", "new.md"], cwd=repo)
        assert result.returncode == 1, result.stdout
        (repo / "fresh.md").write_text(CLEAN * 8)
        result = _run(["--ratchet", "HEAD", "fresh.md"], cwd=repo)
        assert result.returncode == 0, result.stdout

    @pytest.mark.integration
    def test_the_failure_names_both_scores(self, repo: Path) -> None:
        """Scenario: the author sees what the file was and what it became."""
        doc = repo / "doc.md"
        doc.write_text(CLEAN * 8)
        _git(repo, "add", "doc.md")
        _git(repo, "commit", "-qm", "clean")
        doc.write_text(CLEAN * 8 + SLOP * 4)
        result = _run(["--ratchet", "HEAD", "doc.md"], cwd=repo)
        assert "was 0.00" in result.stdout
        assert "--audit" in result.stdout


class TestWriteTimeHookStaysInsideTheYaml:
    """Feature: the hookify rule warns only on what the audit also reports.

    `warn-slop-in-markdown` inlines its regex because hooks run on a
    Python with no pyyaml. Nothing else keeps that copy aligned with
    `en.yaml`, so a sample the hook flags and the audit does not would
    send an author to a command that finds nothing.
    """

    HOOK_RULE = (
        REPO_ROOT
        / "plugins/hookify/skills/rule-catalog/rules/documentation"
        / "warn-slop-in-markdown.md"
    )
    SAMPLES = [
        "The cache is warm — the probe is not.",
        "The cache is warm -- the probe is not.",
        "The hooks + skills load together.",
        "The system is fast; it scales.",
        "The result is clear, not clever.",
        "It's a tool, not a toy.",
        "The third sends your code, not just a status check.",
        "The value of tests cannot be overstated.",
        "It goes without saying that the hook runs first.",
        "Needless to say, the gate passes.",
        "It is not uncommon for the probe to stall.",
        "The parser never fails to surprise.",
        "The flag is named “verbose” here.",
    ]

    def _hook_pattern(self) -> str:
        frontmatter = self.HOOK_RULE.read_text().split("---")[1]
        conditions = yaml.safe_load(frontmatter)["conditions"]
        return next(c["pattern"] for c in conditions if c["field"] == "new_text")

    @pytest.mark.unit
    def test_every_hook_sample_is_also_an_audit_finding(self) -> None:
        pattern = self._hook_pattern()
        for sample in self.SAMPLES:
            assert re.search(pattern, sample, re.MULTILINE), f"hook misses: {sample!r}"
            assert audit_text(sample), f"audit misses what the hook flags: {sample!r}"


class TestPythonCommentsAreScanned:
    """The scorer reaches a comment and a docstring, and only those.

    Every Tier 5 category this repository wrote reached markdown only,
    because the collector globbed ``*.md``. Half of what Anthropic
    issue #65961 reports lives in a comment, so the categories were
    written and then never pointed at the text that carries the
    behavior.

    The projection blanks every non-prose line rather than extracting
    the prose into a new string. That keeps the line count, so a
    finding still names the line a reader must open.
    """

    @pytest.mark.unit
    def test_a_docstring_finding_reports_its_real_line(self, tmp_path: Path) -> None:
        """Scenario: A residue docstring is located, not merely counted."""
        module = tmp_path / "sample.py"
        module.write_text(
            '"""Parse a record.\n\nThis used to be an int field.\n"""\n',
            encoding="utf-8",
        )
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(module)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "temporal_residue" in completed.stdout
        assert f"{module}:3" in completed.stdout

    @pytest.mark.unit
    def test_code_outside_a_comment_is_not_scored(self, tmp_path: Path) -> None:
        """Guard: an identifier is not prose.

        A variable named ``robust_seamless_handler`` is a name the
        author chose. Scoring it would report a slop finding against
        code the scanner was never asked to review.
        """
        module = tmp_path / "code.py"
        module.write_text(
            "robust_seamless_handler = None\ncomprehensive = ['actionable']\n",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(module)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "0 findings" in completed.stdout

    @pytest.mark.unit
    def test_a_doctest_line_is_not_scored(self, tmp_path: Path) -> None:
        """Guard: ``>>>`` is executable example code, not prose."""
        module = tmp_path / "doctest_sample.py"
        module.write_text(
            '"""Check a record.\n'
            "\n"
            '>>> parse("x") is not just a stub, but a record\n'
            "True\n"
            '"""\n',
            encoding="utf-8",
        )
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(module)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "0 findings" in completed.stdout

    @pytest.mark.unit
    def test_a_directory_sweep_skips_python_without_the_flag(
        self, tmp_path: Path
    ) -> None:
        """Scenario: The markdown gate CI runs does not change shape.

        A tree of docstrings turned on at once would fail the existing
        threshold on text nobody was asked to review, so a directory
        root stays markdown until ``--python`` says otherwise.
        """
        (tmp_path / "mod.py").write_text(
            "# This used to be an int field.\n", encoding="utf-8"
        )
        without = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "temporal_residue" not in without.stdout

        with_flag = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", "--python", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "temporal_residue" in with_flag.stdout

    @pytest.mark.unit
    def test_the_contrastive_comment_from_issue_65961_is_caught(
        self, tmp_path: Path
    ) -> None:
        """Scenario: The complaint that prompted this work is detected.

        "if commenting on a proto string field that is replacing an int
        field, do not comment that 'this is not an int field'". The
        category that catches it, ``negative_parallelism``, already
        existed at high confidence and default-on. It had simply never
        been pointed at a comment.
        """
        module = tmp_path / "proto.py"
        module.write_text(
            '# This is a string field, not an int field.\ncontribution_id = ""\n',
            encoding="utf-8",
        )
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", str(module)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "negative_parallelism" in completed.stdout


class TestPythonWordFloor:
    """A short docstring's score measures its denominator.

    The score is weighted hits per 100 words. A tier 1 hit is worth 3,
    so under roughly 100 words a single finding can put a file over a
    3.0 threshold on its own. Measured over six plugins, a module with
    14 words of docstring and one finding scored 21.43 while a
    1029-word ADR carrying twelve scored 1.55.

    The floor gates only. `--audit` still reports every finding,
    because a finding is true however much prose surrounds it.
    """

    @pytest.mark.unit
    def test_a_short_python_file_is_floored_out_of_the_gate(
        self, tmp_path: Path
    ) -> None:
        """Scenario: One hit in a one-line docstring does not gate."""
        module = tmp_path / "short.py"
        module.write_text('"""A comprehensive helper."""\n', encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--threshold",
                "3.0",
                "--python",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "under the 150-word floor, not scored" in completed.stdout
        assert "short.py" not in completed.stdout
        assert completed.returncode == 0

    @pytest.mark.unit
    def test_a_long_python_file_still_gates(self, tmp_path: Path) -> None:
        """Scenario: Past the floor, the score means what it always did."""
        module = tmp_path / "long.py"
        filler = " ".join(["the parser reads a record and returns it"] * 30)
        module.write_text(
            '"""' + filler + " This is a comprehensive and robust seamless"
            " comprehensive robust comprehensive solution." + '"""\n',
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--threshold",
                "3.0",
                "--python",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "long.py" in completed.stdout
        assert completed.returncode == 1

    @pytest.mark.unit
    def test_a_short_markdown_file_is_not_floored(self, tmp_path: Path) -> None:
        """Guard: the floor is Python only.

        A one-line module docstring is ordinary. A 14-word README is a
        finding in itself, so markdown keeps the behavior it had and
        the `docs book/src` gate is untouched.
        """
        doc = tmp_path / "short.md"
        doc.write_text(
            "A comprehensive robust seamless actionable solution.\n",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--threshold", "3.0", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "short.md" in completed.stdout
        assert "word floor" not in completed.stdout
        assert completed.returncode == 1

    @pytest.mark.unit
    def test_audit_reports_a_finding_below_the_floor(self, tmp_path: Path) -> None:
        """Guard: the floor gates, it does not hide.

        A finding is true however little prose surrounds it. Only the
        ratio needs a denominator worth dividing by.
        """
        module = tmp_path / "tiny.py"
        module.write_text('"""A comprehensive helper."""\n', encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--audit", "--python", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "comprehensive" in completed.stdout
        assert "1 findings" in completed.stdout


class TestDoubleBacktickCodeIsStripped:
    """RST marks code with two backticks and the scorer must see that.

    The single-backtick alternative consumes an opening pair as an
    empty span, leaving the code between them bare. Docstrings across
    this repository use the RST convention, so a formula reached the
    scorer as prose and its plus sign scored as a conjunction.
    """

    @pytest.mark.unit
    def test_a_formula_in_double_backticks_does_not_score(self) -> None:
        """Scenario: Arithmetic marked as code is code."""
        text = "The ratio ``(n_i - n_j) / (n_i + n_j + n_k)`` bounds it."
        result = score_text(text, allowlist=load_allowlist())
        categories = {finding.category for finding in result.findings}
        assert "plus_sign_conjunction" not in categories

    @pytest.mark.unit
    def test_a_plus_conjunction_outside_code_still_scores(self) -> None:
        """Guard: the fix strips code, it does not disable the category."""
        text = "ADR + architecture documentation analysis for the review."
        result = score_text(text, allowlist=load_allowlist())
        categories = {finding.category for finding in result.findings}
        assert "plus_sign_conjunction" in categories

    @pytest.mark.unit
    def test_single_backtick_code_is_still_stripped(self) -> None:
        """Guard: the added alternative did not displace the old one."""
        text = "Call `a + b` when the counter advances past the mark."
        result = score_text(text, allowlist=load_allowlist())
        categories = {finding.category for finding in result.findings}
        assert "plus_sign_conjunction" not in categories


class TestDoubleDashReachesTheGate:
    """The spaced double dash is scored, not merely audited.

    `.claude/rules/slop-scan-for-docs.md` rule 2a calls it a
    high-confidence tell and an always-fix. It was registered in
    `_audit_rules()` only, and `.github/workflows/slop-check.yml`
    invokes gate and ratchet mode and never `--audit`, so the category
    had no enforcement path anywhere in the pipeline.
    """

    @pytest.mark.unit
    def test_the_gate_rules_carry_double_dash(self) -> None:
        """Scenario: a scored run can see the category at all."""
        text = "The gate runs -- and the audit runs too."
        result = score_text(text, allowlist=load_allowlist())
        categories = {finding.category for finding in result.findings}
        assert "double_dash" in categories

    @pytest.mark.unit
    def test_a_table_cell_separator_is_not_flagged(self) -> None:
        """Guard: `| -- |` is markdown table syntax, not punctuation."""
        text = "| col | col |\n| -- | -- |\n| a | b |\n"
        result = score_text(text, allowlist=load_allowlist())
        categories = {finding.category for finding in result.findings}
        assert "double_dash" not in categories

    @pytest.mark.unit
    def test_a_shell_end_of_options_marker_inside_code_is_not_flagged(
        self,
    ) -> None:
        """Guard: `--` is a real shell separator and belongs in code."""
        text = "Run `git log -- path` to scope it.\n"
        result = score_text(text, allowlist=load_allowlist())
        categories = {finding.category for finding in result.findings}
        assert "double_dash" not in categories
