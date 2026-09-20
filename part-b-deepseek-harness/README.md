# Part B — DeepSeek Harness plugin composition

Part B installs and customizes the official DeepSeek Harness. The deliverable
uses the standard coding preset plus a local Cordis overlay that adds two
plugins written from scratch.

## Composition

| Plugin | Origin | Purpose |
|---|---|---|
| `@deepseek-ai/dsh-tool-fs` | Official | Read, write, and edit files |
| `@deepseek-ai/dsh-tool-fs-search` | Official | Search project files |
| `@deepseek-ai/dsh-tool-todo` | Official | Track structured task progress |
| `@deepseek-ai/dsh-tool-web` | Official | Web retrieval tools |
| `@deepseek-ai/dsh-tool-ask-user` | Official | Ask structured user questions |
| `part-b-session-inspector` | Built from scratch | Prove the custom plugin is loaded |
| `part-b-prompt-linter` | Built from scratch | Reject vague tasks before execution |

The first five plugins are supplied by the official standard coding preset. The
generated patch adds the final two without modifying the upstream harness.

DeepSeek Harness describes itself as an everything-is-a-plugin architecture and
documents a plugin as a module exporting `apply(ctx)`. The custom modules follow
that contract and register model-callable tools through `ctx.tools`.

## Requirements

The official project currently documents Node.js 18 or newer, npm/pnpm, and Git
for a source checkout. Use Node 20+ when possible.

## Offline demo

This demo does not require a DeepSeek API key:

```bash
cd part-b-deepseek-harness
npm run demo
npm run generate:patch
```

The demo imports the two real plugin modules, mounts them on a minimal fake
`ctx.tools` registry, calls both tools, and asserts one rejected and one
accepted prompt.

## Live DeepSeek Harness setup

Clone and build the official harness separately:

```bash
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness
pnpm install
pnpm run build
```

Generate the overlay from this assignment repository:

```bash
cd ../CMPE297-Assignment2/part-b-deepseek-harness
npm run generate:patch
```

Start the Web UI from the DeepSeek Harness checkout:

```bash
pnpm dsh web \
  --patch ../CMPE297-Assignment2/part-b-deepseek-harness/patches/part-b.generated.cordis.yml
```

On Windows PowerShell, use the same command as one line if the line-continuation
character is inconvenient:

```powershell
pnpm dsh web --patch ..\CMPE297-Assignment2\part-b-deepseek-harness\patches\part-b.generated.cordis.yml
```

Configure the model provider through the Harness settings UI before running a
model task. The plugin-load and offline demonstrations do not expose or require
credentials.

## Creator-mode demonstration

Use the prompts in [`prompts/demo-prompts.md`](prompts/demo-prompts.md). The
combined prompt demonstrates a creator-style workflow: inspect the composition,
validate the task with the linter, create a new plugin, and verify it. Capture
the Web UI trajectory and terminal output for the required video.

## Safety and scope

The custom tools are deliberately deterministic and read-only. The official
filesystem, terminal, and web plugins may have broader capabilities depending
on the selected Harness profile and permissions. Review the Harness safety
notice before enabling shell or network tools, and use a disposable demo
workspace for the recording.

## References

- [DeepSeek Harness source repository](https://github.com/deepseek-ai/deepseek-harness)
- [Official installation README](https://github.com/deepseek-ai/deepseek-harness/blob/master/README.md)
- [Official first-plugin tutorial](https://deepseek-harness.github.io/deepseek-harness/en/develop/basic/)
