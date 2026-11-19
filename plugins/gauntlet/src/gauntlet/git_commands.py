"""Recognize a git commit inside a Bash command string.

The detector is leyline's ``shell_command``, carried here as a generated
copy so gauntlet's precommit gate and imbue's vows agree on what commits.
"""

from __future__ import annotations

from gauntlet._vendored_leyline_shell_command import is_git_commit

__all__ = ["is_git_commit"]
