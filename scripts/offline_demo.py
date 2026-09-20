"""Run the complete tool loop without spending an API request.

This script is useful for the repository walkthrough and CI smoke tests. The
real CLI uses the identical CodingAgent loop with OpenRouterClient.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from openharness.agent import CodingAgent
from openharness.models import ChatResponse
from openharness.tools import Workspace, build_coding_tools


class DemoProvider:
    def __init__(self) -> None:
        self.turn = 0

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]],
        temperature: float = 0.1,
    ) -> ChatResponse:
        self.turn += 1
        if self.turn == 1:
            return ChatResponse(
                message={
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "demo-call-1",
                            "type": "function",
                            "function": {
                                "name": "write_file",
                                "arguments": '{"path":"demo.txt","content":"Harness tool call worked\\n"}',
                            },
                        }
                    ],
                },
                finish_reason="tool_calls",
            )
        if self.turn == 2:
            return ChatResponse(
                message={
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "demo-call-2",
                            "type": "function",
                            "function": {
                                "name": "run_command",
                                "arguments": '{"command":"python -c \\"print(open(\\\"demo.txt\\\").read().strip())\\""}',
                            },
                        }
                    ],
                },
                finish_reason="tool_calls",
            )
        return ChatResponse(
            message={
                "role": "assistant",
                "content": "The harness wrote demo.txt and verified its contents with a command.",
            },
            finish_reason="stop",
        )


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        workspace = Workspace(root)
        agent = CodingAgent(
            DemoProvider(),
            build_coding_tools(workspace, auto_approve=True),
            workspace=root,
            max_steps=4,
        )
        result = agent.run("Create a file and verify it.")
        print(result.final_text)
        print(f"Created file: {(root / 'demo.txt').read_text().strip()}")
        print(f"Trajectory events: {len(agent.recorder.events)}")


if __name__ == "__main__":
    main()
