from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from openharness.openrouter import OpenRouterClient


class OpenRouterClientTests(unittest.TestCase):
    @patch("openharness.openrouter.urlopen")
    def test_chat_sends_tools_and_parses_response(self, mock_urlopen) -> None:
        response = mock_urlopen.return_value.__enter__.return_value
        response.read.return_value = json.dumps(
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "hello"},
                    }
                ],
                "usage": {"total_tokens": 7},
            }
        ).encode()

        client = OpenRouterClient(
            "test-key",
            model="test/model",
            http_referer="https://example.com",
            app_title="Test Harness",
        )
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a file",
                    "parameters": {"type": "object"},
                },
            }
        ]
        result = client.chat([{"role": "user", "content": "hi"}], tools=tools)

        request = mock_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode())
        self.assertEqual(payload["model"], "test/model")
        self.assertEqual(payload["tools"], tools)
        self.assertEqual(payload["parallel_tool_calls"], False)
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")
        self.assertEqual(result.message["content"], "hello")
        self.assertEqual(result.usage["total_tokens"], 7)


if __name__ == "__main__":
    unittest.main()
