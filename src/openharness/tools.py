"""Local tools exposed to the model and the associated safety boundary."""

from __future__ import annotations

import json
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


class ToolExecutionError(RuntimeError):
    """Raised for a tool request that cannot be completed safely."""


@dataclass
class Workspace:
    """A filesystem and process boundary rooted at one project directory."""

    root: Path
    max_file_bytes: int = 200_000
    max_command_seconds: int = 30

    def __post_init__(self) -> None:
        self.root = self.root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative_path: str) -> Path:
        """Resolve a relative path and reject workspace escape attempts."""

        if not relative_path:
            relative_path = "."
        candidate = (self.root / relative_path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ToolExecutionError(
                f"Path '{relative_path}' is outside the workspace boundary"
            ) from exc
        return candidate

    @staticmethod
    def _ignored(path: Path) -> bool:
        ignored = {".git", ".venv", "venv", "node_modules", "__pycache__", ".harness"}
        return any(part in ignored for part in path.parts)

    @staticmethod
    def _display_path(path: Path) -> str:
        """Return a stable, platform-independent path for model/tool output."""

        return path.as_posix()

    def list_files(self, path: str = ".", max_depth: int = 3) -> dict[str, Any]:
        directory = self.resolve(path)
        if not directory.is_dir():
            raise ToolExecutionError(f"Not a directory: {path}")
        base_depth = len(directory.relative_to(self.root).parts)
        files: list[dict[str, str]] = []
        for candidate in sorted(directory.rglob("*")):
            if self._ignored(candidate.relative_to(self.root)):
                continue
            depth = len(candidate.relative_to(self.root).parts) - base_depth
            if depth > max_depth:
                continue
            if candidate.is_file():
                files.append(
                    {
                        "path": self._display_path(candidate.relative_to(self.root)),
                        "type": "file",
                    }
                )
            elif candidate.is_dir() and depth == 1:
                files.append(
                    {
                        "path": self._display_path(candidate.relative_to(self.root)) + "/",
                        "type": "directory",
                    }
                )
        return {"ok": True, "root": str(self.root), "files": files}

    def read_file(
        self,
        path: str,
        start_line: int = 1,
        end_line: int | None = None,
    ) -> dict[str, Any]:
        file_path = self.resolve(path)
        if not file_path.is_file():
            raise ToolExecutionError(f"File does not exist: {path}")
        if file_path.stat().st_size > self.max_file_bytes:
            raise ToolExecutionError(
                f"File is larger than the configured limit of {self.max_file_bytes} bytes"
            )
        if start_line < 1 or (end_line is not None and end_line < start_line):
            raise ToolExecutionError("Line range is invalid")
        text = file_path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        selected = lines[start_line - 1 : end_line]
        return {
            "ok": True,
            "path": self._display_path(file_path.relative_to(self.root)),
            "start_line": start_line,
            "end_line": min(end_line or len(lines), len(lines)),
            "content": "\n".join(selected),
        }

    def write_file(self, path: str, content: str) -> dict[str, Any]:
        file_path = self.resolve(path)
        encoded = content.encode("utf-8")
        if len(encoded) > self.max_file_bytes:
            raise ToolExecutionError(
                f"Content is larger than the configured limit of {self.max_file_bytes} bytes"
            )
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return {
            "ok": True,
            "path": self._display_path(file_path.relative_to(self.root)),
            "bytes_written": len(encoded),
        }

    def search_files(self, query: str, path: str = ".", max_results: int = 20) -> dict[str, Any]:
        if not query:
            raise ToolExecutionError("Search query cannot be empty")
        directory = self.resolve(path)
        if not directory.exists():
            raise ToolExecutionError(f"Path does not exist: {path}")
        matches: list[dict[str, Any]] = []
        candidates = [directory] if directory.is_file() else directory.rglob("*")
        for candidate in candidates:
            if len(matches) >= max_results:
                break
            if not candidate.is_file() or self._ignored(candidate.relative_to(self.root)):
                continue
            try:
                if candidate.stat().st_size > self.max_file_bytes:
                    continue
                lines = candidate.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if query.lower() in line.lower():
                    matches.append(
                        {
                            "path": self._display_path(candidate.relative_to(self.root)),
                            "line": line_number,
                            "text": line[:500],
                        }
                    )
                    break
        return {"ok": True, "query": query, "matches": matches}

    def run_command(self, command: str, timeout_seconds: int | None = None) -> dict[str, Any]:
        _validate_command(command)
        timeout = min(timeout_seconds or self.max_command_seconds, self.max_command_seconds)
        try:
            completed = subprocess.run(
                command,
                cwd=self.root,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "ok": False,
                "timed_out": True,
                "command": command,
                "stdout": _clip(exc.stdout or ""),
                "stderr": _clip(exc.stderr or ""),
                "exit_code": None,
            }
        return {
            "ok": completed.returncode == 0,
            "command": command,
            "stdout": _clip(completed.stdout),
            "stderr": _clip(completed.stderr),
            "exit_code": completed.returncode,
        }


def _clip(value: str, limit: int = 6000) -> str:
    return value if len(value) <= limit else value[:limit] + "\n...[output clipped]"


def _validate_command(command: str) -> None:
    """Reject common destructive or host-escape commands before shell launch."""

    lowered = command.lower().strip()
    blocked_patterns = [
        r"(^|\s)sudo(\s|$)",
        r"\brm\s+(-[a-z]*f[a-z]*\s+)?/",  # root or absolute recursive deletion
        r"\brm\s+-[^\n]*r[^\n]*f",
        r"\bgit\s+reset\s+--hard",
        r"\bgit\s+clean\s+-[^\n]*f",
        r"\bshutdown\b|\breboot\b|\bmkfs\b|\bdd\s+if=",
        r"curl[^\n|]*\|\s*(ba)?sh",
        r"wget[^\n|]*\|\s*(ba)?sh",
        r":\(\)\s*\{",  # fork bomb
    ]
    if any(re.search(pattern, lowered) for pattern in blocked_patterns):
        raise ToolExecutionError("Command rejected by the safety policy")
    if ".." in shlex.split(command)[0:1]:
        raise ToolExecutionError("Command rejected because its executable path is unsafe")


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., dict[str, Any]]
    requires_approval: bool = False

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """Registry that translates model tool calls into local function calls."""

    def __init__(
        self,
        definitions: list[ToolDefinition],
        *,
        approval_fn: Callable[[ToolDefinition, dict[str, Any]], bool] | None = None,
    ) -> None:
        self.definitions = {definition.name: definition for definition in definitions}
        self.approval_fn = approval_fn

    def schemas(self) -> list[dict[str, Any]]:
        return [definition.schema() for definition in self.definitions.values()]

    def execute(self, name: str, arguments: dict[str, Any] | str | None) -> dict[str, Any]:
        definition = self.definitions.get(name)
        if not definition:
            return {"ok": False, "error": f"Unknown tool: {name}"}
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments or "{}")
            except json.JSONDecodeError as exc:
                return {"ok": False, "error": f"Tool arguments were not valid JSON: {exc}"}
        if not isinstance(arguments, dict):
            return {"ok": False, "error": "Tool arguments must be a JSON object"}
        if definition.requires_approval and self.approval_fn and not self.approval_fn(
            definition, arguments
        ):
            return {"ok": False, "error": f"User denied tool: {name}"}
        try:
            return definition.handler(**arguments)
        except (TypeError, ToolExecutionError, OSError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}


def build_coding_tools(
    workspace: Workspace,
    *,
    auto_approve: bool = False,
    input_fn: Callable[[str], str] = input,
) -> ToolRegistry:
    """Create the five tools used by the coding agent."""

    def approve(definition: ToolDefinition, arguments: dict[str, Any]) -> bool:
        if auto_approve:
            return True
        preview = json.dumps(arguments, ensure_ascii=False)
        try:
            answer = input_fn(f"\nApprove {definition.name}({preview[:500]})? [y/N] ")
        except EOFError:
            return False
        return answer.strip().lower() in {"y", "yes"}

    definitions = [
        ToolDefinition(
            name="list_files",
            description="List project files within the workspace boundary.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative directory path."},
                    "max_depth": {"type": "integer", "minimum": 1, "maximum": 8},
                },
                "additionalProperties": False,
            },
            handler=workspace.list_files,
        ),
        ToolDefinition(
            name="read_file",
            description="Read a text file before proposing or making a change.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path."},
                    "start_line": {"type": "integer", "minimum": 1},
                    "end_line": {"type": "integer", "minimum": 1},
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            handler=workspace.read_file,
        ),
        ToolDefinition(
            name="search_files",
            description="Find the first matching line in text files under the workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "path": {"type": "string"},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            handler=workspace.search_files,
        ),
        ToolDefinition(
            name="write_file",
            description="Create or replace a UTF-8 text file inside the workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
            handler=workspace.write_file,
            requires_approval=True,
        ),
        ToolDefinition(
            name="run_command",
            description="Run a project command from the workspace root and return its output.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 30},
                },
                "required": ["command"],
                "additionalProperties": False,
            },
            handler=workspace.run_command,
            requires_approval=True,
        ),
    ]
    return ToolRegistry(definitions, approval_fn=approve)
