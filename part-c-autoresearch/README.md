# Part C — Bounded autoresearch ML harness

Part C adds a custom DeepSeek Harness plugin that runs a small, reproducible
ML autoresearch loop. The agent can request an experiment, but the plugin—not
the model—controls the objective, candidate pool, trial budget, Python entry
point, timeout, and result artifact.

## What is implemented

| Component | Purpose |
|---|---|
| `benchmark/train.py` | Generates a deterministic nonlinear regression dataset and trains one candidate configuration. |
| `benchmark/autoresearch.py` | Evaluates a baseline, tests a bounded candidate pool, and selects the lowest validation MSE. |
| `plugins/autoresearch.mjs` | DeepSeek Harness/Cordis plugin exposing `run_autoresearch_experiment`. |
| `scripts/offline-demo.mjs` | Mounts the real plugin on a fake tool registry and executes it end-to-end. |
| `tests/test_autoresearch.py` | Verifies reproducibility, improvement, budget enforcement, and report serialization. |
| `scripts/generate-patch.mjs` | Creates the absolute-path Cordis overlay for the official Harness checkout. |

## Why this qualifies as autoresearch

The loop follows a measurable research cycle:

```text
fixed benchmark → baseline → candidate configuration → train → validate
       ↑                                                     ↓
       └──────────── record result and keep the best ───────┘
```

The baseline uses a degree-one model. Candidates can add degree-two polynomial
features and change learning rate, epochs, and regularization. Each trial is
evaluated on the same deterministic train/validation split. The objective is
`minimize_validation_mse`.

## Requirements

- Node.js 18 or newer
- Python 3.10 or newer
- No Python packages, dataset download, model API, or API key is required

## Run the complete local demo

From the assignment repository:

```powershell
cd C:\Users\vcsk0\CMPE297-Assignment2\part-c-autoresearch
npm run demo
npm test
npm run generate:patch
```

You can also run the Python runner directly:

```powershell
python benchmark\autoresearch.py --max-trials 5 --seed 7
```

The experiment report is saved under `results/`. Result files are intentionally
ignored by Git because they are generated evidence; the source, tests, and
video instructions are committed.

## DeepSeek Harness integration

Generate the local overlay:

```powershell
npm run generate:patch
```

From the official DeepSeek Harness checkout, start the Web UI. Adjust the
relative path if your two folders are located elsewhere:

```powershell
pnpm dsh web --patch ..\CMPE297-Assignment2\part-c-autoresearch\patches\part-c.generated.cordis.yml
```

The overlay loads `plugins/autoresearch.mjs` into the standard agent. Use the
prompts in [`prompts/demo-prompts.md`](prompts/demo-prompts.md), then capture
the tool call, structured result, trajectory, and generated JSON artifact for
the video.

## Safety and reproducibility

- `maxTrials` is restricted to 1–8; the baseline is always separate.
- The Python process is terminated after 30 seconds by the plugin.
- The seed and candidate pool are explicit and deterministic.
- The tool accepts no arbitrary shell command, filesystem path, Python code, or
  model-supplied objective.
- The benchmark has no network access and creates only its own result artifact.
- The result records baseline, every trial, acceptance decisions, best result,
  objective, budget, seed, and safety metadata.

This is a teaching harness. Production autoresearch needs stronger process
isolation, signed inputs, resource quotas, dependency capture, and an external
held-out evaluation set.

## Video walkthrough

See [`docs/VIDEO_WALKTHROUGH.md`](docs/VIDEO_WALKTHROUGH.md) for the complete
recording script.
