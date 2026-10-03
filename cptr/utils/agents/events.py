"""Normalized event types emitted by coding agent adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentTextDelta:
    text: str


@dataclass
class AgentReasoningDelta:
    text: str


@dataclass
class AgentToolUpdate:
    call_id: str
    status: str
    name: str | None = None
    arguments: dict[str, Any] | None = None
    output: str | None = None
    # Human-friendly display name, kept separate from `name` (a coarse
    # category — e.g. "run_command" selects the output-truncation limit in
    # chat_task.py) so adapters stop smuggling it into arguments["title"].
    title: str | None = None


@dataclass
class AgentToolOutputDelta:
    call_id: str
    delta: str
    stream_kind: str = "tool_output"
    replace: bool = False


@dataclass
class AgentDone:
    usage: dict[str, Any] | None = None
    resume_state: dict[str, Any] | None = None


@dataclass
class AgentError:
    message: str


AgentEvent = (
    AgentTextDelta
    | AgentReasoningDelta
    | AgentToolUpdate
    | AgentToolOutputDelta
    | AgentDone
    | AgentError
)
