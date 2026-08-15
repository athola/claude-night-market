"""The three duplicated hook payload readers must agree on their contract.

Claude Code delivers hook payloads as JSON on stdin, with the legacy
``CLAUDE_TOOL_*`` environment variables as a fallback. Three plugins each
implement that read:

* ``leyline/hooks/noqa_guard._read_payload``
* ``sanctum/hooks/deferred_item_watcher.read_payload``
* ``abstract/hooks/shared/hook_io.read_hook_payload``

Plugin isolation forbids a cross-plugin import, so the copies cannot be
collapsed into one. Until this file existed, the only thing holding them
together was a comment in each saying the three must change together --
and the comment had already lost. ``hook_io`` coerced ``tool_input`` to a
dict on both paths, ``deferred_item_watcher`` on the environment path
alone, and ``noqa_guard`` on neither, so a list-valued
``CLAUDE_TOOL_INPUT`` reached a consumer that calls ``.get`` on it.

The shared contract is deliberately narrow: whatever else a reader adds,
``tool_name`` is a ``str`` and ``tool_input`` is a ``dict``. Both are what
every consumer indexes into without checking. Reader-specific keys
(``tool_response``, ``session_id``) are each reader's own business and are
not asserted here.

This is a test at the repo root because it is the only level that can see
all three plugins at once.
"""

from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLUGINS = REPO_ROOT / "plugins"

# (id, module path, extra sys.path entry, reader attribute)
READERS = [
    (
        "noqa_guard",
        PLUGINS / "leyline" / "hooks" / "noqa_guard.py",
        None,
        "_read_payload",
    ),
    (
        "deferred_item_watcher",
        PLUGINS / "sanctum" / "hooks" / "deferred_item_watcher.py",
        PLUGINS / "sanctum" / "hooks",
        "read_payload",
    ),
    (
        "hook_io",
        PLUGINS / "abstract" / "hooks" / "shared" / "hook_io.py",
        None,
        "read_hook_payload",
    ),
]


def _load_reader(path: Path, extra_path: Path | None, attr: str):
    """Import a hook module by file path and return its reader function."""
    if extra_path is not None and str(extra_path) not in sys.path:
        sys.path.insert(0, str(extra_path))
    spec = importlib.util.spec_from_file_location(f"_payload_{path.stem}", path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, attr)


@pytest.fixture(params=READERS, ids=[reader[0] for reader in READERS])
def reader(request):
    """Yield each payload reader in turn."""
    _name, path, extra_path, attr = request.param
    if not path.is_file():
        pytest.fail(f"payload reader missing: {path.relative_to(REPO_ROOT)}")
    return _load_reader(path, extra_path, attr)


@pytest.fixture
def no_legacy_env(monkeypatch):
    """Clear the legacy variables so a case cannot pass on ambient state."""
    for name in (
        "CLAUDE_TOOL_NAME",
        "CLAUDE_TOOL_INPUT",
        "CLAUDE_TOOL_OUTPUT",
        "CLAUDE_SESSION_ID",
    ):
        monkeypatch.delenv(name, raising=False)


def _feed_stdin(monkeypatch, text: str) -> None:
    """Replace stdin with a non-tty stream carrying ``text``."""
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))


class TestAllReadersLoad:
    """The matrix below is vacuous if the modules do not import."""

    @pytest.mark.unit
    def test_every_declared_reader_is_callable(self, reader):
        """
        GIVEN a declared payload reader
        WHEN the module is imported by path
        THEN the named reader function exists and is callable
        """
        assert callable(reader)


class TestSharedPayloadContract:
    """Scenario: every reader returns a str tool_name and a dict tool_input."""

    @pytest.mark.unit
    def test_stdin_payload_is_returned(self, reader, monkeypatch, no_legacy_env):
        """
        GIVEN a well-formed JSON payload on stdin
        WHEN the reader runs
        THEN the payload's tool_name and tool_input come back
        """
        _feed_stdin(monkeypatch, '{"tool_name": "Edit", "tool_input": {"a": 1}}')
        payload = reader()
        assert payload["tool_name"] == "Edit"
        assert payload["tool_input"] == {"a": 1}

    @pytest.mark.unit
    def test_empty_stdin_falls_back_to_env(self, reader, monkeypatch, no_legacy_env):
        """
        GIVEN empty stdin and the legacy environment variables set
        WHEN the reader runs
        THEN it reads the legacy variables
        """
        _feed_stdin(monkeypatch, "")
        monkeypatch.setenv("CLAUDE_TOOL_NAME", "Write")
        monkeypatch.setenv("CLAUDE_TOOL_INPUT", '{"file_path": "x.py"}')
        payload = reader()
        assert payload["tool_name"] == "Write"
        assert payload["tool_input"] == {"file_path": "x.py"}

    @pytest.mark.unit
    def test_malformed_stdin_warns_and_does_not_raise(
        self, reader, monkeypatch, no_legacy_env, capsys
    ):
        """
        GIVEN stdin carrying text that is not JSON
        WHEN the reader runs
        THEN it returns a usable payload
        AND it writes a warning to stderr

        A corrupted payload must be distinguishable from an idle hook. The
        legacy variables are unset on a real invocation, so a silently
        swallowed decode error makes every consumer no-op with no signal.
        """
        _feed_stdin(monkeypatch, "not json at all")
        payload = reader()
        assert isinstance(payload["tool_name"], str)
        assert capsys.readouterr().err.strip(), "malformed payload must warn"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "stdin_text",
        ['["a", "b"]', '"a string"', "42", "null"],
        ids=["list", "string", "number", "null"],
    )
    def test_non_object_stdin_still_yields_a_dict_tool_input(
        self, reader, monkeypatch, no_legacy_env, stdin_text
    ):
        """
        GIVEN stdin carrying valid JSON that is not an object
        WHEN the reader runs
        THEN tool_input is still a dict
        """
        _feed_stdin(monkeypatch, stdin_text)
        payload = reader()
        assert isinstance(payload["tool_input"], dict)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "env_value",
        ['["a"]', '"a string"', "7", "not json", ""],
        ids=["list", "string", "number", "garbage", "empty"],
    )
    def test_non_object_env_tool_input_still_yields_a_dict(
        self, reader, monkeypatch, no_legacy_env, env_value
    ):
        """
        GIVEN empty stdin and a CLAUDE_TOOL_INPUT that is not a JSON object
        WHEN the reader runs
        THEN tool_input is still a dict

        Consumers index tool_input without checking. A list here is how a
        hook raises AttributeError on a payload it was handed, not on one
        it built.
        """
        _feed_stdin(monkeypatch, "")
        monkeypatch.setenv("CLAUDE_TOOL_INPUT", env_value)
        payload = reader()
        assert isinstance(payload["tool_input"], dict)

    @pytest.mark.unit
    def test_missing_keys_yield_typed_empties(self, reader, monkeypatch, no_legacy_env):
        """
        GIVEN a JSON object on stdin carrying neither key
        WHEN the reader runs
        THEN tool_name is a str and tool_input is a dict
        """
        _feed_stdin(monkeypatch, "{}")
        payload = reader()
        assert isinstance(payload["tool_name"], str)
        assert isinstance(payload["tool_input"], dict)

    @pytest.mark.unit
    def test_null_valued_keys_yield_typed_empties(
        self, reader, monkeypatch, no_legacy_env
    ):
        """
        GIVEN a JSON object whose two shared keys are explicitly null
        WHEN the reader runs
        THEN tool_name is a str and tool_input is a dict

        An absent key and a null-valued key arrive the same way over the
        wire; a reader that only guards ``.get`` misses the second.
        """
        _feed_stdin(monkeypatch, '{"tool_name": null, "tool_input": null}')
        payload = reader()
        assert isinstance(payload["tool_name"], str)
        assert isinstance(payload["tool_input"], dict)
