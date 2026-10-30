import json
import contextlib
import io
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import doctor


ROOT = pathlib.Path(__file__).resolve().parents[1]


class DoctorCliTests(unittest.TestCase):
    def run_doctor(self, responses):
        output_dir = ROOT / ".local"
        output_dir.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output_dir) as temporary:
            receipt_path = pathlib.Path(temporary) / "receipt.json"

            def run(command, **kwargs):
                if command == ["git", "rev-parse", "HEAD"]:
                    return subprocess.CompletedProcess(command, 0, "a" * 40 + "\n", "")
                if command == ["git", "status", "--porcelain"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                return responses.pop(0)

            with patch.object(doctor.subprocess, "run", side_effect=run):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = doctor.main(["--output", str(receipt_path)])
            return code, json.loads(receipt_path.read_text(encoding="utf-8"))

    def test_all_required_commands_write_a_head_bound_passing_receipt(self):
        responses = [
            subprocess.CompletedProcess([], 0, "Configuration valid.\n", ""),
            subprocess.CompletedProcess([], 0, "Generated settings current.\n", ""),
            subprocess.CompletedProcess([], 0, "Safe-Settings config valid.\n", ""),
            subprocess.CompletedProcess([], 0, "Ran 25 tests in 0.9s\n\nOK\n", ""),
        ]
        code, receipt = self.run_doctor(responses)
        self.assertEqual(0, code)
        self.assertEqual(1, receipt["schema_version"])
        self.assertEqual("a" * 40, receipt["head_sha"])
        self.assertEqual("a" * 40, receipt["checkout_sha"])
        self.assertFalse(receipt["worktree_dirty"])
        self.assertEqual("pass", receipt["outcome"])
        self.assertEqual(
            ["configuration", "repository_settings", "safe_settings", "unit_tests"],
            [check["name"] for check in receipt["checks"]],
        )
        self.assertEqual(
            ["scripts/generate_repository_settings.py", "--check"],
            receipt["checks"][1]["command"][-2:],
        )
        self.assertTrue(all(check["status"] == "pass" for check in receipt["checks"]))
        self.assertTrue(all((ROOT / check["evidence_path"]).is_file() for check in receipt["checks"]))

    def test_skipped_test_case_is_unknown_and_blocks_a_pass(self):
        responses = [
            subprocess.CompletedProcess([], 0, "Configuration valid.\n", ""),
            subprocess.CompletedProcess([], 0, "Generated settings current.\n", ""),
            subprocess.CompletedProcess([], 0, "Safe-Settings config valid.\n", ""),
            subprocess.CompletedProcess([], 0, "Ran 25 tests in 0.9s\n\nOK (skipped=1)\n", ""),
        ]
        code, receipt = self.run_doctor(responses)
        self.assertEqual(2, code)
        self.assertEqual("unknown", receipt["outcome"])
        self.assertEqual("unknown", receipt["checks"][3]["status"])
        self.assertIn("skipped", receipt["checks"][3]["reason"])

    def test_zero_test_run_is_unknown_even_when_unittest_exits_zero(self):
        responses = [
            subprocess.CompletedProcess([], 0, "Configuration valid.\n", ""),
            subprocess.CompletedProcess([], 0, "Generated settings current.\n", ""),
            subprocess.CompletedProcess([], 0, "Safe-Settings config valid.\n", ""),
            subprocess.CompletedProcess([], 0, "Ran 0 tests in 0.0s\n\nOK\n", ""),
        ]
        code, receipt = self.run_doctor(responses)
        self.assertEqual(2, code)
        self.assertEqual("unknown", receipt["outcome"])
        self.assertIn("zero tests", receipt["checks"][3]["reason"])

    def test_failed_check_still_writes_receipt_and_returns_failure(self):
        responses = [
            subprocess.CompletedProcess([], 1, "configuration invalid\n", ""),
            subprocess.CompletedProcess([], 0, "Generated settings current.\n", ""),
            subprocess.CompletedProcess([], 0, "Safe-Settings config valid.\n", ""),
            subprocess.CompletedProcess([], 0, "Ran 25 tests in 0.9s\n\nOK\n", ""),
        ]
        code, receipt = self.run_doctor(responses)
        self.assertEqual(1, code)
        self.assertEqual("fail", receipt["outcome"])
        self.assertEqual("fail", receipt["checks"][0]["status"])
        self.assertTrue((ROOT / receipt["checks"][0]["evidence_path"]).is_file())

    def test_failing_unittest_process_stays_fail_when_summary_is_missing(self):
        responses = [
            subprocess.CompletedProcess([], 0, "Configuration valid.\n", ""),
            subprocess.CompletedProcess([], 0, "Generated settings current.\n", ""),
            subprocess.CompletedProcess([], 0, "Safe-Settings config valid.\n", ""),
            subprocess.CompletedProcess([], 1, "", "test failure traceback\n"),
        ]
        code, receipt = self.run_doctor(responses)
        self.assertEqual(1, code)
        self.assertEqual("fail", receipt["outcome"])
        self.assertEqual("fail", receipt["checks"][3]["status"])
        self.assertIn("exited with code 1", receipt["checks"][3]["reason"])

    def test_pull_request_receipt_separates_source_and_checkout_sha(self):
        responses = [
            subprocess.CompletedProcess([], 0, "Configuration valid.\n", ""),
            subprocess.CompletedProcess([], 0, "Generated settings current.\n", ""),
            subprocess.CompletedProcess([], 0, "Safe-Settings config valid.\n", ""),
            subprocess.CompletedProcess([], 0, "Ran 25 tests in 0.9s\n\nOK\n", ""),
        ]
        with patch.dict("os.environ", {
            "SAMWISE_GITHUB_SHA": "b" * 40,
            "SAMWISE_PR_HEAD_SHA": "c" * 40,
            "SAMWISE_PR_BASE_SHA": "d" * 40,
            "SAMWISE_PR_NUMBER": "42",
        }):
            code, receipt = self.run_doctor(responses)
        self.assertEqual(0, code)
        self.assertEqual("c" * 40, receipt["head_sha"])
        self.assertEqual("a" * 40, receipt["checkout_sha"])
        self.assertEqual("b" * 40, receipt["github"]["workflow_sha"])
        self.assertEqual("d" * 40, receipt["github"]["pull_request_base_sha"])


if __name__ == "__main__":
    unittest.main()
