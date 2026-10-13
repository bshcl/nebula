"""Deterministic checks on player text before it enters the model.

No character, item, or quest names belong here. The filter only decides
whether a message may be stored and sent on, and why not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MAX_USER_INPUT_CHARS = 500

# Obvious instruction-override phrases only. Not a content-moderation list.
_INJECTION_PHRASES = (
    "ignore previous instructions",
    "ignore all previous instructions",
)

_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class InputFilterResult:
    """Outcome of screening one player message."""

    text: str
    reason: str | None
    rejected: bool


def screen_user_input(text: str) -> InputFilterResult:
    """Return the text that may be stored, or a rejection that must not be stored.

    Empty and injection hits set ``rejected``. Over-long text is cut to
    ``MAX_USER_INPUT_CHARS`` and still allowed through.
    """
    stripped = text.strip()
    if not stripped:
        return InputFilterResult(text="", reason="empty", rejected=True)

    normalized = _WHITESPACE_RE.sub(" ", stripped.casefold())
    for phrase in _INJECTION_PHRASES:
        if phrase.casefold() in normalized:
            return InputFilterResult(text="", reason="prompt_injection", rejected=True)

    if len(stripped) > MAX_USER_INPUT_CHARS:
        return InputFilterResult(
            text=stripped[:MAX_USER_INPUT_CHARS],
            reason="truncated",
            rejected=False,
        )
    return InputFilterResult(text=stripped, reason=None, rejected=False)
