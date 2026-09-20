import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmark"))

from autoresearch import BASELINE, run_search
from train import train_and_evaluate


class AutoresearchTests(unittest.TestCase):
    def test_baseline_is_reproducible(self):
        first = train_and_evaluate(BASELINE, seed=7)
        second = train_and_evaluate(BASELINE, seed=7)
        self.assertEqual(first, second)

    def test_search_improves_validation_mse(self):
        report = run_search(seed=7, max_trials=5)
        self.assertLess(report["best"]["validationMse"], report["baseline"]["validationMse"])
        self.assertEqual(len(report["trials"]), 5)
        self.assertGreater(report["improvement"], 0)

    def test_search_respects_trial_budget(self):
        report = run_search(seed=11, max_trials=2)
        self.assertEqual(report["budget"]["evaluatedTrials"], 2)
        self.assertEqual(len(report["trials"]), 2)

    def test_report_can_be_serialized(self):
        report = run_search(seed=7, max_trials=1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["objective"], "minimize_validation_mse")


if __name__ == "__main__":
    unittest.main()
