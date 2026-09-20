"""Minimal OpenRouter HTTP client.

This is deliberately implemented with the Python standard library so the
agent loop remains visible instead of being hidden behind an SDK.
"""

from __future__ import annotations

import json
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import ChatResponse


class OpenRouterError(RuntimeError):
    """Raised when OpenRouter cannot produce a valid chat response."""


class OpenRouterClient:
    """OpenAI-compatible client for OpenRouter chat completions."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str,
        base_url: str = "https://openrouter.ai/api/v1",
        http_referer: str | None = None,
        app_title: str | None = None,
        timeout: int = 120,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.http_referer = http_referer
        self.app_title = app_title
        self.timeout = timeout

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: Iterable[dict[str, Any]] = (),
        temperature: float = 0.1,
    ) -> ChatResponse:
        """Send one non-streaming chat request and normalize its response."""

        tool_list = list(tools)
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
            "parallel_tool_calls": False,
        }
        # OpenRouter requires the same tool schema on the follow-up request
        # after a tool call, so always include the field, even when empty.
        payload["tools"] = tool_list
        if tool_list:
            payload["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.app_title:
            headers["X-Title"] = self.app_title

        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw_body = response.read().decode("utf-8")
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise OpenRouterError(f"OpenRouter HTTP {exc.code}: {details[:1000]}") from exc
        except URLError as exc:
            raise OpenRouterError(f"Could not reach OpenRouter: {exc.reason}") from exc
        except TimeoutError as exc:
            raise OpenRouterError("OpenRouter request timed out") from exc

        try:
            data = json.loads(raw_body)
            choice = data["choices"][0]
            message = choice["message"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise OpenRouterError(f"Invalid OpenRouter response: {raw_body[:1000]}") from exc

        return ChatResponse(
            message=message,
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage", {}),
            raw=data,
        )
