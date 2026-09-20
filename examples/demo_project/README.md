# Harness demonstration project

This deliberately small project is a safe target for the live coding-agent
demo. A useful prompt is:

> Inspect this project. Add a `subtract(left, right)` function to
> `calculator.py`, add unit tests for all three operations, run the tests, and
> summarize the result.

Run the harness from the repository root with:

```bash
coding-harness \
  --workspace examples/demo_project \
  --auto-approve \
  "Inspect this project. Add a subtract(left, right) function to calculator.py, add unit tests for all three operations, run the tests, and summarize the result."
```
