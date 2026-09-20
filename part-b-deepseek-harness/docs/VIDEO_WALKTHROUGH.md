# Part B video walkthrough

Target length: 8–12 minutes. Keep API keys and personal credentials off camera.

## 1. Explain the objective

DeepSeek Harness is an open-source agent harness built around an
everything-is-a-plugin architecture. Part B demonstrates composition rather
than forking the harness: the standard coding preset contributes five official
plugins, and a local overlay contributes two plugins written from scratch.

## 2. Show the seven-plugin composition

Explain the roles:

1. `@deepseek-ai/dsh-tool-fs` — read/write/edit project files.
2. `@deepseek-ai/dsh-tool-fs-search` — search files.
3. `@deepseek-ai/dsh-tool-todo` — maintain visible structured work.
4. `@deepseek-ai/dsh-tool-web` — web retrieval tools.
5. `@deepseek-ai/dsh-tool-ask-user` — structured user questions.
6. `part-b-session-inspector` — custom diagnostic tool.
7. `part-b-prompt-linter` — custom deterministic quality gate.

The first five are supplied by the standard preset; the last two are added by
the generated overlay.

## 3. Walk through custom plugin #1

Open `plugins/session-inspector.mjs`. Show the `name`, `inject`, `apply`, and
`ctx.tools.register` sections. Explain that it returns safe runtime facts and
does not access secrets, the network, or the filesystem.

## 4. Walk through custom plugin #2

Open `plugins/prompt-linter.mjs`. Explain the deterministic checks: minimum and
maximum length, vague language, verification criteria, and named artifact.
Show that this plugin is useful before an agent begins changing a repository.

## 5. Run the offline demo

From `part-b-deepseek-harness` run:

```bash
npm run demo
npm run generate:patch
```

Show the two registered tool names, the inspector result, weak-prompt failure,
strong-prompt success, and the final assertion.

## 6. Install and launch DeepSeek Harness

In a separate directory, use the official source checkout:

```bash
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness
pnpm install
pnpm run build
pnpm dsh web --patch ../CMPE297-Assignment2/part-b-deepseek-harness/patches/part-b.generated.cordis.yml
```

Open the local Web UI URL printed by the terminal. The startup log should show
the custom plugin modules loading. Use the Web UI's tool/trajectory surfaces to
show the tool calls and results.

## 7. Run the live prompts

Use the prompts in `prompts/demo-prompts.md`. Show the tool calls for
`inspect_harness_environment` and `lint_agent_prompt`, then open the trajectory
to demonstrate that the tool results are part of the session event stream.

## 8. Creator-mode extension

Use the combined prompt to ask the agent to create a new diagnostic plugin. The
point of the demonstration is the workflow: inspect the current composition,
validate the proposed task, create the plugin, and verify it. If the current
Web profile does not expose creator-mode UI in the installed version, show the
same plugin composition through the patch overlay and explain that the patch is
the reproducible artifact.
