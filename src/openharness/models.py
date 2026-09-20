"""Small data structures shared by the client, tools, and agent loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatResponse:
    """Normalized OpenRouter chat-completion response."""

    message: dict[str, Any]
    finish_reason: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
