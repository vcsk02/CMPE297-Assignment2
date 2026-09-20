"""The complete model/tool/model agentic loop."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .models import ChatResponse
from .trace import TraceRecorder
from .tools import ToolRegistry


class ChatProvider(Protocol):
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]],
        temperature: float = 0.1,
    ) -> ChatResponse: ...


SYSTEM_PROMPT = """You are a careful software-engineering coding agent.

Your job is to complete the user's task inside the supplied workspace.

Operating rules:
1. Inspect the project before editing it. Use list_files, read_file, or search_files.
2. Work only inside the workspace boundary. Never access secrets or unrelated paths.
3. Make the smallest coherent change that satisfies the task.
4. Use write_file for edits and run_command for tests or checks. Ask for approval is handled by the harness.
5. After changing code, run the most relevant tests or a safe verification command.
6. Do not claim a test passed unless the tool output shows it passed.
7. Finish with a concise summary, changed files, and verification results.

The workspace root is: {workspace}
"""


@dataclass
class AgentResult:
    final_text: str
    steps: int
    messages: list[dict[str, Any]]
    trace_path: Path | None = None


class CodingAgent:
    """A bounded tool-calling loop with inspectable trajectory events."""

    def __init__(
        self,
        provider: ChatProvider,
        tools: ToolRegistry,
        *,
        workspace: Path,
        max_steps: int = 12,
        recorder: TraceRecorder | None = None,
    ) -> None:
        self.provider = provider
        self.tools = tools
        self.workspace = workspace.resolve()
        self.max_steps = max_steps
        self.recorder = recorder or TraceRecorder()

    def run(self, task: str) -> AgentResult:
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(workspace=self.workspace),
            },
            {"role": "user", "content": task},
        ]
        self.recorder.record("run_started", {"task": task, "workspace": str(self.workspace)})

        for step in range(1, self.max_steps + 1):
            self.recorder.record("model_request", {"step": step, "messages": messages})
            response = self.provider.chat(messages, tools=self.tools.schemas(), temperature=0.1)
            assistant_message = dict(response.message)
            assistant_message.setdefault("role", "assistant")
            messages.append(assistant_message)
            self.recorder.record(
                "model_response",
                {
                    "step": step,
                    "message": assistant_message,
                    "finish_reason": response.finish_reason,
                    "usage": response.usage,
                },
            )

            tool_calls = assistant_message.get("tool_calls") or []
            if not tool_calls:
                final_text = _message_text(assistant_message)
                self.recorder.record("run_finished", {"steps": step, "final_text": final_text})
                return AgentResult(
                    final_text=final_text,
                    steps=step,
                    messages=messages,
                    trace_path=self.recorder.path,
                )

            for tool_call in tool_calls:
                function = tool_call.get("function", {})
                tool_name = function.get("name", "")
                arguments = function.get("arguments", "{}")
                result = self.tools.execute(tool_name, arguments)
                self.recorder.record(
                    "tool_result",
                    {
                        "step": step,
                        "tool_call_id": tool_call.get("id"),
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": result,
                    },
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", f"call-{step}"),
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        message = f"Stopped after the maximum of {self.max_steps} steps without a final answer."
        self.recorder.record("run_stopped", {"reason": "max_steps", "steps": self.max_steps})
        return AgentResult(
            final_text=message,
            steps=self.max_steps,
            messages=messages,
            trace_path=self.recorder.path,
        )


def _message_text(message: dict[str, Any]) -> str:
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "\n".join(parts).strip()
    return str(content).strip()
