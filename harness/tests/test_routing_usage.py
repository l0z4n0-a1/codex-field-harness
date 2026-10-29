import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from collect_usage import normalize, normalize_legacy_record, read_events
from routing import catalog, validate_route


class RoutingUsageTests(unittest.TestCase):
    def test_catalog_rejects_hidden_unknown_tier_and_invalid_effort(self):
        visible = catalog({"models": [{"slug": "gpt-6-sol", "visibility": "list", "supported_reasoning_levels": [{"effort": "medium"}]},
                                      {"slug": "hidden", "visibility": "hide", "supported_reasoning_levels": [{"effort": "medium"}]}]})
        validate_route("gpt-6-sol", "medium", visible)
        for model, effort in [("priority", "medium"), ("hidden", "medium"), ("unknown", "medium"), ("gpt-6-sol", "ultra")]:
            with self.assertRaises(ValueError):
                validate_route(model, effort, visible)

    def test_cumulative_duplicate_and_cached_subset(self):
        event = {"type": "thread/token_count", "payload": {"info": {"total_token_usage": {"input_tokens": 100, "cached_input_tokens": 60, "output_tokens": 20}}}}
        later = {"type": "thread/token_count", "payload": {"info": {"total_token_usage": {"input_tokens": 130, "cached_input_tokens": 80, "output_tokens": 30}}}}
        result = normalize([event, event, later, {"type": "turn.completed"}], "r", "t", "a")
        self.assertEqual((result["input_tokens"], result["cached_input_tokens_included_in_input"], result["output_tokens"]), (130, 80, 30))
        self.assertEqual(result["terminal_events"], 1)
        delta = normalize([later], "r", "t", "a", cumulative_baseline={"input_tokens": 100, "cached_input_tokens": 60, "output_tokens": 20})
        self.assertEqual((delta["input_tokens"], delta["cached_input_tokens_included_in_input"], delta["output_tokens"]), (30, 20, 10))

    def test_missing_cancel_and_zero_distinction(self):
        missing = normalize([{"type": "turn.cancelled"}], "r", "t", "a")
        self.assertIsNone(missing["input_tokens"])
        self.assertEqual(missing["status"], "canceled")
        zero = normalize([{"type": "turn.completed", "usage": {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}}], "r", "t", "a")
        self.assertEqual(zero["input_tokens"], 0)

    def test_retry_is_separate_attempt(self):
        failed = normalize([{"type": "turn.failed"}], "r", "t", "a1")
        passed = normalize([{"type": "turn.completed"}], "r", "t", "a2")
        self.assertEqual((failed["status"], passed["status"]), ("failed", "success"))
        self.assertNotEqual(failed["attempt_id"], passed["attempt_id"])

    def test_legacy_channels_and_unknown_usage(self):
        self.assertEqual(normalize_legacy_record({"canal": "codex", "tokens": "unknown", "prompt": "private"}),
                         {"channel": "codex", "status": None, "tokens": None, "usage_known": False})
        self.assertEqual(normalize_legacy_record({"channel": "codex", "tokens": 0})["tokens"], 0)

    def test_truncated_jsonl_keeps_unknown_not_success(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "events.jsonl"
            path.write_text('{"type":"turn.started"}\n{"type":', encoding="utf-8")
            receipt = normalize(read_events(path), "r", "t", "a")
            self.assertEqual(receipt["status"], "unknown")
            self.assertIsNone(receipt["input_tokens"])

    def test_completed_then_truncated_or_conflicting_terminal_is_unknown(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "events.jsonl"
            path.write_text('{"type":"turn.completed"}\n{"type":', encoding="utf-8")
            truncated = normalize(read_events(path), "r", "t", "a")
            self.assertEqual(truncated["status"], "unknown")
            self.assertIn("malformed JSONL", truncated["limitations"][0])
            conflict = normalize([{"type": "turn.completed"}, {"type": "turn.failed"}], "r", "t", "a")
            self.assertEqual(conflict["status"], "unknown")
            self.assertEqual(conflict["terminal_events"], 2)

    def test_cumulative_reset_is_unknown_not_zero(self):
        event = {"type": "thread/token_count", "payload": {"info": {"total_token_usage": {
            "input_tokens": 5, "cached_input_tokens": 0, "output_tokens": 2}}}}
        result = normalize([event, {"type": "turn.completed"}], "r", "t", "a",
                           cumulative_baseline={"input_tokens": 100, "cached_input_tokens": 60, "output_tokens": 20})
        self.assertIsNone(result["input_tokens"])
        self.assertEqual(result["usage_source"], "cumulative_reset_unattributed")
        self.assertIn("cumulative counters decreased", result["limitations"][0])

    def test_impossible_subcounts_are_not_reported_as_usage(self):
        result = normalize([{"type": "turn.completed", "usage": {"input_tokens": 10,
                            "cached_input_tokens": 12, "output_tokens": 2, "reasoning_output_tokens": 3}}],
                           "r", "t", "a")
        self.assertEqual(result["input_tokens"], 10)
        self.assertIsNone(result["cached_input_tokens_included_in_input"])
        self.assertIsNone(result["reasoning_tokens_included_in_output"])
        self.assertEqual(len(result["limitations"]), 2)

    def test_non_object_jsonl_is_malformed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "events.jsonl"
            path.write_text('[]\n', encoding="utf-8")
            self.assertEqual(normalize(read_events(path), "r", "t", "a")["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
