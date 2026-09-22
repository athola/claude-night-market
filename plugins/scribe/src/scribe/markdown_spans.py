"""The one inline-code pattern every scribe check strips before scoring.

Four sites used to carry their own copy and three of them were the
single-backtick form. On an RST double-backtick span that form matches
the opening pair as an empty span and the closing pair as another,
which leaves the code between them exposed: ``to_american`` rewrote
``colour`` inside one, and the negation density counted ``not_found``
as a stance. Importing one compiled pattern is what keeps the four
from drifting apart again.

The double-backtick alternative comes first so the single-backtick one
cannot consume the opening pair. The single-backtick alternative stops
at a newline, because an unmatched backtick would otherwise swallow the
rest of the document.
"""

from __future__ import annotations

import re

__all__ = ["INLINE_CODE"]

INLINE_CODE = re.compile(r"``[^`]*``|`[^`\n]*`")
