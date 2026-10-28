"""stdlib-only helpers shared by modules that hooks import.

``utils`` imports PyYAML, and the homeostatic hook runs under the
operator's bare python3. A module the hook loads through ``utils``
failed to import there, and the hook's ImportError guard turned that
into a silently missing feature. These live here so that cannot happen.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def safe_json_load(path: Path, default: Any = None) -> Any:
    """Load JSON from a file, returning a default value on any error.

    Args:
        path: Path to the JSON file.
        default: Value to return if the file is missing or malformed.

    Returns:
        Parsed JSON data, or default on FileNotFoundError, OSError,
        or json.JSONDecodeError.

    """
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, OSError, json.JSONDecodeError) as e:
        logger.debug("safe_json_load: %s: %s", path, e)
        return default


def emit_warn(module: str, message: str) -> None:
    """Write a newline-terminated ``module: message`` line to stderr.

    Centralised replacement for the per-module ``_warn`` helpers
    (D-12) used by improvement_queue, improvement_memory, and
    performance_tracker. Stderr (not logging) is the contract
    those modules' tests assert on via ``capsys``.
    """
    sys.stderr.write(f"{module}: {message}\n")
