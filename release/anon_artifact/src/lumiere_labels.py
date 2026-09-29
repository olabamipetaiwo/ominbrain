"""
Canonical answer-text comparison for LUMIERE items.

The v3 DSCR drafts spell the same RANO category two ways: "Progressive disease" (33 of the 52 keys) and
"Progressive disease (PD)" (2 keys). Comparing raw strings therefore counted 33 progressive-disease keys
instead of 35, so the DSCR majority baseline was reported as 63.5% (33/52) where it is 67.3% (35/52),
and the two mis-spelt keys were treated as non-progressive in the TCM lookup and the donor check.
The item files are left untouched (they are what the models were shown); every analysis that compares
answer TEXT goes through canonical_answer_text().
"""

from __future__ import annotations

import re

_RANO = ("progressive disease", "stable disease", "partial response", "complete response")
_RANO_RE = re.compile(r"^\s*(" + "|".join(_RANO) + r")\s*(\([^)]*\))?\s*\.?\s*$", re.IGNORECASE)


def canonical_answer_text(text: str) -> str:
    """RANO category strings collapse to one spelling; every other text is returned unchanged."""
    m = _RANO_RE.match(text or "")
    return m.group(1).capitalize() if m else text
