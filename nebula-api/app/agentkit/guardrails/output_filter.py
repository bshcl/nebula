"""Output guardrails for player-facing NPC replies."""

from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass, field

ALLOWED_ANIM_ACTIONS = frozenset({"WAVE", "ANGRY", "THINK"})

# [[ANIM:WAVE]] / [[GIFT:navigator_emblem]] / [[MOOD:72]] / [[SYSTEM:OFFLINE]]
_TAG_RE = re.compile(r"\[\[([A-Z]+):([^\]]+)\]\]")
_TOOL_XML_RE = re.compile(
    r"<\s*(tool_call|function|function_call|invoke)\b[^>]*>.*?</\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_GIFT_ID_RE = re.compile(r"^[a-z0-9_]+$", re.IGNORECASE)
# A count tied to a bag word. Ordinary numbers ("waiting 3 days") do not match.
_INVENTORY_CLAIM_RE = re.compile(
    r"(?:"
    r"\byou have\s+\d+\b[^.!?\n]{0,60}\b(?:bag|inventory|backpack)\b"
    r"|"
    r"\b(?:bag|inventory|backpack)\b[^.!?\n]{0,40}\bhas\s+\d+\b"
    r")",
    re.IGNORECASE,
)


@dataclass
class GuardrailResult:
    text: str
    violations: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.violations)


def sanitize_npc_reply(
    text: str,
    *,
    allowed_gift_ids: Collection[str] | None = None,
) -> GuardrailResult:
    """Clean one assistant reply before it is persisted / trusted.

    ``allowed_gift_ids`` is the catalog. When it is set, a well-formed
    ``[[GIFT:]]`` whose id is missing from that set is removed. When it is
    omitted, only the id shape is checked.
    """
    if not text:
        return GuardrailResult(text="")

    allowed = set(allowed_gift_ids) if allowed_gift_ids is not None else None
    violations: list[str] = []
    cleaned = text

    without_xml, xml_count = _TOOL_XML_RE.subn("", cleaned)
    if xml_count:
        violations.append("stripped_tool_xml")
        cleaned = without_xml

    def _replace_tag(match: re.Match[str]) -> str:
        kind = match.group(1).upper()
        value = match.group(2).strip()

        if kind == "ANIM":
            action = value.upper()
            if action in ALLOWED_ANIM_ACTIONS:
                return f"[[ANIM:{action}]]"
            violations.append(f"removed_anim:{action}")
            return ""

        if kind == "GIFT":
            item_id = value.strip()
            if not _GIFT_ID_RE.fullmatch(item_id):
                violations.append(f"removed_gift:{item_id}")
                return ""
            if allowed is not None and item_id not in allowed:
                violations.append(f"removed_unknown_gift:{item_id}")
                return ""
            return f"[[GIFT:{item_id}]]"

        if kind == "MOOD":
            # Server owns mood sync; model must not emit it.
            violations.append("removed_model_mood_tag")
            return ""

        if kind == "SYSTEM":
            # Keep known system markers (e.g. OFFLINE); drop unknowns.
            if value.upper() == "OFFLINE":
                return "[[SYSTEM:OFFLINE]]"
            violations.append(f"removed_system:{value}")
            return ""

        violations.append(f"removed_unknown_tag:{kind}")
        return ""

    cleaned = _TAG_RE.sub(_replace_tag, cleaned)

    without_claims, claim_count = _INVENTORY_CLAIM_RE.subn("", cleaned)
    if claim_count:
        violations.append("removed_inventory_claim")
        cleaned = without_claims

    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    # De-dupe while preserving order
    unique: list[str] = []
    for item in violations:
        if item not in unique:
            unique.append(item)
    return GuardrailResult(text=cleaned, violations=unique)
