# Part A — OpenRouter Coding Harness

This repository contains a small coding agent implemented from scratch. It
uses OpenRouter for model inference and a local Python tool loop for inspecting,
editing, and testing a project.

The core loop is intentionally easy to explain:

```text
user task → model response → tool call → local tool result → model response → final answer
```

The model never directly changes files. It proposes a function call, and the
harness validates and executes that call inside a configured workspace.

## Features

- OpenRouter-compatible chat-completions client implemented with `urllib`.
- Tool-calling loop with a bounded maximum number of steps.
- `list_files`, `read_file`, `search_files`, `write_file`, and `run_command` tools.
- Workspace path traversal protection.
- Approval prompts for file writes and command execution.
- Blocklist for common destructive commands.
- JSONL trajectory traces for code-walkthrough videos and debugging.
- Offline fake-provider demo and unit tests that do not require an API key.

## Setup

Use Python 3.10 or newer:

```bash
cd part-a-coding-harness
python -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -e .
cp .env.example .env
```

Put an OpenRouter key in `.env`:

```dotenv
OPENROUTER_API_KEY=your-key
OPENROUTER_MODEL=openai/gpt-4o-mini
```

The model can be changed without code edits. Select a model available in your
OpenRouter account that supports tool/function calling.

## Offline verification

The offline demo exercises the same agent loop without making a network call:

```bash
PYTHONPATH=src python scripts/offline_demo.py
```

Run the test suite:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Live coding-agent demo

The example project is intentionally small:

```bash
coding-harness \
  --workspace examples/demo_project \
  --auto-approve \
  "Inspect this project. Add a subtract(left, right) function to calculator.py, add unit tests for all three operations, run the tests, and summarize the result."
```

For a recorded presentation, omit `--auto-approve` and approve each write or
command interactively. The default trace is saved under:

```text
examples/demo_project/.harness/traces/<run-id>.jsonl
```

`--auto-approve` is convenient for a controlled demo only. In normal use,
review proposed writes and commands before accepting them.

## Project walkthrough

### `src/openharness/openrouter.py`

Builds a POST request to `/chat/completions`, sends the bearer token and
optional attribution headers, includes the tool schema, and normalizes the
first response choice into `ChatResponse`.

### `src/openharness/tools.py`

Defines the workspace boundary and the tools. Every path is resolved and checked
with `Path.relative_to`, so `../` cannot escape the workspace. Mutating tools
are marked `requires_approval=True` and are gated by the registry.

### `src/openharness/agent.py`

Maintains the conversation history. When the model returns `tool_calls`, each
call is executed locally and appended as a `role=tool` message. The next model
request receives the result and can continue reasoning. The loop ends on a
normal assistant message or the configured step limit.

### `src/openharness/trace.py`

Records the task, model requests, model responses, tool results, and completion
as append-only JSONL. This makes the trajectory easy to inspect during the
video demonstration.

### `src/openharness/cli.py`

Connects configuration, the workspace, the OpenRouter client, the tool registry,
the trace recorder, and the agent into one executable command.

## Suggested YouTube walkthrough

1. State the problem: a language model can propose code, but a harness must
   control tools, state, execution, and evidence.
2. Show the repository tree and `.env` setup without revealing the API key.
3. Walk through `OpenRouterClient.chat` and point out the tool schema.
4. Walk through `Workspace.resolve` and the approval gate.
5. Walk through the loop in `CodingAgent.run`.
6. Run `python scripts/offline_demo.py` and open the resulting trajectory in
   the terminal.
7. Run the live example task against `examples/demo_project`.
8. Show the changed files and test output.
9. Explain the limits: command policy is a defense-in-depth guard, not a full
   sandbox; production use should use containers or a dedicated runner.

## Design choices and limitations

This is a teaching harness rather than a production execution service. It uses
standard-library HTTP and shell execution to keep the mechanics visible. A
production version should add container isolation, stronger command policies,
secret redaction, structured patch application, retries, cost limits, and
provider/model evaluation.

## References

- [OpenRouter quickstart](https://openrouter.ai/docs/quickstart)
- [OpenRouter client tool calling](https://openrouter.ai/docs/guides/features/tool-calling)
- [OpenRouter Python SDK chat documentation](https://openrouter.ai/docs/client-sdks/python/sdks/chat/README)
