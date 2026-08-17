import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ai_task_evaluator.evaluator import TaskSpecError, evaluate_task, validate_task


class EvaluatorTests(unittest.TestCase):
    def test_weighted_scoring_and_reasons(self):
        spec = {
            "id": "demo",
            "timeout_seconds": 2,
            "checks": [
                {
                    "name": "pass",
                    "command": [sys.executable, "solution.py"],
                    "stdout_equals": "ok",
                    "weight": 75,
                },
                {
                    "name": "mismatch",
                    "command": [sys.executable, "solution.py"],
                    "stdout_equals": "not-ok",
                    "weight": 25,
                },
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "solution.py").write_text("print('ok')\n", encoding="utf-8")
            report = evaluate_task(spec, temp_dir)
        self.assertEqual(report.score, 75.0)
        self.assertTrue(report.checks[0].passed)
        self.assertIn("did not exactly match", report.checks[1].reason)

    def test_nonzero_exit_is_reported(self):
        spec = {
            "id": "exit",
            "checks": [
                {"name": "exit", "command": [sys.executable, "bad.py"], "weight": 1}
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "bad.py").write_text("raise SystemExit(3)\n", encoding="utf-8")
            report = evaluate_task(spec, temp_dir)
        self.assertEqual(report.score, 0.0)
        self.assertIn("got 3", report.checks[0].reason)

    def test_invalid_spec_is_rejected(self):
        with self.assertRaises(TaskSpecError):
            validate_task({"id": "x", "checks": []})


if __name__ == "__main__":
    unittest.main()
