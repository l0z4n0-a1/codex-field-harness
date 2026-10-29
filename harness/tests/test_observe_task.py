import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from observe_task import record, summary


def sample(task_id="real-1", **changes):
    row = {
        "schema_version": "1.0", "release_id": "candidate-a", "task_id": task_id, "revision": 1,
        "task_class": "software", "route_id": None,
        "started_at": "2026-09-25T12:00:00Z", "completed_at": "2026-09-25T12:01:00Z",
        "real_user_task": True, "synthetic": False, "harness_self_test": False,
        "accepted_result": True, "acceptance_basis": "objective_gate",
        "acceptance_evidence_ref": "local:test-receipt", "acceptance_evidence_verified": True,
        "human_approval": None, "attempt_count": 1, "retry_count": 0,
        "input_tokens": 100, "cached_input_tokens_included_in_input": 40,
        "output_tokens": 10, "monetary_cost": None,
        "execution_seconds": 5, "wait_seconds": 0, "integration_seconds": 1,
        "human_review_seconds": 0, "rework_seconds": 0,
    }
    row.update(changes)
    return row


RELEASE = {"release_id": "candidate-a", "recorded_at_utc": "2026-09-25T11:00:00Z"}


class ObservationTests(unittest.TestCase):
    def test_real_task_counts_without_inventing_missing_money(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = pathlib.Path(directory) / "real.jsonl"
            first = sample()
            self.assertTrue(record(ledger, first)["eligible_preliminary"])
            self.assertEqual(record(ledger, first)["state"], "already_recorded")
            result = summary(ledger, RELEASE)
            self.assertEqual(result["revision_records"], 1)
            self.assertEqual(result["eligible_real_tasks"], 1)
            self.assertEqual(result["input_tokens_per_accepted"], 100)
            self.assertEqual(result["total_seconds_per_accepted"], 6)
            self.assertIsNone(result["money_per_accepted"])
            self.assertFalse(result["production_validated"])

    def test_revision_rejection_and_synthetic_exclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = pathlib.Path(directory) / "real.jsonl"
            record(ledger, sample())
            with self.assertRaises(ValueError):
                record(ledger, sample(input_tokens=101))
            with self.assertRaises(ValueError):
                record(ledger, sample(revision=2, release_id="candidate-b"))
            record(ledger, sample(revision=2, accepted_result=False, acceptance_evidence_ref="local:failed-gate"))
            record(ledger, sample("synthetic-1", synthetic=True))
            record(ledger, sample("pending-1", completed_at=None, accepted_result=None,
                                  acceptance_basis="unknown", acceptance_evidence_ref=None,
                                  acceptance_evidence_verified=False))
            result = summary(ledger, RELEASE)
            self.assertEqual(result["distinct_tasks"], 3)
            self.assertEqual(result["eligible_real_tasks"], 1)
            self.assertEqual(result["accepted"], 0)
            self.assertEqual(result["rejected"], 1)
            self.assertEqual(result["pending_evidence_or_outcome"], 1)
            self.assertIsNone(result["input_tokens_per_accepted"])

    def test_other_release_and_pre_rollout_are_not_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = pathlib.Path(directory) / "real.jsonl"
            record(ledger, sample("prior", started_at="2026-09-25T10:00:00Z", completed_at="2026-09-25T10:01:00Z"))
            record(ledger, sample("other-release", release_id="candidate-b"))
            result = summary(ledger, RELEASE)
            self.assertEqual(result["eligible_real_tasks"], 0)
            self.assertEqual(result["outside_release_or_pre_rollout_tasks"], 2)
            self.assertFalse(result["review_due"])

    def test_reject_prompt_text_and_inconsistent_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = pathlib.Path(directory) / "real.jsonl"
            with self.assertRaises(ValueError):
                record(ledger, sample(prompt="private content"))
            with self.assertRaises(ValueError):
                record(ledger, sample(cached_input_tokens_included_in_input=101))
            with self.assertRaises(ValueError):
                record(ledger, sample(acceptance_evidence_verified=True, acceptance_evidence_ref=None))
            self.assertFalse(ledger.exists())

    def test_cli_record_and_summary_on_synthetic_temp_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = pathlib.Path(directory) / "real.jsonl"
            source = pathlib.Path(directory) / "input.json"
            release = pathlib.Path(directory) / "release.json"
            source.write_text(json.dumps(sample("fixture-only", synthetic=True)), encoding="utf-8")
            release.write_text(json.dumps(RELEASE), encoding="utf-8")
            script = pathlib.Path(__file__).resolve().parents[1] / "observe_task.py"
            recorded = json.loads(subprocess.check_output([sys.executable, str(script), "record", "--input", str(source), "--ledger", str(ledger)], text=True))
            self.assertEqual(recorded["state"], "recorded")
            self.assertFalse(recorded["eligible_preliminary"])
            observed = json.loads(subprocess.check_output([sys.executable, str(script), "summary", "--ledger", str(ledger), "--release-receipt", str(release)], text=True))
            self.assertEqual(observed["eligible_real_tasks"], 0)


if __name__ == "__main__":
    unittest.main()
