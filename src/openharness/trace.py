"""Append-only JSONL trajectory recording for reproducible demos."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any


class TraceRecorder:
    """Record requests, tool calls, results, and final output as JSONL."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.session_id = uuid.uuid4().hex[:12]
        self.events: list[dict[str, Any]] = []
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {
            "session_id": self.session_id,
            "timestamp": time.time(),
            "type": event_type,
            **payload,
        }
        self.events.append(event)
        if self.path:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
