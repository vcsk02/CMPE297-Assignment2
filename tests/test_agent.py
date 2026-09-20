from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

from openharness.agent import CodingAgent
from openharness.models import ChatResponse
from openharness.tools import Workspace, build_coding_tools


class FakeProvider:
    def __init__(self) -> None:
        self.calls = 0

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]],
        temperature: float = 0.1,
    ) -> ChatResponse:
        self.calls += 1
        if self.calls == 1:
            return ChatResponse(
                message={
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {
                                "name": "write_file",
                                "arguments": '{"path":"answer.txt","content":"done"}',
                            },
                        }
                    ],
                },
                finish_reason="tool_calls",
            )
        return ChatResponse(
            message={"role": "assistant", "content": "Implemented and verified the change."},
            finish_reason="stop",
        )


class AgentTests(unittest.TestCase):
    def test_agent_executes_tool_then_returns_final_answer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = Workspace(root)
            tools = build_coding_tools(workspace, auto_approve=True)
            provider = FakeProvider()
            result = CodingAgent(
                provider,
                tools,
                workspace=root,
                max_steps=3,
            ).run("Create answer.txt")
            self.assertEqual(provider.calls, 2)
            self.assertEqual(result.steps, 2)
            self.assertEqual((root / "answer.txt").read_text(), "done")
            self.assertIn("verified", result.final_text)


if __name__ == "__main__":
    unittest.main()
