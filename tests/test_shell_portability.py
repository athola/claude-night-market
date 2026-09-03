"""Shell and Makefile constructs that break on the documented toolchain.

The build-and-env skill accepts stock macOS: bash 3.2, BSD coreutils,
GNU make 3.81 from the Xcode command line tools. The September 2026
review reproduced each construct below failing on that host. Each test
names the failure it guards so the next reader knows what breaks.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS = REPO_ROOT / "plugins"
AUTH_MODULE = PLUGINS / "leyline" / "scripts" / "interactive_auth.sh"


def test_house_lint_gate_passes_arguments_in_the_form_set_u_accepts() -> None:
    """`main "${@}"` under `set -eu` is an unbound-variable error on bash 3.2
    when there are no arguments, so `sh scripts/shellcheck.sh` aborted before
    linting anything. `"$@"` is the form bash 3.2 exempts.
    """
    last = (
        (REPO_ROOT / "scripts" / "shellcheck.sh").read_text().rstrip().splitlines()[-1]
    )
    assert last == 'main "$@"', last


def test_ci_detection_guards_unset_variables() -> None:
    """is_ci() read $CI and friends bare; any `set -u` caller, including the
    module's own test script, aborted with 'unbound variable'.
    """
    body = AUTH_MODULE.read_text()
    for name in (
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "AWS_EXECUTION_ENV",
        "GITHUB_TOKEN",
        "GITLAB_TOKEN",
    ):
        assert not re.search(rf'-[nz] "\${name}"', body), (
            f"bare ${name} tested in interactive_auth.sh"
        )


def test_auth_module_refuses_bash_3_before_declaring_associative_arrays() -> None:
    """`declare -A` is a parse error on stock macOS bash 3.2, mid-source, with
    no message naming the cause. A version check must come first.
    """
    body = AUTH_MODULE.read_text()
    assert body.index("BASH_VERSINFO") < re.search(r"^declare -A", body, re.M).start()


def test_jq_programs_take_data_as_arguments_not_interpolation() -> None:
    """A key or value spliced into a jq program is jq code. `--arg` is data."""
    for path in [AUTH_MODULE, REPO_ROOT / "scripts" / "shared" / "json_utils.sh"]:
        for line in path.read_text().splitlines():
            if "jq" in line and not line.lstrip().startswith("#"):
                assert not re.search(r'jq\s+-r\s+"\.\$', line), (
                    f"{path.name}: {line.strip()}"
                )
                assert not re.search(r'jq\s+"\.\$', line), (
                    f"{path.name}: {line.strip()}"
                )


def test_tokens_are_not_echoed_into_a_pipeline() -> None:
    """`echo "$token" | gh auth login` prints the token under `set -x`, which
    the house rule makes every script able to enable.
    """
    body = AUTH_MODULE.read_text()
    assert 'echo "$token"' not in body
    assert 'echo "$GITHUB_TOKEN"' not in body


def test_supported_services_message_lists_every_key() -> None:
    """`${!ARRAY[@]}` inside a string keeps only the first key (SC2145)."""
    assert "${!AUTH_CHECK_COMMANDS[@]}" not in AUTH_MODULE.read_text()


def test_setup_hooks_avoid_bash_3_and_bsd_traps() -> None:
    """bash 3.2 rejects a fractional `read -t`, so conserve's setup hook never
    saw its maintenance branch; BSD uniq has no -w, so memory-palace's setup
    hook died under pipefail before emitting JSON.
    """
    conserve = (PLUGINS / "conserve" / "hooks" / "setup.sh").read_text()
    palace = (PLUGINS / "memory-palace" / "hooks" / "setup.sh").read_text()
    assert not re.search(r"read -t 0\.\d", conserve)
    assert "uniq -d -w" not in palace


def test_root_makefile_hashes_with_a_tool_macos_ships() -> None:
    """`sha256sum` is GNU coreutils; macOS ships `shasum -a 256`."""
    body = (REPO_ROOT / "Makefile").read_text()
    recipe_lines = [line for line in body.splitlines() if line.startswith("\t")]
    assert not any("sha256sum" in line for line in recipe_lines), (
        "bare sha256sum in a recipe"
    )


def test_shared_includes_say_when_make_is_too_old_to_honor_them() -> None:
    """GNU make 3.81 silently ignores .SHELLFLAGS and .ONESHELL, so every
    recipe runs without -euo pipefail. The include must say so.
    """
    for name in ("common.mk", "markdown-only.mk"):
        body = (PLUGINS / "abstract" / "config" / "make" / name).read_text()
        assert "MAKE_VERSION" in body, name


def test_no_notparallel_with_prerequisites() -> None:
    """Prerequisite-scoped .NOTPARALLEL is honored only by recent make; on
    3.81 it serializes the whole invocation under -j.
    """
    for makefile in PLUGINS.glob("*/Makefile"):
        for line in makefile.read_text().splitlines():
            assert not re.match(r"\.NOTPARALLEL:\s*\S", line), (
                f"{makefile.parent.name}: {line}"
            )
