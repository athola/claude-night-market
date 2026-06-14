"""Tests for CCR (reversible compression) in the conserve plugin.

Ported from chopratejas/headroom's CCR idea: when a single tool output is
large, archive the original to an external cache keyed by a content-addressed
handle, surface a compact digest + retrieval command, and let a later turn
fetch the original (or a slice) on demand via context_retrieve.py.

These tests are written before the implementation (TDD RED phase). They drive
the public API of two modules:

- hooks/tool_output_summarizer.py: get_ccr_threshold, should_archive,
  archive_large_output, build_digest, extract_tool_response_text, main
- scripts/context_retrieve.py: resolve_handle, slice_content, grep_content,
  main
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import uuid
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = PLUGIN_ROOT / "hooks"
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"

# Named constants (avoid PLR2004 magic values in assertions).
DEFAULT_THRESHOLD = 25_000
SMALL_THRESHOLD = 100
HANDLE_HEX_LEN = 12
HEAD_LINES = 3
TAIL_LINES = 2


def _load_module(module_path: Path):
    """Load a module by path via importlib (conftest pattern).

    A unique module name is used so repeated loads stay isolated.
    """
    unique = f"{module_path.stem}_{uuid.uuid4().hex[:8]}"
    spec = importlib.util.spec_from_file_location(unique, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def summarizer():
    """Load the tool_output_summarizer hook module."""
    return _load_module(HOOKS_DIR / "tool_output_summarizer.py")


@pytest.fixture
def retriever():
    """Load the context_retrieve CLI module (lives in scripts/)."""
    return _load_module(SCRIPTS_DIR / "context_retrieve.py")


# ---------------------------------------------------------------------------
# Threshold + archive decision
# ---------------------------------------------------------------------------


def test_get_ccr_threshold_default(summarizer, monkeypatch):
    monkeypatch.delenv("CONSERVE_CCR_THRESHOLD", raising=False)
    assert summarizer.get_ccr_threshold() == DEFAULT_THRESHOLD


def test_get_ccr_threshold_env_override(summarizer, monkeypatch):
    monkeypatch.setenv("CONSERVE_CCR_THRESHOLD", str(SMALL_THRESHOLD))
    assert summarizer.get_ccr_threshold() == SMALL_THRESHOLD


def test_get_ccr_threshold_invalid_env_falls_back(summarizer, monkeypatch):
    monkeypatch.setenv("CONSERVE_CCR_THRESHOLD", "not-a-number")
    assert summarizer.get_ccr_threshold() == DEFAULT_THRESHOLD


def test_should_archive_below_threshold_is_false(summarizer):
    assert summarizer.should_archive("x" * 50, threshold=SMALL_THRESHOLD) is False


def test_should_archive_at_threshold_is_true(summarizer):
    assert summarizer.should_archive("x" * SMALL_THRESHOLD, threshold=SMALL_THRESHOLD)


# ---------------------------------------------------------------------------
# Archiving (content-addressed, reversible)
# ---------------------------------------------------------------------------


def test_archive_writes_file_and_returns_handle(summarizer, tmp_path):
    text = "FATAL: boom\n" + ("line\n" * 1000)
    handle = summarizer.archive_large_output(text, archive_dir=tmp_path)

    assert handle.startswith("ccr-")
    assert len(handle) == len("ccr-") + HANDLE_HEX_LEN
    archived = tmp_path / f"{handle}.txt"
    assert archived.exists()
    assert archived.read_text(encoding="utf-8") == text


def test_archive_handle_is_stable_for_same_content(summarizer, tmp_path):
    text = "same content " * 500
    h1 = summarizer.archive_large_output(text, archive_dir=tmp_path)
    h2 = summarizer.archive_large_output(text, archive_dir=tmp_path)
    assert h1 == h2


def test_archive_handle_differs_for_different_content(summarizer, tmp_path):
    h1 = summarizer.archive_large_output("alpha " * 500, archive_dir=tmp_path)
    h2 = summarizer.archive_large_output("beta " * 500, archive_dir=tmp_path)
    assert h1 != h2


# ---------------------------------------------------------------------------
# Digest
# ---------------------------------------------------------------------------


def test_build_digest_contains_head_tail_counts_and_retrieval(summarizer):
    lines = [f"line-{i}" for i in range(100)]
    text = "\n".join(lines)
    handle = "ccr-deadbeef0000"

    digest = summarizer.build_digest(text, handle, head=HEAD_LINES, tail=TAIL_LINES)

    # Head and tail content present.
    assert "line-0" in digest
    assert "line-99" in digest
    # Middle content elided.
    assert "line-50" not in digest
    # Counts present.
    assert "100 lines" in digest  # total line count, labeled (not a bare 100)
    # Retrieval affordance present.
    assert handle in digest
    assert "context_retrieve.py" in digest
    assert "retrieve" in digest.lower()


def test_build_digest_short_text_is_not_elided(summarizer):
    # Given text shorter than head+tail, Then the full body shows, no elision.
    text = "only\ntwo lines"
    digest = summarizer.build_digest(text, "ccr-aaaaaaaaaaaa", head=20, tail=20)
    assert "only" in digest
    assert "two lines" in digest
    assert "elided" not in digest


# ---------------------------------------------------------------------------
# tool_response extraction (handles str and dict shapes)
# ---------------------------------------------------------------------------


def test_extract_tool_response_text_from_str(summarizer):
    assert summarizer.extract_tool_response_text({"tool_response": "hello"}) == "hello"


def test_extract_tool_response_text_from_dict_stdout(summarizer):
    payload = {"tool_response": {"stdout": "out", "stderr": "err"}}
    text = summarizer.extract_tool_response_text(payload)
    assert "out" in text
    assert "err" in text


def test_extract_tool_response_text_missing_is_empty(summarizer):
    assert summarizer.extract_tool_response_text({}) == ""


def test_extract_tool_response_text_unknown_dict_falls_back_to_json(summarizer):
    # Given a dict with no recognized text keys
    payload = {"tool_response": {"exitCode": 1, "meta": {"k": "v"}}}
    # When extracting, Then nothing is silently dropped (JSON dump)
    text = summarizer.extract_tool_response_text(payload)
    assert "exitCode" in text
    assert "meta" in text


def test_extract_tool_response_text_other_type_is_stringified(summarizer):
    # A list payload (unexpected shape) is stringified, not dropped.
    assert summarizer.extract_tool_response_text({"tool_response": [1, 2]}) == "[1, 2]"


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------


def _run_main(module, hook_input, monkeypatch, capsys):
    """Feed hook_input via stdin to module.main() and capture stdout."""
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(hook_input)))
    rc = module.main()
    captured = capsys.readouterr()
    return rc, captured.out


def test_main_archives_large_single_output(summarizer, monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CONSERVE_CCR_THRESHOLD", str(SMALL_THRESHOLD))
    big = "FATAL marker\n" + ("noise line\n" * 200)
    hook_input = {"tool_name": "Bash", "tool_response": {"stdout": big}}

    rc, out = _run_main(summarizer, hook_input, monkeypatch, capsys)

    assert rc == 0
    archive_dir = tmp_path / ".claude" / "context-archive"
    archived = list(archive_dir.glob("ccr-*.txt"))
    assert len(archived) == 1, "large output should be archived to a handle"
    # The digest/handle is surfaced to the model via additionalContext.
    payload = json.loads(out)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert archived[0].stem in ctx
    assert "context_retrieve.py" in ctx


def test_main_small_output_not_archived(summarizer, monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CONSERVE_CCR_THRESHOLD", str(DEFAULT_THRESHOLD))
    hook_input = {"tool_name": "Bash", "tool_response": {"stdout": "tiny output"}}

    rc, _ = _run_main(summarizer, hook_input, monkeypatch, capsys)

    assert rc == 0
    archive_dir = tmp_path / ".claude" / "context-archive"
    assert not archive_dir.exists() or not list(archive_dir.glob("ccr-*.txt"))


def test_main_is_fail_open_when_archive_errors(
    summarizer, monkeypatch, tmp_path, capsys
):
    # Given archiving raises (e.g. disk error), When the hook runs,
    # Then it never propagates the error into the host (returns 0).
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CONSERVE_CCR_THRESHOLD", str(SMALL_THRESHOLD))

    def _boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(summarizer, "archive_large_output", _boom)
    hook_input = {"tool_name": "Bash", "tool_response": {"stdout": "x" * 500}}

    rc, out = _run_main(summarizer, hook_input, monkeypatch, capsys)

    assert rc == 0
    assert out.strip() == ""  # no digest emitted, no crash


def test_main_ignores_non_target_tools(summarizer, monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CONSERVE_CCR_THRESHOLD", str(SMALL_THRESHOLD))
    hook_input = {"tool_name": "Write", "tool_response": {"stdout": "x" * 500}}

    rc, out = _run_main(summarizer, hook_input, monkeypatch, capsys)

    assert rc == 0
    assert out.strip() == ""  # no processing for non-verbose tools


# ---------------------------------------------------------------------------
# context_retrieve.py
# ---------------------------------------------------------------------------


def test_resolve_handle_with_and_without_suffix(retriever, tmp_path):
    target = tmp_path / "ccr-abc123abc123.txt"
    target.write_text("payload", encoding="utf-8")

    assert retriever.resolve_handle("ccr-abc123abc123", tmp_path) == target
    assert retriever.resolve_handle("ccr-abc123abc123.txt", tmp_path) == target


def test_resolve_handle_missing_raises(retriever, tmp_path):
    with pytest.raises(FileNotFoundError):
        retriever.resolve_handle("ccr-doesnotexist", tmp_path)


def test_slice_content_full(retriever):
    text = "a\nb\nc\nd"
    assert retriever.slice_content(text) == text


def test_slice_content_head_and_tail(retriever):
    text = "\n".join(str(i) for i in range(10))
    assert retriever.slice_content(text, head=HEAD_LINES) == "0\n1\n2"
    assert retriever.slice_content(text, tail=TAIL_LINES) == "8\n9"


def test_slice_content_line_range(retriever):
    text = "\n".join(str(i) for i in range(10))
    # 1-indexed inclusive range "3:5" -> lines 3,4,5 -> values 2,3,4
    assert retriever.slice_content(text, lines="3:5") == "2\n3\n4"


def test_slice_content_open_ended_range(retriever):
    text = "\n".join(str(i) for i in range(10))
    # "8:" with no end runs to the last line -> values 7,8,9
    assert retriever.slice_content(text, lines="8:") == "7\n8\n9"


def test_grep_content_returns_matching_lines(retriever):
    text = "ok one\nFATAL boom\nok two\nFATAL crash"
    assert retriever.grep_content(text, "FATAL") == "FATAL boom\nFATAL crash"


def test_retrieve_roundtrip_via_main(retriever, tmp_path, capsys):
    handle = "ccr-feedface0001"
    (tmp_path / f"{handle}.txt").write_text("ok\nFATAL boom\nok\n", encoding="utf-8")
    argv = [handle, "--grep", "FATAL", "--archive-dir", str(tmp_path)]

    rc = retriever.main(argv)
    out = capsys.readouterr().out

    assert rc == 0
    assert "FATAL boom" in out
    assert "ok" not in out.split("FATAL boom")[0].strip()


def test_retrieve_head_slice_via_main(retriever, tmp_path, capsys):
    handle = "ccr-feedface0002"
    (tmp_path / f"{handle}.txt").write_text("a\nb\nc\nd\ne\n", encoding="utf-8")
    rc = retriever.main([handle, "--head", "2", "--archive-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.strip() == "a\nb"


def test_retrieve_full_via_main(retriever, tmp_path, capsys):
    handle = "ccr-feedface0003"
    (tmp_path / f"{handle}.txt").write_text("x\ny\nz", encoding="utf-8")
    rc = retriever.main([handle, "--archive-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.strip() == "x\ny\nz"


def test_retrieve_missing_handle_returns_nonzero(retriever, tmp_path):
    rc = retriever.main(["ccr-missing", "--archive-dir", str(tmp_path)])
    assert rc != 0


# ---------------------------------------------------------------------------
# Regression coverage for PR #577 review findings (F1-F3)
# ---------------------------------------------------------------------------


def test_archive_large_output_handles_lone_surrogate(summarizer, tmp_path):
    """A lone surrogate must not crash the strict-UTF-8 archive write.

    UnicodeEncodeError is a ValueError, not an OSError, so it would escape
    the OSError fail-open guard. The write uses errors='replace' to match
    the handle hash, so the surrogate is archived instead of raising.
    """
    text = "start\n" + "\ud83d" + "\nend"  # lone high surrogate
    handle = summarizer.archive_large_output(text, tmp_path)
    archived = tmp_path / f"{handle}.txt"
    assert archived.is_file()
    # Round-trips through the same replace-on-error decoding retrieval uses.
    archived.read_text(encoding="utf-8", errors="replace")


def test_slice_content_tail_zero_returns_empty(retriever):
    """`--tail 0` returns zero lines, not the whole archive.

    `[-0:]` is `[0:]` (everything), the opposite of conserve's purpose.
    """
    text = "\n".join(str(i) for i in range(5))
    assert retriever.slice_content(text, tail=0) == ""


def test_slice_content_open_start_range(retriever):
    """`--lines :3` (open start) reads from the beginning through line 3."""
    text = "\n".join(str(i) for i in range(10))
    assert retriever.slice_content(text, lines=":3") == "0\n1\n2"


def test_retrieve_invalid_lines_returns_error(retriever, tmp_path):
    """A non-integer `--lines` bound is a clean error (exit 2).

    It must not surface an uncaught ValueError traceback.
    """
    handle = "ccr-feedface0010"
    (tmp_path / f"{handle}.txt").write_text("a\nb\nc\n", encoding="utf-8")
    rc = retriever.main([handle, "--lines", "abc", "--archive-dir", str(tmp_path)])
    assert rc == 2


def test_retrieve_invalid_grep_returns_error(retriever, tmp_path):
    """An invalid `--grep` regex is a clean error (exit 2).

    build_digest tells the model to pass --grep, so a malformed pattern is
    a reachable input; it must not raise an uncaught re.error traceback.
    """
    handle = "ccr-feedface0011"
    (tmp_path / f"{handle}.txt").write_text("a\nb\nc\n", encoding="utf-8")
    rc = retriever.main([handle, "--grep", "(", "--archive-dir", str(tmp_path)])
    assert rc == 2
