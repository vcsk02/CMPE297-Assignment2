# Part C demonstration prompts

Use these prompts in the DeepSeek Harness Web UI after applying the generated
Cordis overlay.

## 1. Inspect the capability

> Run one bounded autoresearch experiment with five trials and seed 7. Report the baseline validation MSE, every candidate configuration, the best configuration, the percentage improvement, and the saved artifact path.

## 2. Demonstrate reproducibility

> Run the autoresearch experiment twice with seed 7 and the same five-trial budget. Verify that the benchmark produces the same baseline and best validation MSE both times.

## 3. Demonstrate the safety budget

> Run autoresearch with the largest allowed trial budget, seed 11, and explain why the tool stops after the bounded number of candidates instead of continuing indefinitely.

## 4. Creator-mode workflow

> Inspect the Part C autoresearch plugin, run a five-trial experiment, summarize the best configuration and validation improvement, then create a short Markdown report in the workspace that includes the objective, baseline, trial table, best result, safety limits, and artifact path. Verify that the report exists and is readable.
