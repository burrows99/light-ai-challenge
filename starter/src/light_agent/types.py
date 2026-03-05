"""
Shared types for the Light Agent Runtime.

These are provided as a starting point. You're welcome to extend, modify,
or replace them entirely with your own type system (dataclasses, Pydantic,
TypedDict, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Tool execution types
# ---------------------------------------------------------------------------

class ToolCallStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class ToolCall:
    """A request from the LLM to execute a specific tool."""

    name: str
    arguments: dict[str, Any]
    call_id: str | None = None  # Optional ID to correlate calls with results


@dataclass
class ToolResult:
    """The outcome of executing a tool."""

    tool_name: str
    status: ToolCallStatus
    result: Any | None = None
    error: str | None = None
    duration_ms: float | None = None


# ---------------------------------------------------------------------------
# Conversation / message types
# ---------------------------------------------------------------------------

@dataclass
class Message:
    """
    A single message in the agent's conversation history.

    role:
        - "user"      — the original user request
        - "assistant"  — an LLM response (may contain tool_calls and/or content)
        - "tool"       — the result of a tool execution
    """

    role: str
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_result: ToolResult | None = None


# ---------------------------------------------------------------------------
# Execution trace
# ---------------------------------------------------------------------------

@dataclass
class ExecutionTrace:
    """
    Structured record of a single agent run.

    This is your observability output. A good trace lets you understand
    exactly what happened — which tools were called, in what order, what
    the LLM decided at each step, and how long it all took.
    """

    user_request: str = ""
    steps: list[Message] = field(default_factory=list)
    final_response: str | None = None
    tool_calls_made: int = 0
    total_duration_ms: float | None = None
    error: str | None = None
