"""Configuration loading for the coding harness.

The project intentionally avoids a dotenv dependency. A local ``.env`` file is
loaded only for convenience; real deployments should prefer environment
variables or a secret manager.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(start: Path | None = None) -> None:
    """Load simple KEY=VALUE pairs without overwriting existing variables."""

    directory = (start or Path.cwd()).resolve()
    candidates = [directory / ".env", *directory.parents]
    for candidate in candidates:
        if not candidate.is_file():
            continue
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)
        return


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


@dataclass(frozen=True)
class Settings:
    """Runtime settings for one harness run."""

    api_key: str
    model: str
    base_url: str
    http_referer: str | None
    app_title: str | None
    max_steps: int
    request_timeout: int
    max_file_bytes: int
    max_command_seconds: int

    @classmethod
    def from_env(cls, env_dir: Path | None = None) -> "Settings":
        _load_dotenv(env_dir)
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        return cls(
            api_key=api_key,
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            http_referer=os.getenv("OPENROUTER_HTTP_REFERER") or None,
            app_title=os.getenv("OPENROUTER_APP_TITLE") or None,
            max_steps=_int_env("HARNESS_MAX_STEPS", 12),
            request_timeout=_int_env("HARNESS_REQUEST_TIMEOUT", 120),
            max_file_bytes=_int_env("HARNESS_MAX_FILE_BYTES", 200_000),
            max_command_seconds=_int_env("HARNESS_MAX_COMMAND_SECONDS", 30),
        )
