import json
import pathlib
import sys
import tempfile
import unittest
import psutil

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "adapters"))
from dispatch import DispatchError, run, run_with_retry

FAKE = pathlib.Path(__file__).resolve().parents[1] / "adapters" / "fake_provider.py"


class DispatchTests(unittest.TestCase):
    def test_scenarios_and_retry_limits(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            for scenario, expected in [("valid", "success"), ("malformed_json", "unknown"),
                                       ("auth_error", "failed"), ("quota_error", "failed"),
                                       ("partial_exit_zero", "partial"), ("stale_artifact", "unknown"),
                                       ("uncertain_side_effect", "failed"),
                                       ("unknown_failure", "failed"),
                                       ("success_exit_nonzero", "failed"),
                                       ("failed_after_usage", "failed")]:
                run_id = "run-" + scenario
                argv = [sys.executable, str(FAKE), scenario, run_id]
                if scenario == "stale_artifact":
                    stale = root / "old.txt"
                    stale.write_text("old", encoding="utf-8")
                    argv.append(str(stale))
                result = run(argv, root, root / scenario, "literal ' \" `$(Get-Secret)", timeout_seconds=5, run_id=run_id)
                self.assertEqual(result["status"], expected, scenario)
                if scenario in {"auth_error", "quota_error", "uncertain_side_effect",
                                "unknown_failure", "success_exit_nonzero", "failed_after_usage"}:
                    self.assertFalse(result["retry_allowed"])
            receipts = run_with_retry(lambda rid, _: [sys.executable, str(FAKE), "transient_retry", rid],
                                      root, root / "retry", "synthetic", timeout_seconds=5)
            self.assertEqual(len(receipts), 2)
            for scenario in ("unknown_failure", "success_exit_nonzero", "failed_after_usage"):
                receipts = run_with_retry(lambda rid, _: [sys.executable, str(FAKE), scenario, rid],
                                          root, root / ("no-retry-" + scenario), "synthetic", timeout_seconds=5)
                self.assertEqual(len(receipts), 1, scenario)
            with self.assertRaises(DispatchError):
                run([sys.executable, str(FAKE), "valid", "x"], root, root / "blocked", "x", provider="external")

    def test_literal_argv_and_stdin_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            run_id = "literal-argv"
            literal = 'a space "quoted" `$(Get-Secret) & ; | \\ path'
            prompt = 'stdin "quoted" `$(Get-Secret)'
            result = run([sys.executable, str(FAKE), "valid", run_id, literal], root,
                         root / "argv", prompt, timeout_seconds=5, run_id=run_id)
            self.assertEqual(result["status"], "success")
            payload = json.loads((root / "argv" / "stdout.txt").read_text(encoding="utf-8"))
            self.assertEqual(payload["argv_tail"], [literal])
            self.assertEqual(payload["echo"], prompt)

    def test_timeout_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            marker = root / "child.pid"
            result = run([sys.executable, str(FAKE), "timeout_with_child", "r", str(marker)], root, root / "timeout",
                         "x", timeout_seconds=0.8, run_id="r")
            self.assertEqual(result["status"], "canceled")
            self.assertTrue(marker.exists())
            child_pid = int(marker.read_text(encoding="utf-8"))
            self.assertFalse(psutil.pid_exists(child_pid), "watchdog left child process alive")


if __name__ == "__main__":
    unittest.main()
