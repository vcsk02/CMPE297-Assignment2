"""Bounded autoresearch loop for the Part C DeepSeek Harness plugin."""

from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path

from train import Config, train_and_evaluate


OBJECTIVE = "minimize_validation_mse"
BASELINE = Config(feature_degree=1, learning_rate=0.03, epochs=20, l2=0.1)
CANDIDATES = [
    Config(feature_degree=1, learning_rate=0.03, epochs=40, l2=0.1),
    Config(feature_degree=2, learning_rate=0.01, epochs=80, l2=0.001),
    Config(feature_degree=2, learning_rate=0.03, epochs=80, l2=0.001),
    Config(feature_degree=2, learning_rate=0.08, epochs=80, l2=0.001),
    Config(feature_degree=2, learning_rate=0.03, epochs=120, l2=0.01),
    Config(feature_degree=2, learning_rate=0.015, epochs=160, l2=0.001),
    Config(feature_degree=2, learning_rate=0.05, epochs=120, l2=0.005),
    Config(feature_degree=1, learning_rate=0.08, epochs=120, l2=0.01),
]


def run_search(seed: int, max_trials: int) -> dict:
    baseline = train_and_evaluate(BASELINE, seed)
    trials = []
    best = baseline
    for index, config in enumerate(CANDIDATES[:max_trials], start=1):
        result = train_and_evaluate(config, seed)
        result["trial"] = index
        result["accepted"] = result["validationMse"] < best["validationMse"]
        if result["accepted"]:
            best = result
        trials.append(result)

    improvement = (baseline["validationMse"] - best["validationMse"]) / baseline["validationMse"]
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + f"-{uuid.uuid4().hex[:8]}"
    return {
        "runId": run_id,
        "benchmark": "synthetic-nonlinear-regression",
        "objective": OBJECTIVE,
        "seed": seed,
        "budget": {
            "maxTrials": max_trials,
            "evaluatedTrials": len(trials),
            "candidatePool": len(CANDIDATES),
        },
        "baseline": baseline,
        "trials": trials,
        "best": best,
        "improvement": round(improvement, 8),
        "stoppingReason": "trial_budget_exhausted",
        "safety": {
            "externalNetwork": False,
            "arbitraryCodeExecution": False,
            "maxTrials": 8,
            "fixedDatasetGeneration": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-trials", type=int, default=5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "results")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    args = parser.parse_args()
    if not 1 <= args.max_trials <= 8:
        parser.error("--max-trials must be between 1 and 8")
    if not 0 <= args.seed <= 999999:
        parser.error("--seed must be between 0 and 999999")

    report = run_search(seed=args.seed, max_trials=args.max_trials)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    artifact = args.output_dir / f"run-{report['runId']}.json"
    report["artifactPath"] = artifact.as_posix()
    artifact.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report))
    else:
        print(f"Run: {report['runId']}")
        print(f"Baseline validation MSE: {report['baseline']['validationMse']:.6f}")
        print(f"Best validation MSE: {report['best']['validationMse']:.6f}")
        print(f"Improvement: {report['improvement'] * 100:.2f}%")
        print(f"Artifact: {report['artifactPath']}")


if __name__ == "__main__":
    main()
