"""Prompt and file-context composition for delegation.

Split out of ``delegation_executor``: everything here turns a prompt and
a list of paths into the text and argv a CLI receives, and none of it
spawns a process. Imports flow one way: this module knows the service
contract and nothing about ``Delegator``.
"""

from __future__ import annotations

import logging
from pathlib import Path

from scripts.delegation_services import ServiceConfig

try:
    from leyline.tokens import estimate_tokens
except ImportError:  # pragma: no cover

    def estimate_tokens(files: list[str], prompt: str = "") -> int:
        """Estimate tokens as fallback when leyline isn't installed."""
        total = len(prompt) // 4

        skip_dirs = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
            "dist",
            "build",
        }
        for p in files:
            path = Path(p)
            if path.is_file():
                try:
                    total += (
                        len(path.read_text(encoding="utf-8", errors="replace")) // 4
                    )
                except OSError:
                    pass
            elif path.is_dir():
                for child in path.rglob("*"):
                    if any(part in skip_dirs for part in child.parts):
                        continue
                    if child.is_file():
                        try:
                            total += (
                                len(child.read_text(encoding="utf-8", errors="replace"))
                                // 4
                            )
                        except OSError:
                            pass

        return total


logger = logging.getLogger(__name__)

# Linux caps a single argv entry at MAX_ARG_STRLEN (128 KiB). A CLI without a
# file-reference syntax must carry file contents inside the prompt argument, so
# inlined context is bounded well below that ceiling and the remainder is
# reported as truncated rather than failing the exec with E2BIG.
MAX_INLINE_CONTEXT_BYTES = 96 * 1024

# Below this much remaining budget a file cannot carry useful content, so the
# walk stops instead of emitting header-only blocks.
_MIN_INLINE_FILE_BYTES = 512


def _iter_context_files(files: list[str]) -> list[Path]:
    """Expand the requested paths into a stable list of readable files."""
    skip_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__"}
    resolved: list[Path] = []
    for file_path in files:
        path = Path(file_path)
        if path.is_file():
            resolved.append(path)
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if any(part in skip_dirs for part in child.parts):
                    continue
                if child.is_file():
                    resolved.append(child)
    return resolved


def _inline_context(files: list[str]) -> str:
    """Read file contents into a prompt block for CLIs without ``@path``.

    Reading the filesystem is a trust boundary, so unreadable files are
    skipped rather than aborting the delegation. The byte budget is an OS
    limit (see MAX_INLINE_CONTEXT_BYTES), and hitting it is reported in the
    prompt and the log instead of silently dropping context.
    """
    blocks: list[str] = []
    used = 0
    truncated = False

    for path in _iter_context_files(files):
        remaining = MAX_INLINE_CONTEXT_BYTES - used
        if remaining <= _MIN_INLINE_FILE_BYTES:
            truncated = True
            break

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            logger.warning("Skipping unreadable context file %s: %s", path, e)
            continue

        header = f"--- BEGIN FILE: {path} ---\n"
        footer = f"\n--- END FILE: {path} ---"
        budget = remaining - len(header.encode("utf-8")) - len(footer.encode("utf-8"))
        if budget <= 0:
            # The markers alone outgrow what is left, which a deep path can
            # do while `remaining` still clears _MIN_INLINE_FILE_BYTES. Skip
            # rather than slice: a negative bound counts from the end of the
            # file, so the tighter the budget the more it would admit, and
            # the argument would exceed the execve limit this ceiling exists
            # to stay under.
            truncated = True
            continue
        encoded = content.encode("utf-8")
        if len(encoded) > budget:
            # Carry as much of the file as fits rather than dropping it whole:
            # one oversized file must not yield a prompt with no context at all.
            content = encoded[:budget].decode("utf-8", errors="ignore")
            content += f"\n[file truncated at {budget} bytes]"
            truncated = True

        block = header + content + footer
        blocks.append(block)
        used += len(block.encode("utf-8")) + 1

    if truncated:
        logger.warning(
            "Inline context truncated at %d bytes; %d file(s) included",
            MAX_INLINE_CONTEXT_BYTES,
            len(blocks),
        )
        blocks.append(
            f"[context truncated at {MAX_INLINE_CONTEXT_BYTES} bytes; "
            f"{len(blocks)} file(s) included]"
        )

    return "\n".join(blocks)


def _prompt_argv(service: ServiceConfig, prompt: str) -> list[str]:
    """Return the argv tail that delivers ``prompt`` as data, never as flags.

    Every CLI in the registry except the stdin one reads a dash-leading
    prompt as its own flag and answers with a help page, exiting 0. That
    is indistinguishable from an answer to a caller, and it needs no
    credential to trigger. The two escapes are not interchangeable:

    - a positional provider takes ``--``, which ends option parsing
    - a provider whose flag takes a value needs the value attached, as
      ``--prompt=<text>``, because ``--`` protects the next positional
      argument and not the flag's operand

    Both are applied only to a prompt that begins with a dash, so an
    ordinary call builds the argv it always built.
    """
    needs_escape = prompt.startswith("-")

    if service.prompt_flag is None:
        return ["--", prompt] if needs_escape else [prompt]

    if needs_escape and service.prompt_long_flag:
        return [f"{service.prompt_long_flag}={prompt}"]

    if needs_escape:
        # A flag provider with no long form has no third escape. Sending the
        # prompt bare reproduces the failure this function exists to stop:
        # the CLI reads it as its own flag and prints help at exit 0.
        raise ValueError(
            f"{service.name}: a dash-leading prompt cannot be escaped without "
            "prompt_long_flag; set it in the service config"
        )
    return [service.prompt_flag, prompt]


def _delivered_prompt(
    service: ServiceConfig,
    prompt: str,
    files: list[str] | None,
) -> str:
    """Build the prompt text as the service will receive it, files included.

    Shared by ``build_command`` and ``execute`` so the argv form and the stdin
    form cannot drift: a stdin-delivering service must send exactly what an
    argv-delivering one would have carried.
    """
    if files:
        return _compose_prompt_with_files(service, prompt, files)
    return prompt


def _compose_prompt_with_files(
    service: ServiceConfig,
    prompt: str,
    files: list[str],
) -> str:
    """Attach file context to a prompt using the service's own convention."""
    if service.inline_files:
        context = _inline_context(files)
        return f"{context}\n\n{prompt}" if context else prompt

    file_refs = []
    for file_path in files:
        path = Path(file_path)
        if path.exists():
            if path.is_file():
                file_refs.append(f"@{file_path}")
            elif path.is_dir():
                # Use glob pattern for directories
                file_refs.append(f"@{file_path}/**/*")
    if file_refs:
        return " ".join(file_refs) + " " + prompt
    return prompt
