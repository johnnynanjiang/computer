"""Single source of truth for turning a tool call's (name, title, arguments)
into what gets shown to a user: a short title and an optional one-line hint.

Previously this heuristic was hand-copied in three places (the Codex adapter,
the OpenAI-compatible gateway, and the frontend's toolLabel()), each with an
incomplete field-name list — none of them knew about Codex MCP calls' actual
`server`/`tool` fields, or that some adapters nest a tool's real arguments
under a single wrapper key. Call this once, centrally, and everything else
just displays the result.
"""

from __future__ import annotations

from typing import Any

# Ordered by how likely the value is to be the single most useful thing to
# show next to the tool name. Extend this list — not per-adapter guesses —
# when a new backend's argument shape isn't well summarized.
_HINT_KEYS = (
    "command",
    "file_path",
    "path",
    "url",
    "pattern",
    "query",
    "prompt",
    "task",
)

# The hint is a glance, not the detail — the full arguments are always one
# click away in the expanded JSON. Keep it short enough to stay a label
# rather than becoming a second, truncated copy of the command line.
_HINT_MAX_CHARS = 20


def _unwrap_single_dict_value(arguments: dict[str, Any]) -> dict[str, Any]:
    """Some adapters can only pass a tool's real arguments through nested
    under one wrapper key (e.g. an `input` payload). Transparently unwrap a
    lone dict-valued key so hint lookup still sees the real fields.
    """
    if len(arguments) == 1:
        (only_value,) = arguments.values()
        if isinstance(only_value, dict):
            return only_value
    return arguments


def _clip_hint(value: str) -> str:
    hint = " ".join(value.split()).replace("<", "‹").replace(">", "›")
    if len(hint) <= _HINT_MAX_CHARS:
        return hint
    truncated = hint[:_HINT_MAX_CHARS]
    # Prefer breaking at a word boundary so e.g. a command's first token
    # ("/bin/bash") isn't chopped mid-word into something unreadable.
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return f"{truncated} ..."


def describe_tool_call(
    name: str | None,
    title: str | None,
    arguments: dict[str, Any] | None,
) -> tuple[str, str | None]:
    """Return (display_title, one_line_hint) for a tool call.

    `title` (an adapter-supplied human-friendly name, when known) wins over
    `name` (a coarse routing category like "agent_tool"/"run_command"). MCP
    tool calls carrying `server`/`tool` fields get a `server.tool` title even
    without an explicit `title`, since that's a stronger signal than a bare
    category name.
    """
    args = _unwrap_single_dict_value(dict(arguments or {}))

    tool = args.get("tool")
    if isinstance(tool, str) and tool.strip():
        server = args.get("server")
        display_title = (
            f"{server}.{tool.strip()}"
            if isinstance(server, str) and server.strip()
            else tool.strip()
        )
    else:
        display_title = (title or name or "tool").strip() or "tool"

    hint_value = next(
        (args[key] for key in _HINT_KEYS if isinstance(args.get(key), str) and args[key].strip()),
        None,
    )
    hint = _clip_hint(hint_value) if hint_value else None

    return display_title, hint


def is_command_like(arguments: dict[str, Any] | None) -> bool:
    """Whether a tool call's arguments represent shell/command execution.

    Reuses the exact same signal `describe_tool_call()` treats as the
    strongest hint (a non-empty `command` argument) so callers that need a
    coarse "is this shell output" classification — e.g. picking the larger
    output-truncation limit — don't need a separate detection convention
    (previously each adapter had to remember to set name == "run_command").
    """
    args = _unwrap_single_dict_value(dict(arguments or {}))
    command = args.get("command")
    return isinstance(command, str) and bool(command.strip())
