"""The hook events Claude Code fires, as one set every validator reads.

``frontmatter.py`` and ``scripts/hook_validator.py`` each kept their own copy.
The frontmatter copy stopped at the 2.1.50 roster of 19 and called 14 real
events invalid, so the two disagreed about the same hooks.json. The source is
the event headings of code.claude.com/docs/en/hooks (33 events at 2.1.289).

Standard library only: ``hook_validator.py`` runs under the operator's bare
``python3``.
"""

from __future__ import annotations

HOOK_EVENTS = frozenset(
    {
        "ConfigChange",
        "CwdChanged",
        "DirectoryAdded",
        "Elicitation",
        "ElicitationResult",
        "FileChanged",
        "InstructionsLoaded",
        "MessageDisplay",
        "Notification",
        "PermissionDenied",
        "PermissionRequest",
        "PostCompact",
        "PostModelSwitch",
        "PostToolBatch",
        "PostToolUse",
        "PostToolUseFailure",
        "PreCompact",
        "PreModelSwitch",
        "PreToolUse",
        "SessionEnd",
        "SessionStart",
        "Setup",
        "Stop",
        "StopFailure",
        "SubagentStart",
        "SubagentStop",
        "TaskCompleted",
        "TaskCreated",
        "TeammateIdle",
        "UserPromptExpansion",
        "UserPromptSubmit",
        "WorktreeCreate",
        "WorktreeRemove",
    }
)
