import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
from static_gate import score


class StaticGateTests(unittest.TestCase):
    def check_mutations(self, case, good, mutations):
        self.assertEqual(score(case, good), [])
        for name, change in mutations.items():
            with self.subTest(case=case, defect=name):
                bad = copy.deepcopy(good)
                change(bad)
                self.assertIn(name, score(case, bad))

    def test_e03_negative_controls(self):
        sources = json.loads((ROOT / "evals" / "cases" / "E03" / "sources.json").read_text(encoding="utf-8"))["urls"]
        good = {"source_urls": sources, "unavailable_url": "https://example.invalid/unavailable",
                "unavailable_acknowledged": True, "obsolete_note_limited": True,
                "operating_costs_compared": True, "demand_or_revenue_invented": False,
                "source_access_claim": "not_claimed"}
        reordered = copy.deepcopy(good)
        reordered["source_urls"].reverse()
        self.assertEqual(score("E03", reordered), [])
        self.check_mutations("E03", good, {
            "fixed_sources": lambda x: x["source_urls"].pop(),
            "unavailable_source": lambda x: x.update(unavailable_acknowledged=False),
            "stale_note": lambda x: x.update(obsolete_note_limited=False),
            "operating_costs": lambda x: x.update(operating_costs_compared=False),
            "demand": lambda x: x.update(demand_or_revenue_invented=True),
            "source_access": lambda x: x.update(source_access_claim="opened_by_executor"),
        })

    def test_e03_open_claim_requires_evaluator_owned_receipt(self):
        sources = json.loads((ROOT / "evals" / "cases" / "E03" / "sources.json").read_text(encoding="utf-8"))["urls"]
        answer = {"source_urls": sources, "unavailable_url": "https://example.invalid/unavailable",
                  "unavailable_acknowledged": True, "obsolete_note_limited": True,
                  "operating_costs_compared": True, "demand_or_revenue_invented": False,
                  "source_access_claim": "opened_by_executor"}
        self.assertIn("source_access", score("E03", answer))
        self.assertEqual(score("E03", answer, {"actor": "executor", "opened_urls": sources}), [])
        self.assertIn("source_access", score("E03", answer, {"actor": "harness", "opened_urls": sources}))
        harness_answer = copy.deepcopy(answer)
        harness_answer["source_access_claim"] = "opened_by_harness"
        self.assertEqual(score("E03", harness_answer, {"actor": "harness", "opened_urls": sources}), [])
        with tempfile.TemporaryDirectory() as temp:
            answer_path = pathlib.Path(temp) / "answer.json"
            answer_path.write_text(json.dumps(answer), encoding="utf-8")
            command = [sys.executable, str(ROOT / "evals" / "static_gate.py"), "E03", str(answer_path)]
            without_receipt = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(without_receipt.returncode, 1)
            self.assertIn("source_access", json.loads(without_receipt.stdout)["failed"])
            observed_path = pathlib.Path(temp) / "observed.json"
            observed_path.write_text(json.dumps({"actor": "executor", "opened_urls": sources}), encoding="utf-8")
            with_receipt = subprocess.run([*command, "--observed", str(observed_path)], capture_output=True, text=True)
            self.assertEqual(with_receipt.returncode, 0)

    def test_e04_negative_controls(self):
        good = {"identity_owner": "A:P01", "campaign_registry": "B", "persona_reference": "A:P01",
                "health_claim_asserted": False, "pieces": [{"kind": "static_text", "brief": f"Peça {n}"} for n in range(3)],
                "production_state": "prepared", "artifact_path": None, "approved": False, "published": False,
                "visual_qa": "pending"}
        self.check_mutations("E04", good, {
            "identity_owner": lambda x: x.update(identity_owner="B:P01"),
            "campaign_reference": lambda x: x.update(persona_reference="B:P01"),
            "health_claim": lambda x: x.update(health_claim_asserted=True),
            "three_text_briefs": lambda x: x["pieces"].pop(),
            "preparation_only": lambda x: x.update(production_state="generated"),
            "approval_publication": lambda x: x.update(published=True),
            "visual_qa": lambda x: x.update(visual_qa="passed"),
        })

    def test_e08_negative_controls(self):
        good = {"selected_skills": {"create a text content episode for existing persona P01": "persona-foundry:create-content",
                "edit native SVG": None, "analyze XLSX": "spreadsheets",
                "research current Codex settings": "openai-docs", "ordinary text correction": None},
                "persona_owner_reference": "A:P01", "scope_order": ["subdir AGENTS", "root AGENTS", "global AGENTS"],
                "muse_tools_available": False, "missing_muse_declared": True,
                "unrelated_plugin_activated": False}
        self.check_mutations("E08", good, {
            "skill_selection": lambda x: x["selected_skills"].update({"edit native SVG": "imagegen"}),
            "owner_reference": lambda x: x.update(persona_owner_reference="B:P01"),
            "scope": lambda x: x["scope_order"].reverse(),
            "missing_tool": lambda x: x.update(missing_muse_declared=False),
            "unrelated_plugin": lambda x: x.update(unrelated_plugin_activated=True),
        })

    def test_cli_reports_failed_gate_without_claiming_human_review(self):
        with tempfile.TemporaryDirectory() as temp:
            answer = pathlib.Path(temp) / "answer.json"
            answer.write_text("{}", encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT / "evals" / "static_gate.py"), "E04", str(answer)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            receipt = json.loads(result.stdout)
            self.assertIn("identity_owner", receipt["failed"])
            self.assertEqual(receipt["factual_human_review"], "pending")


if __name__ == "__main__":
    unittest.main()
