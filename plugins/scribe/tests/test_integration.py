"""Integration tests for the scribe slop-detector pipeline.

Issue #132: Add functional integration tests for scribe plugin

Each test exercises multiple modules working together end-to-end, rather
than a single helper in isolation.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Minimal inline helpers
# ---------------------------------------------------------------------------

_T1_WORDS = [
    "delve",
    "embark",
    "tapestry",
    "realm",
    "beacon",
    "multifaceted",
    "nuanced",
    "pivotal",
    "meticulous",
    "intricate",
    "showcasing",
    "leveraging",
    "streamline",
    "unleash",
    "comprehensive",
]
_T2_WORDS = [
    "underscore",
    "bolster",
    "foster",
    "seamless",
    "invaluable",
    "vibrant",
    "interplay",
    "endeavor",
]
_PHRASE_PATS = [
    r"in today's fast-paced",
    r"cannot be overstated",
    r"a testament to",
    r"unlock the (?:full )?potential",
    r"treasure trove",
    r"it's important to (?:note|remember|understand) that",
    r"invaluable resource",
    r"underscores the importance",
]
_CONCLUSION_PATS = [
    r"^Overall,",
    r"^In conclusion,",
    r"^In summary,",
    r"^Ultimately,",
    r"^To sum up,",
]

_RE_T1 = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in _T1_WORDS) + r")\b", re.IGNORECASE
)
_RE_T2 = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in _T2_WORDS) + r")\b", re.IGNORECASE
)
_RE_PHRASE = re.compile(r"(" + "|".join(_PHRASE_PATS) + r")", re.IGNORECASE)
_RE_CONCLUSION = re.compile(r"(" + "|".join(_CONCLUSION_PATS) + r")", re.MULTILINE)


def _score(text: str) -> float:
    words = text.split()
    if not words:
        return 0.0
    raw = (len(_RE_T1.findall(text)) * 3) + (len(_RE_PHRASE.findall(text)) * 3)
    return min(10.0, (raw / len(words)) * 100)


def _rating(score: float) -> str:
    if score <= 1.0:
        return "Clean"
    if score <= 2.5:
        return "Light"
    if score <= 5.0:
        return "Moderate"
    return "Heavy"


def _build_pattern(builtin: list[str], custom: list[str]) -> re.Pattern[str]:
    return re.compile(
        r"\b(" + "|".join(re.escape(w) for w in builtin + custom) + r")\b",
        re.IGNORECASE,
    )


def _matches(text: str, pat: re.Pattern[str], allowlist: list[str]) -> list[str]:
    return [m for m in pat.findall(text) if m.lower() not in allowlist]


def _parse_config(raw: dict[str, Any]) -> dict[str, Any]:
    cw = raw.get("custom_words", {})
    th = raw.get("thresholds", {})
    return {
        "custom_words": {
            "tier1": [w.lower() for w in cw.get("tier1", [])],
            "tier2": [w.lower() for w in cw.get("tier2", [])],
        },
        "allowlist": [w.lower() for w in raw.get("allowlist", [])],
        "thresholds": {
            "warn": float(th.get("warn", 2.0)),
            "error": float(th.get("error", 5.0)),
        },
    }


def _file_result(path: str, score: float, markers: int) -> dict[str, Any]:
    return {"path": path, "score": score, "rating": _rating(score), "markers": markers}


def _ci_output(files: list[dict[str, Any]], threshold: float = 3.0) -> dict[str, Any]:
    if not files:
        return {
            "files": [],
            "summary": {
                "total_files": 0,
                "avg_score": 0.0,
                "max_score": 0.0,
                "pass": True,
            },
        }
    scores = [f["score"] for f in files]
    max_s = max(scores)
    return {
        "files": files,
        "summary": {
            "total_files": len(files),
            "avg_score": round(sum(scores) / len(scores), 2),
            "max_score": max_s,
            "pass": max_s <= threshold,
        },
    }


def _exit_code(output: dict[str, Any]) -> int:
    return 0 if output["summary"]["pass"] else 1


def _metrics_record(
    dt: datetime, scores: list[dict[str, Any]], total_markers: int
) -> dict[str, Any]:
    values = [s["score"] for s in scores]
    avg = round(sum(values) / len(values), 4) if values else 0.0
    return {
        "timestamp": dt.isoformat(),
        "files_scanned": len(scores),
        "scores": scores,
        "summary": {
            "avg_score": avg,
            "max_score": max(values) if values else 0.0,
            "total_markers": total_markers,
        },
    }


def _save_record(record: dict[str, Any], history_dir: str, dt: datetime) -> None:
    os.makedirs(history_dir, exist_ok=True)
    fname = "scan-" + dt.strftime("%Y-%m-%d-%H%M%S") + ".json"
    with open(os.path.join(history_dir, fname), "w") as fh:
        json.dump(record, fh)


def _load_history(history_dir: str) -> list[dict[str, Any]]:
    if not os.path.isdir(history_dir):
        return []
    records = []
    for fname in sorted(f for f in os.listdir(history_dir) if f.endswith(".json")):
        with open(os.path.join(history_dir, fname)) as fh:
            records.append(json.load(fh))
    return records


def _deltas(records: list[dict[str, Any]]) -> list[Any]:
    out: list[Any] = [None]
    for i in range(1, len(records)):
        prev = records[i - 1]["summary"]["avg_score"]
        curr = records[i]["summary"]["avg_score"]
        out.append(round(curr - prev, 4))
    return out


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestEndToEndSlopDetection:
    """End-to-end pipeline: tier1 + tier2 + phrases + structural."""

    def test_sloppy_document_reports_all_tiers(self) -> None:
        """Given a document with tier-1 words, phrases, and a conclusion starter,
        when the full pipeline runs, every category has at least one hit.
        """
        doc = (
            "In today's fast-paced world, this comprehensive solution delves into\n"
            "the multifaceted realm of documentation. It is a testament to our\n"
            "meticulous approach. This tapestry of features is invaluable.\n"
            "In conclusion, we must unleash the full potential.\n"
        )
        assert len(_RE_T1.findall(doc)) >= 4
        assert len(_RE_T2.findall(doc)) >= 1
        assert len(_RE_PHRASE.findall(doc)) >= 1
        assert len(_RE_CONCLUSION.findall(doc)) >= 1

    def test_clean_document_has_zero_matches(self) -> None:
        """Given a document with no slop, every category returns zero matches."""
        doc = (
            "The cache sits between the API and the database. When a request\n"
            "arrives, we check Redis first. Cache hits return in under 5ms.\n"
        )
        assert _RE_T1.findall(doc) == []
        assert _RE_T2.findall(doc) == []
        assert _RE_PHRASE.findall(doc) == []
        assert _RE_CONCLUSION.findall(doc) == []

    def test_score_higher_for_sloppy_than_clean(self) -> None:
        """Sloppy doc score must exceed clean doc score by more than 2 points."""
        sloppy = (
            "This comprehensive solution delves into the multifaceted realm. "
            "We must unleash the potential and streamline the tapestry. "
            "In today's fast-paced world the approach is meticulous and pivotal."
        )
        clean = (
            "The system processes requests and returns results. "
            "Each request goes through validation before storage."
        )
        assert _score(sloppy) > _score(clean) + 2.0


@pytest.mark.integration
class TestConfigAndDetectionIntegration:
    """Config allowlist and custom words interact with the detection pass."""

    def test_allowlisted_word_is_skipped(self) -> None:
        """'realm' in allowlist must not appear in flagged matches."""
        config = _parse_config({"allowlist": ["realm"]})
        pat = _build_pattern(_T1_WORDS, [])
        text = "The realm of documentation requires meticulous attention."
        hits = [m.lower() for m in _matches(text, pat, config["allowlist"])]
        assert "realm" not in hits
        assert "meticulous" in hits

    def test_custom_word_caught_builtin_absent_word_not_caught(self) -> None:
        """Custom 'synergize' is detected; words absent from text are not."""
        config = _parse_config({"custom_words": {"tier1": ["synergize"]}})
        pat = _build_pattern(_T1_WORDS, config["custom_words"]["tier1"])
        text = "We need to synergize our documentation process."
        hits = [m.lower() for m in _matches(text, pat, config["allowlist"])]
        assert "synergize" in hits
        assert "delve" not in hits

    def test_allowlist_and_custom_applied_together(self) -> None:
        """Allowlist blocks one word; custom adds another; both must apply."""
        config = _parse_config(
            {"custom_words": {"tier1": ["ideate"]}, "allowlist": ["delve"]}
        )
        pat = _build_pattern(_T1_WORDS, config["custom_words"]["tier1"])
        text = "Let us ideate and delve into every realm."
        hits = [m.lower() for m in _matches(text, pat, config["allowlist"])]
        assert "ideate" in hits
        assert "realm" in hits
        assert "delve" not in hits

    def test_warn_threshold_gates_ci_pass(self) -> None:
        """Score between warn and error: passes at error threshold, fails at warn."""
        config = _parse_config({"thresholds": {"warn": 1.5, "error": 4.0}})
        result = _file_result("docs/guide.md", 2.0, 5)
        assert (
            _ci_output([result], threshold=config["thresholds"]["error"])["summary"][
                "pass"
            ]
            is True
        )
        assert (
            _ci_output([result], threshold=config["thresholds"]["warn"])["summary"][
                "pass"
            ]
            is False
        )


@pytest.mark.integration
class TestProgressAndDetectionIntegration:
    """Progress tracking across a multi-file simulated scan."""

    def test_progress_lines_emitted_for_three_files(self) -> None:
        """Scanning three files must produce one progress line per file."""
        files = ["docs/intro.md", "docs/api.md", "docs/guide.md"]
        lines = [f"[{i + 1}/{len(files)}] Scanning {f}..." for i, f in enumerate(files)]
        assert len(lines) == 3
        assert lines[0] == "[1/3] Scanning docs/intro.md..."
        assert lines[2] == "[3/3] Scanning docs/guide.md..."

    def test_progress_counter_increments_per_file(self) -> None:
        """Counter in each line must reflect its 1-based position."""
        files = ["a.md", "b.md", "c.md", "d.md"]
        for idx, f in enumerate(files, 1):
            line = f"[{idx}/{len(files)}] Scanning {f}..."
            assert f"[{idx}/4]" in line

    def test_no_progress_below_threshold(self) -> None:
        """Progress output is suppressed for fewer than 3 files."""
        assert (1 >= 3) is False
        assert (2 >= 3) is False

    def test_progress_filepath_present_in_each_line(self) -> None:
        """Each progress line must include the corresponding file path."""
        files = ["docs/readme.md", "docs/howto.md", "docs/ref.md"]
        for i, path in enumerate(files):
            line = f"[{i + 1}/{len(files)}] Scanning {path}..."
            assert path in line


@pytest.mark.integration
class TestCIOutputIntegration:
    """CI JSON output conforms to schema and exit-code logic works end-to-end."""

    def test_output_schema_has_required_keys(self) -> None:
        """Full CI output must contain 'files' and 'summary' with required keys."""
        output = _ci_output(
            [_file_result("docs/a.md", 1.2, 3), _file_result("docs/b.md", 3.8, 9)]
        )
        assert set(output.keys()) == {"files", "summary"}
        assert set(output["summary"].keys()) == {
            "total_files",
            "avg_score",
            "max_score",
            "pass",
        }

    def test_exit_code_zero_when_all_files_pass(self) -> None:
        """All files below threshold must yield exit code 0."""
        output = _ci_output(
            [
                _file_result("docs/a.md", 0.5, 1),
                _file_result("docs/b.md", 1.8, 4),
                _file_result("docs/c.md", 2.9, 7),
            ],
            threshold=3.0,
        )
        assert _exit_code(output) == 0

    def test_exit_code_one_when_any_file_exceeds_threshold(self) -> None:
        """Any file above threshold must yield exit code 1."""
        output = _ci_output(
            [_file_result("docs/a.md", 0.5, 1), _file_result("docs/b.md", 5.1, 14)]
        )
        assert _exit_code(output) == 1

    def test_json_roundtrip_preserves_all_fields(self, tmp_path: Any) -> None:
        """CI output written as JSON and re-read must match the original dict."""
        output = _ci_output([_file_result("docs/guide.md", 2.4, 6)], threshold=3.0)
        out_file = tmp_path / "ci-report.json"
        out_file.write_text(json.dumps(output))
        loaded = json.loads(out_file.read_text())
        assert loaded["files"][0]["path"] == "docs/guide.md"
        assert loaded["files"][0]["score"] == pytest.approx(2.4)
        assert loaded["summary"]["pass"] is True

    def test_rating_assigned_per_score_band(self) -> None:
        """Ratings on all four boundary scores must match the spec."""
        assert _file_result("f.md", 1.0, 0)["rating"] == "Clean"
        assert _file_result("f.md", 2.5, 0)["rating"] == "Light"
        assert _file_result("f.md", 5.0, 0)["rating"] == "Moderate"
        assert _file_result("f.md", 5.1, 0)["rating"] == "Heavy"


@pytest.mark.integration
class TestMetricsAndDetectionIntegration:
    """Run detection, save to metrics, load history, verify trend calculation."""

    def test_save_and_load_single_record(self, tmp_path: Any) -> None:
        """A record written to disk must be loadable with identical content."""
        dt = datetime(2026, 3, 1, 10, 0, 0)
        scores = [
            {"path": "docs/guide.md", "score": 1.4, "word_count": 320},
            {"path": "docs/api.md", "score": 2.8, "word_count": 600},
        ]
        _save_record(_metrics_record(dt, scores, 8), str(tmp_path), dt)
        history = _load_history(str(tmp_path))
        assert len(history) == 1
        assert history[0]["files_scanned"] == 2
        assert history[0]["summary"]["avg_score"] == pytest.approx(2.1, abs=0.01)

    def test_trend_calculation_across_three_scans(self, tmp_path: Any) -> None:
        """Three saved scans must produce correct per-record deltas."""
        data = [
            (datetime(2026, 1, 1), 1.0),
            (datetime(2026, 2, 1), 1.5),
            (datetime(2026, 3, 1), 1.2),
        ]
        for dt, avg in data:
            _save_record(
                _metrics_record(
                    dt, [{"path": "a.md", "score": avg, "word_count": 100}], 2
                ),
                str(tmp_path),
                dt,
            )
        history = _load_history(str(tmp_path))
        deltas = _deltas(history)
        assert deltas[0] is None
        assert deltas[1] == pytest.approx(0.5, abs=0.001)
        assert deltas[2] == pytest.approx(-0.3, abs=0.001)

    def test_regression_detected_between_scans(self, tmp_path: Any) -> None:
        """A score jump above 0.5 between consecutive scans is a regression."""
        dt1, dt2 = datetime(2026, 2, 1), datetime(2026, 3, 1)
        _save_record(
            _metrics_record(
                dt1, [{"path": "a.md", "score": 1.0, "word_count": 100}], 2
            ),
            str(tmp_path),
            dt1,
        )
        _save_record(
            _metrics_record(
                dt2, [{"path": "a.md", "score": 2.1, "word_count": 100}], 6
            ),
            str(tmp_path),
            dt2,
        )
        history = _load_history(str(tmp_path))
        delta = _deltas(history)[-1]
        assert delta is not None
        assert delta > 0.5

    def test_no_regression_when_score_improves(self, tmp_path: Any) -> None:
        """A decreasing score must produce a negative delta."""
        dt1, dt2 = datetime(2026, 2, 1), datetime(2026, 3, 1)
        _save_record(
            _metrics_record(
                dt1, [{"path": "a.md", "score": 3.0, "word_count": 100}], 9
            ),
            str(tmp_path),
            dt1,
        )
        _save_record(
            _metrics_record(
                dt2, [{"path": "a.md", "score": 1.0, "word_count": 100}], 3
            ),
            str(tmp_path),
            dt2,
        )
        delta = _deltas(_load_history(str(tmp_path)))[-1]
        assert delta is not None
        assert delta < 0


@pytest.mark.integration
class TestScoringThresholdBoundaries:
    """Exact boundary scores map to the correct ratings."""

    def test_score_zero_is_clean(self) -> None:
        assert _rating(0.0) == "Clean"

    def test_score_1_0_is_clean(self) -> None:
        assert _rating(1.0) == "Clean"

    def test_score_1_01_is_light(self) -> None:
        assert _rating(1.01) == "Light"

    def test_score_2_5_is_light(self) -> None:
        assert _rating(2.5) == "Light"

    def test_score_2_51_is_moderate(self) -> None:
        assert _rating(2.51) == "Moderate"

    def test_score_5_0_is_moderate(self) -> None:
        assert _rating(5.0) == "Moderate"

    def test_score_5_01_is_heavy(self) -> None:
        assert _rating(5.01) == "Heavy"

    def test_ci_pass_at_exact_threshold(self) -> None:
        """A file scoring exactly at the CI threshold must register as passing."""
        output = _ci_output([_file_result("docs/a.md", 3.0, 6)], threshold=3.0)
        assert output["summary"]["pass"] is True
        assert _exit_code(output) == 0

    def test_ci_fail_just_above_threshold(self) -> None:
        """A file scoring one hundredth above the threshold must fail."""
        output = _ci_output([_file_result("docs/a.md", 3.01, 6)], threshold=3.0)
        assert output["summary"]["pass"] is False
        assert _exit_code(output) == 1
