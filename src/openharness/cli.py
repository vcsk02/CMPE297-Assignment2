"""Command-line interface for the coding harness."""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

from .agent import CodingAgent
from .config import Settings
from .openrouter import OpenRouterClient
from .tools import Workspace, build_coding_tools
from .trace import TraceRecorder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coding-harness",
        description="Run a bounded OpenRouter coding agent inside a workspace.",
    )
    parser.add_argument("task", nargs="?", help="Task for the coding agent")
    parser.add_argument("--task-file", type=Path, help="Read the task from a UTF-8 text file")
    parser.add_argument("--workspace", type=Path, default=Path("."))
    parser.add_argument("--model", help="Override OPENROUTER_MODEL")
    parser.add_argument("--max-steps", type=int, help="Maximum model/tool turns")
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically approve write_file and run_command tool calls",
    )
    parser.add_argument(
        "--trace-path",
        type=Path,
        help="Optional JSONL path for the run trajectory",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.task and args.task_file:
        print("Use either a positional task or --task-file, not both.", file=sys.stderr)
        return 2
    try:
        task = args.task
        if args.task_file:
            task = args.task_file.read_text(encoding="utf-8")
        if not task:
            task = input("Task for the coding agent: ").strip()
        if not task:
            print("A task is required.", file=sys.stderr)
            return 2

        settings = Settings.from_env(Path.cwd())
        workspace = Workspace(
            args.workspace,
            max_file_bytes=settings.max_file_bytes,
            max_command_seconds=settings.max_command_seconds,
        )
        client = OpenRouterClient(
            settings.api_key,
            model=args.model or settings.model,
            base_url=settings.base_url,
            http_referer=settings.http_referer,
            app_title=settings.app_title,
            timeout=settings.request_timeout,
        )
        trace_path = args.trace_path
        if trace_path is None:
            trace_path = workspace.root / ".harness" / "traces" / f"{uuid.uuid4().hex[:12]}.jsonl"
        recorder = TraceRecorder(trace_path)
        registry = build_coding_tools(workspace, auto_approve=args.auto_approve)
        agent = CodingAgent(
            client,
            registry,
            workspace=workspace.root,
            max_steps=args.max_steps or settings.max_steps,
            recorder=recorder,
        )
        print(f"Workspace: {workspace.root}")
        print(f"Model: {client.model}")
        print(f"Trace: {trace_path}")
        print("Running agent...\n")
        result = agent.run(task)
        print(result.final_text)
        print(f"\nCompleted in {result.steps} step(s).")
        return 0
    except (ValueError, OSError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # CLI boundary: keep errors readable for a demo.
        print(f"Harness error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
