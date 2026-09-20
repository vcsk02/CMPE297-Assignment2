# Part A video walkthrough script

Target length: 8–12 minutes. Keep the API key hidden; show `.env.example`, not
the real `.env` file.

## 1. Problem and design — 60 seconds

Explain that the model is not the harness. The harness supplies the stateful
conversation, exposes a controlled tool interface, executes tools locally, and
returns evidence to the model. The design is:

```text
task → OpenRouter → tool call → approval/safety gate → local result → OpenRouter → answer
```

## 2. Repository tour — 60 seconds

Show:

- `src/openharness/openrouter.py`: standard-library OpenRouter client
- `src/openharness/tools.py`: workspace tools and safety boundary
- `src/openharness/agent.py`: bounded agent loop
- `src/openharness/trace.py`: JSONL trajectory recording
- `src/openharness/cli.py`: command-line composition
- `tests/`: offline behavioral checks

## 3. OpenRouter client — 90 seconds

Open `openrouter.py`. Point out that the request uses:

- `Authorization: Bearer ...`
- `POST /chat/completions`
- `messages`
- `tools`
- `parallel_tool_calls: false` for an easy-to-follow deterministic demo

Explain that the same tool schema is sent on every turn, including the turn
after a tool result.

## 4. Safety boundary — 120 seconds

Open `tools.py` and demonstrate:

1. `Workspace.resolve("../outside.txt")` is rejected.
2. `write_file` and `run_command` require approval by default.
3. destructive command patterns are rejected before shell execution.
4. commands execute with the workspace as their current directory.

Mention that this is a teaching boundary, not a complete security sandbox;
production execution should use a container or isolated runner.

## 5. Agent loop — 120 seconds

Open `agent.py` and explain:

1. The system prompt and user task become the initial messages.
2. A model response is appended to history.
3. Each `tool_call` is dispatched by name through `ToolRegistry`.
4. The JSON result becomes a `role=tool` message.
5. The model receives the expanded history and either calls another tool or
   returns the final answer.
6. `max_steps` prevents an unbounded loop.

## 6. Offline execution — 90 seconds

Run:

```bash
PYTHONPATH=src python scripts/offline_demo.py
PYTHONPATH=src python -m unittest discover -s tests -v
```

Show the output proving that the fake provider caused a file write, executed a
verification command, and reached a final answer. Explain that the fake
provider replaces only the network client; the real `CodingAgent` and tools are
unchanged.

## 7. Live OpenRouter execution — 120 seconds

Run the example against a small project:

```bash
coding-harness \
  --workspace examples/demo_project \
  "Inspect this project. Add a subtract(left, right) function to calculator.py, add unit tests for all three operations, run the tests, and summarize the result."
```

Approve each `write_file` and `run_command` request on camera. Then show the
new files, the test output, and the JSONL trace under `.harness/traces/`.

For a controlled classroom demo, `--auto-approve` can be used, but explain
that it bypasses the interactive approval prompt and should not be the default
for untrusted tasks.

## 8. Closing — 30 seconds

Summarize what was implemented from scratch: provider adapter, tool schema,
execution loop, safety controls, tests, and trajectory evidence. State the
next improvement: containerized execution and a patch-based editor.
