"""Node tool allowlists. The checker knows no game names.

A caller registers which tool names and argument shapes a node may use.
Anything else is rejected before a service runs.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

TOOL_NOT_ALLOWED = "tool_not_allowed"
MISSING_ARGUMENT = "missing_argument"
UNEXPECTED_ARGUMENT = "unexpected_argument"
BAD_ARGUMENT_TYPE = "bad_argument_type"


@dataclass(frozen=True)
class ArgumentSpec:
    """One model-supplied argument. Injected state is not an argument."""

    name: str
    required: bool = True


def check_tool_call(
    allowed: Mapping[str, tuple[ArgumentSpec, ...]],
    tool_name: str,
    arguments: Mapping[str, object],
) -> str | None:
    """Return a fixed reason code, or None when the call may proceed."""
    spec = allowed.get(tool_name)
    if spec is None:
        return TOOL_NOT_ALLOWED

    expected = {arg.name: arg for arg in spec}
    for key in arguments:
        if key not in expected:
            return UNEXPECTED_ARGUMENT

    for arg in spec:
        if arg.name not in arguments:
            if arg.required:
                return MISSING_ARGUMENT
            continue
        if not isinstance(arguments[arg.name], str):
            return BAD_ARGUMENT_TYPE
    return None
