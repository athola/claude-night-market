"""Characterization tests for prompt and file-context composition.

Written green before ``delegation_executor.py`` was split, so the split
had a contract to keep. They pin behavior, not location: the import line
is the only thing that moved with the code, and it now names
``delegation_prompt`` so deleting that module turns these red.
"""

import sys
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

import delegation_prompt as prompt_module  # noqa: E402 - sys.path set above
from delegation_executor import Delegator  # noqa: E402 - sys.path set above
from delegation_prompt import (  # noqa: E402 - sys.path set above
    MAX_INLINE_CONTEXT_BYTES,
    _compose_prompt_with_files,
    _delivered_prompt,
    _inline_context,
    _iter_context_files,
    _prompt_argv,
)
from delegation_services import ServiceConfig  # noqa: E402 - sys.path set above

_BASE = ServiceConfig(name="probe", command="probe", auth_method="none")


def _service(**overrides: Any) -> ServiceConfig:
    """Vary one provider without restating its required fields."""
    return replace(_BASE, **overrides)


class TestPromptArgv:
    """Contract for prompt argv."""

    def test_positional_provider_escapes_a_dash_prompt_with_double_dash(self) -> None:
        """Every positional CLI reads a leading dash as its own flag and prints help at exit 0, which looks like an answer to a caller."""
        assert _prompt_argv(_service(prompt_flag=None), "-x") == ["--", "-x"]
        assert _prompt_argv(_service(prompt_flag=None), "hi") == ["hi"]

    def test_flag_provider_attaches_a_dash_prompt_to_its_long_flag(self) -> None:
        """`--` protects the next positional, not a flag's operand, so the value must be attached with `=`."""
        service = _service(prompt_flag="-p", prompt_long_flag="--prompt")
        assert _prompt_argv(service, "-x") == ["--prompt=-x"]
        assert _prompt_argv(service, "hi") == ["-p", "hi"]

    def test_flag_provider_without_a_long_flag_refuses_a_dash_prompt(self) -> None:
        """A refusal that names the missing config, never a bare prompt.

        No third escape form exists, and a bare dash prompt is read by the
        CLI as its own flag and answered with a help page at exit 0. The
        refusal comes at construction, before any prompt is built.
        """
        with pytest.raises(ValueError, match="prompt_long_flag"):
            _prompt_argv(_service(prompt_flag="-p", prompt_long_flag=None), "-x")


class TestContextFiles:
    """Contract for context files."""

    def test_skips_vcs_and_venv_directories_and_sorts(self, tmp_path: Path) -> None:
        """Sorted so the same directory yields the same prompt on every run, which is what makes a delegation reproducible."""
        (tmp_path / "b.py").write_text("b")
        (tmp_path / "a.py").write_text("a")
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "x.js").write_text("x")
        names = [p.name for p in _iter_context_files([str(tmp_path)])]
        assert names == ["a.py", "b.py"]


class TestInlineContext:
    """Contract for inline context."""

    def test_each_file_is_fenced_with_begin_and_end_markers(
        self, tmp_path: Path
    ) -> None:
        """The markers are what a CLI with no `@path` syntax has instead of file references."""
        one = tmp_path / "one.txt"
        one.write_text("alpha")
        block = _inline_context([str(one)])
        assert block.startswith(f"--- BEGIN FILE: {one} ---\nalpha")
        assert block.endswith(f"--- END FILE: {one} ---")
        assert "truncated" not in block

    def test_budget_overflow_truncates_the_file_and_says_so(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Linux caps one argv entry at 128 KiB, and a silently dropped file is worse than a labeled cut."""
        big = tmp_path / "big.txt"
        big.write_text("x" * 5000)
        monkeypatch.setattr(prompt_module, "MAX_INLINE_CONTEXT_BYTES", 1500)
        block = _inline_context([str(big)])
        assert "[file truncated at" in block
        assert block.rstrip().endswith("1 file(s) included]")
        assert "[context truncated at 1500 bytes" in block


class TestComposePromptWithFiles:
    """Contract for compose prompt with files."""

    def test_reference_provider_gets_at_paths_and_a_dir_glob(
        self, tmp_path: Path
    ) -> None:
        """A path that does not exist is left out rather than passed as a reference the CLI would then fail on."""
        one = tmp_path / "one.txt"
        one.write_text("alpha")
        sub = tmp_path / "sub"
        sub.mkdir()
        composed = _compose_prompt_with_files(
            _service(inline_files=False), "go", [str(one), str(sub), "/nope"]
        )
        assert composed == f"@{one} @{sub}/**/* go"

    def test_inline_provider_gets_content_before_the_prompt(
        self, tmp_path: Path
    ) -> None:
        """Context first, so the instruction the model reads last is the user's."""
        one = tmp_path / "one.txt"
        one.write_text("alpha")
        composed = _compose_prompt_with_files(
            _service(inline_files=True), "go", [str(one)]
        )
        assert composed.startswith("--- BEGIN FILE:")
        assert composed.endswith("\n\ngo")

    def test_no_readable_files_leaves_the_prompt_alone(self) -> None:
        """Both conventions collapse to the bare prompt, so a bad path degrades to a plain delegation rather than an error."""
        assert (
            _compose_prompt_with_files(_service(inline_files=True), "go", ["/nope"])
            == "go"
        )
        assert (
            _compose_prompt_with_files(_service(inline_files=False), "go", ["/nope"])
            == "go"
        )


POSITIONAL_PROMPT_SERVICES = ("muse", "codex", "opencode")


MAX_ARG_STRLEN = 128 * 1024


class TestAPromptIsDataAndNeverArgv:
    """A prompt is attacker-shaped input; argv is the place that forgets it.

    Dogfooded on 2026-08-22. Two entry points disagree about a prompt that
    begins with a dash, and only one of them is guarded by argparse:

        CLI:    delegation_executor.py gemini "--usage" -> exit 0, prints
                the usage report, delegates nothing
        Python: Delegator.execute("muse", "--help") -> success=True,
                exit 0, and muse's own help text arrives as the answer

    The CLI path is argparse's to own. The Python path reaches the child's
    parser, and every positional-prompt provider will read a leading dash
    as its own flag. No credential is needed to trigger it and both report
    success, so a caller cannot tell an answer from a help page.

    These build argv rather than spawning, so the suite stays hermetic.
    """

    @pytest.mark.bdd
    @pytest.mark.parametrize("service", POSITIONAL_PROMPT_SERVICES)
    def test_a_positional_provider_separates_a_dash_leading_prompt(
        self,
        service: str,
    ) -> None:
        """GIVEN a prompt that begins with a dash.

        WHEN a positional-prompt provider builds its argv
        THEN an end-of-options separator precedes the prompt

        Replaces the tripwire this file used to carry, which pinned the
        exposure and said in its own docstring to rewrite it once the
        hole was closed. Probed on 2026-08-22:

            muse exec --provider echo -- "--help" -> `echo: --help`
            muse exec --provider echo    "--help" -> the help page

        The separator is emitted only for a dash-leading prompt, so every
        ordinary invocation keeps the argv it had.
        """
        command = Delegator().build_command(service, "--help")

        assert command[-2:] == ["--", "--help"]

    @pytest.mark.bdd
    @pytest.mark.parametrize("service", POSITIONAL_PROMPT_SERVICES)
    def test_an_ordinary_prompt_gains_no_separator(self, service: str) -> None:
        """GIVEN a prompt that does not begin with a dash.

        WHEN the argv is built
        THEN no separator is added

        The fix is scoped to the shape that needs it. A separator on every
        call would be a change to eight CLI contracts at once, and only
        three of them were probed for it.
        """
        command = Delegator().build_command(service, "Reply with: pong")

        assert "--" not in command
        assert command[-1] == "Reply with: pong"

    @pytest.mark.bdd
    @pytest.mark.parametrize(
        ("service", "long_flag"),
        [("gemini", "--prompt"), ("qwen", "--prompt"), ("minimax", "--message")],
    )
    def test_a_value_flag_provider_attaches_a_dash_leading_prompt(
        self,
        service: str,
        long_flag: str,
    ) -> None:
        """GIVEN a prompt that begins with a dash.

        WHEN a provider that passes the prompt as a flag value builds argv
        THEN the value is attached to the long flag with an equals sign

        A separator does not help here, and assuming it did is why the
        first version of this documentation called these providers safe.
        Probed on 2026-08-22:

            gemini -p    "--help" -> the help page
            gemini -p -- "--help" -> the help page
            gemini --prompt="--help" -> reached authentication

        `mmx --message=` and `qwen --prompt=` behave the same way.
        """
        command = Delegator().build_command(service, "--help")

        assert f"{long_flag}=--help" in command
        assert "--help" not in command[:-1] or command[-1].startswith(long_flag)

    @pytest.mark.bdd
    def test_a_stdin_provider_is_structurally_immune(self) -> None:
        """GIVEN a prompt that begins with a dash.

        WHEN a stdin-delivering provider builds its argv
        THEN the prompt is absent from argv entirely

        glimmer is the one provider no escaping applies to, because the
        prompt never reaches a parser that reads flags.
        """
        command = Delegator().build_command("glimmer", "--help")

        assert "--help" not in command

    @pytest.mark.bdd
    def test_shell_metacharacters_survive_as_one_literal_argument(self) -> None:
        """GIVEN a prompt carrying command substitution and a semicolon.

        WHEN the argv is built
        THEN the whole prompt is a single unsplit argument

        Verified against the filesystem on 2026-08-22: the substitution
        did not run. This pins argv assembly only. Whether a shell ever
        sees the list is decided at spawn time, and is guarded by
        `test_the_child_is_spawned_without_a_shell` below.
        """
        evil = "$(touch /tmp/pwned); `id`; rm -rf /nothing"

        command = Delegator().build_command("minimax", evil)

        assert command.count(evil) == 1
        assert all(";" not in part for part in command if part != evil)

    @pytest.mark.bdd
    def test_the_child_is_spawned_without_a_shell(self) -> None:
        """GIVEN any delegation.

        WHEN the child process is spawned
        THEN argv is passed as a list and no shell interprets it

        Assembling argv safely is undone by spawning it through a shell,
        and the two live in different functions. Adding `shell=True` to
        `_launch_process` leaves every argv-level assertion green, so
        this reads the spawn call's own arguments.
        """
        captured: dict[str, object] = {}

        def fake_run(cmd: object, **kwargs: object) -> MagicMock:
            captured["cmd"] = cmd
            captured["shell"] = kwargs.get("shell", False)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("delegation_executor.subprocess.run", side_effect=fake_run):
            Delegator().execute("minimax", "$(id); echo hi", timeout=5)

        assert captured["shell"] is False
        assert isinstance(captured["cmd"], list)

    @pytest.mark.bdd
    def test_the_context_ceiling_does_not_bound_the_prompt(self) -> None:
        """GIVEN a prompt larger than the inline-context ceiling.

        WHEN the argv is built
        THEN the prompt is carried whole, uncapped

        MAX_INLINE_CONTEXT_BYTES bounds what file context adds, not what
        the caller passes. Past MAX_ARG_STRLEN the spawn fails E2BIG:
        measured on 2026-08-22, 127 KiB spawned and 128 KiB did not.
        The executor reports that as a named failure rather than
        truncating, which is the behavior worth keeping.
        """
        oversized = "x" * (MAX_INLINE_CONTEXT_BYTES * 2)

        command = Delegator().build_command("minimax", oversized)

        assert oversized in command
        assert len(oversized) > MAX_INLINE_CONTEXT_BYTES


class TestMissingContextIsDroppedWithoutASignal:
    """Truncated context is named; absent context is not.

    Dogfooded on 2026-08-22 against a real filesystem. A file that cannot
    be found contributes nothing and says nothing, at any log level:

        _delivered_prompt(minimax, "ASK", ["/nope.txt"]) -> "ASK"

    An oversized file is the opposite: it arrives cut and labelled
    `[context truncated at 98304 bytes; N file(s) included]`. Both are
    context loss, and only one reaches the caller as a fact. The mixed
    case is the one that bites, because a caller passing several paths
    gets a plausible prompt built from the subset that resolved.
    """

    @pytest.mark.bdd
    def test_an_unresolvable_path_contributes_nothing_and_says_nothing(
        self,
        tmp_path: Path,
    ) -> None:
        """GIVEN a context file that does not exist.

        WHEN the prompt is assembled for an inlining provider
        THEN the prompt is returned unchanged, with no marker

        Pinning the current behavior so that adding a signal later is a
        deliberate change rather than an accident.
        """
        service = Delegator().services["minimax"]

        delivered = _delivered_prompt(service, "ASK", [str(tmp_path / "nope.txt")])

        assert delivered == "ASK"

    @pytest.mark.bdd
    def test_a_resolvable_path_survives_beside_an_unresolvable_one(
        self,
        tmp_path: Path,
    ) -> None:
        """GIVEN one context file that exists and one that does not.

        WHEN the prompt is assembled
        THEN the good file is inlined and the bad one leaves no trace

        The prompt looks complete. Nothing in it distinguishes "one file
        was requested" from "two were requested and one vanished".
        """
        good = tmp_path / "good.txt"
        good.write_text("KEEPME")
        service = Delegator().services["minimax"]

        delivered = _delivered_prompt(
            service,
            "ASK",
            [str(good), str(tmp_path / "nope.txt")],
        )

        assert "KEEPME" in delivered
        assert "nope.txt" not in delivered

    @pytest.mark.bdd
    def test_oversized_context_arrives_cut_and_labelled(
        self,
        tmp_path: Path,
    ) -> None:
        """GIVEN a context file past the inline ceiling.

        WHEN the prompt is assembled
        THEN it is capped and carries a marker naming the ceiling

        The contrast with an unresolvable path is the point: this loss is
        reported, and it stays under MAX_ARG_STRLEN so the spawn survives.
        """
        huge = tmp_path / "huge.txt"
        huge.write_text("A" * (MAX_INLINE_CONTEXT_BYTES * 2))
        service = Delegator().services["minimax"]

        delivered = _delivered_prompt(service, "ASK", [str(huge)])

        assert "truncated" in delivered
        assert str(MAX_INLINE_CONTEXT_BYTES) in delivered
        assert len(delivered) < MAX_ARG_STRLEN


class TestInlineContextLeavesRoomForThePrompt:
    """The argv ceiling is per element, and the prompt shares the element."""

    @pytest.mark.parametrize("name", ["minimax", *POSITIONAL_PROMPT_SERVICES])
    def test_context_and_prompt_together_fit_one_argv_element(
        self, tmp_path: Path, name: str
    ) -> None:
        """GIVEN a 240 KB context file and a 40 KB prompt.

        WHEN the delivered prompt is turned into argv
        THEN its longest element, with the NUL, fits MAX_ARG_STRLEN
        AND the prompt is carried whole

        Math review finding C2-10: context was capped at 96 KiB and the
        prompt appended to the same element, giving 139123 bytes.
        """
        big = tmp_path / "big.py"
        big.write_text("x = 1\n" * 40000)
        prompt = "Review this module.\n" + "Constraint: keep it.\n" * 2000
        service = Delegator().services[name]

        delivered = _delivered_prompt(service, prompt, [str(big)])
        longest = max(_prompt_argv(service, delivered), key=len)

        assert len(longest.encode("utf-8")) + 1 <= MAX_ARG_STRLEN
        assert delivered.endswith(prompt)
        assert "truncated" in delivered
