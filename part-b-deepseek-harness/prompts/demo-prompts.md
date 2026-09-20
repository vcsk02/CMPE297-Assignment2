# Part B demo prompts

## Prompt 1 — prove the custom plugin is loaded

```text
Call inspect_harness_environment and explain what the result proves about the
loaded Part B plugin. Do not read secrets or modify files.
```

Expected evidence: a tool call named `inspect_harness_environment` and a result
containing the plugin name, Node version, operating system, and working
directory.

## Prompt 2 — reject an underspecified task

```text
Use lint_agent_prompt to review: "Make it better quickly."
```

Expected evidence: `ok: false` and issues about missing scope and verification.

## Prompt 3 — accept a verifiable task

```text
Use lint_agent_prompt to review this task before doing anything else: Add a
prompt-linter plugin to this repository, write a deterministic unit test, run
the test, and report the expected verification output.
```

Expected evidence: `ok: true`, a word count, and an empty issue list.

## Prompt 4 — combined creator-mode demonstration

```text
Create a new diagnostic plugin named release-checker. First call
inspect_harness_environment, then use lint_agent_prompt to validate the plugin
task, and only after the prompt passes create the plugin. Explain the tool
schema and show the verification command.
```

For the video, show the trajectory: the two custom tools are visible in the
tool catalog, the linter produces a deterministic result, and the agent can
continue with the validated task.
