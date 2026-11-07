import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.executor import run_task


class ExecutorTests(unittest.TestCase):
    def test_clean_csv_trims_whitespace_and_creates_quality_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "input.csv"
            output = root / "output.csv"
            source.write_text("Name,Email\n  Alice  , ALICE@EXAMPLE.COM  \nBob,bob@example.com\n", encoding="utf-8")
            task = {
                "task_id": "clean-1",
                "approved": True,
                "status": "approved",
                "type": "clean_csv",
                "input_file": "input.csv",
                "output_file": "output.csv",
            }
            with patch("backend.executor.ROOT", root):
                report = run_task(task)
            self.assertEqual(report["rows_out"], 2)
            with output.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows[0]["Name"], "Alice")
            self.assertEqual(rows[0]["Email"], "ALICE@EXAMPLE.COM")
            self.assertTrue(output.with_suffix(".quality.json").is_file())

    def test_collapses_internal_whitespace(self):
        self.assertEqual(
            __import__("backend.executor", fromlist=["normalize_cell"]).normalize_cell("  Alice   Smith  "),
            "Alice Smith",
        )

    def test_deduplicates_exact_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "input.csv").write_text("id,name\n1,A\n1,A\n2,B\n", encoding="utf-8")
            task = {"type": "deduplicate_csv", "approved": True, "status": "approved", "input_file": "input.csv", "output_file": "out.csv"}
            with patch("backend.executor.ROOT", root):
                report = run_task(task)
            self.assertEqual(report["rows_in"], 3)
            self.assertEqual(report["rows_out"], 2)
            self.assertEqual(report["duplicates_removed"], 1)

    def test_rejects_csv_rows_with_extra_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "input.csv").write_text("id,name\n1,A,unexpected\n", encoding="utf-8")
            task = {
                "type": "clean_csv",
                "approved": True,
                "status": "approved",
                "input_file": "input.csv",
                "output_file": "out.csv",
            }
            with patch("backend.executor.ROOT", root):
                with self.assertRaisesRegex(ValueError, "more values than the header"):
                    run_task(task)

    def test_rejects_task_without_explicit_approval(self):
        with self.assertRaises(PermissionError):
            run_task({"type": "clean_csv", "input_file": "input.csv", "output_file": "out.csv"})

    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            from backend.executor import safe_path
            safe_path("../outside.csv")

    def test_rejects_unsupported_task_type(self):
        with self.assertRaises(ValueError):
            run_task({"type": "run_shell", "approved": True, "status": "approved", "input_file": "in.csv", "output_file": "out.csv"})

    def test_rejects_same_input_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "in.csv").write_text("a\n1\n", encoding="utf-8")
            with patch("backend.executor.ROOT", root):
                with self.assertRaises(ValueError):
                    run_task({"type": "clean_csv", "approved": True, "status": "approved", "input_file": "in.csv", "output_file": "in.csv"})


if __name__ == "__main__":
    unittest.main()
