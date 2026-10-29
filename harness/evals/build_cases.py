"""Materialize synthetic E01-E08 inputs and separate, immutable oracles."""
from __future__ import annotations

import hashlib
import json
import pathlib
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parent
CASES = ROOT / "cases"
ORACLES = ROOT / "oracles"


def write(path: pathlib.Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    leads = [
        ("A", "2026-01-01", "a@exemplo.test", "10.10"),
        ("B", "2026-01-02", "", "0"),
        ("C", "2026-01-03", "c@exemplo.test", "3.35"),
        ("A", "2026-01-04", "a2@exemplo.test", "10.10"),
        ("D", "2026-01-02", "d@exemplo.test", "3.35"),
        ("E", "2026-01-03", "e@exemplo.test", "0"),
        ("F", "2026-01-04", "f@exemplo.test", "10.10"),
        ("B", "2026-01-05", "", "3.35"),
        ("G", "2026-01-06", "g@exemplo.test", "0"),
        ("H", "2026-01-07", "h@exemplo.test", "10.10"),
        ("C", "2026-01-03", "c2@exemplo.test", "3.35"),
        ("I", "2026-01-08", "i@exemplo.test", "0"),
    ]
    rows = [dict(id=i, updated_at=d, email=e, amount=a) for i, d, e, a in leads]
    write(CASES / "E01" / "input.json", {"rows": rows, "rule": "deduplicate by id, latest ISO date wins; same date last input position wins; preserve empty email; amounts are decimal strings with dot; reject comma decimal"})
    chosen = {}
    for row in rows:
        if row["id"] not in chosen or row["updated_at"] >= chosen[row["id"]]["updated_at"]:
            chosen[row["id"]] = row
    expected = {"rows": list(chosen.values()), "count": len(chosen),
                "amount_total": str(sum((Decimal(r["amount"]) for r in chosen.values()), Decimal(0)))}
    write(ORACLES / "E01.json", expected)
    write(CASES / "E02" / "discount.py", "from decimal import Decimal\n\ndef discounted(amount: Decimal) -> Decimal:\n    if not isinstance(amount, Decimal):\n        raise TypeError('Decimal required')\n    return amount * (Decimal('0.90') if amount > Decimal('100') else Decimal('1'))\n")
    write(CASES / "E02" / "test_discount.py", "import unittest\nfrom decimal import Decimal\nfrom discount import discounted\n\nclass DiscountTests(unittest.TestCase):\n    def test_boundary(self):\n        self.assertEqual(discounted(Decimal('99.99')), Decimal('99.99'))\n        self.assertEqual(discounted(Decimal('100')), Decimal('90.00'))\n        self.assertEqual(discounted(Decimal('100.01')), Decimal('90.009'))\n    def test_decimal_contract(self):\n        with self.assertRaises(TypeError): discounted(100.0)\n\nif __name__ == '__main__': unittest.main()\n")
    write(ORACLES / "E02.json", {"minimal_change": "replace > with >= in discount.py", "before_tests_fail": True, "after_tests_pass": True})
    write(CASES / "E03" / "brief.json", {"question": "Choose Markdown files or a vector database for 40 synthetic documents updated weekly; no demonstrated semantic search demand. Cite source manifest, explain tradeoffs and unavailable source.", "documents": 40, "update_frequency": "weekly", "semantic_search_demand": "unproven", "deliberately_obsolete_claim": "A 2021 note says embeddings are always required", "unavailable_url": "https://example.invalid/unavailable"})
    write(CASES / "E03" / "sources.json", {"accessed_at": "2026-09-25", "urls": [
        "https://docs.python.org/3/library/pathlib.html",
        "https://www.sqlite.org/fts5.html",
        "https://www.postgresql.org/docs/current/textsearch.html",
        "https://platform.openai.com/docs/guides/embeddings",
        "https://www.w3.org/TR/json-ld11/",
    ], "verification": "opened on 2026-09-25; official sources; frozen for this fixture version"})
    write(ORACLES / "E03.json", {"critical": ["cite fixed available sources", "acknowledge unavailable URL", "compare operating costs", "do not invent demand or revenue", "explain stale note limitation"]})
    write(CASES / "E04" / "input.json", {"persona": {"id": "P01", "registry": "A", "adult": True, "voice": "calm, practical"}, "campaign": {"registry": "B", "persona_reference": "A:P01", "product": "synthetic wellness tea", "health_claim_proof": None, "offer": "single sample box", "request": "brief 3 static text-only pieces"}, "muse_tools_available": False, "prepare_response": {"status": "READY", "artifact_path": None}})
    write(ORACLES / "E04.json", {"critical": ["A owns existing P01 identity", "B references A:P01", "no health benefit asserted", "three coherent text-only briefs", "READY without file is preparation only", "no generation, approval or publication claim", "visual QA pending"]})
    write(CASES / "E05" / "input.json", {"unit": "BRL synthetic", "monthly_revenue": "12000", "costs": {"media": "3000", "software": "800", "production": "2200", "other": "1000"}, "scenario_revenue_change": "0.20", "scenario_costs_fixed": True})
    write(ORACLES / "E05.json", {"base_contribution": "5000", "low_contribution": "2600", "high_contribution": "7400", "taxes": "unknown", "not_net_profit": True})
    write(CASES / "E06" / "input.json", {"objective": "preserve task continuity", "exclusions": ["no external upload"], "input_hash": "sha256:fixture", "base": "v1", "owner": "coordinator", "active_decision": "use state file", "revoked_decision": "use implicit memory", "data_constraint": "synthetic only", "artifact": "result.json", "gate": "12/12 facts", "blocker": "none", "next_action": "verify hashes"})
    write(ORACLES / "E06.json", {"required_fact_count": 12, "changed_hash_rejected": True, "missing_file_detected": True, "revoked_decision_not_active": True})
    write(CASES / "E07" / "scenarios.json", {"scenarios": ["valid", "malformed_json", "timeout_with_child", "auth_error", "quota_error", "partial_exit_zero", "stale_artifact", "tool_denied", "transient_retry", "uncertain_side_effect", "literal_argv"], "literal": "a'\"`$(Get-Secret) b"})
    write(ORACLES / "E07.json", {"critical": ["process tree cancelled", "no auth/quota retry", "transient retry <=1", "stale artifact rejected", "partial != success", "literal argv unchanged", "no uncertain effect retry"]})
    write(CASES / "E08" / "input.json", {"skills": ["imagegen", "persona-foundry:create-content", "ugc-ai-native-agency:muse-cockpit", "spreadsheets", "openai-docs", "site-alchemy"], "requests": ["create a text content episode for existing persona P01", "edit native SVG", "analyze XLSX", "research current Codex settings", "ordinary text correction"], "scope": ["global AGENTS", "root AGENTS", "subdir AGENTS"], "muse_tools_available": False, "persona_owner_reference": "A:P01"})
    write(ORACLES / "E08.json", {"critical": ["existing persona uses owner registry", "native SVG avoids raster imagegen", "spreadsheet skill selected", "OpenAI Docs for current Codex settings", "no unrelated plugin activation", "subdir instructions win in scope", "missing MUSE tools declared"]})
    write(ROOT / "rubrics.json", {"version": "1.0", "frozen": True, "critical_rule": "all critical criteria pass; unresolved human review remains pending", "cases": {f"E{i:02d}": {"oracle": f"oracles/E{i:02d}.json", "validation_layer": "unit" if i in (1, 2, 5, 6, 7) else "static", "human_review": "pending" if i in (3, 4, 8) else None} for i in range(1, 9)}})
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted([*CASES.rglob("*"), *ORACLES.rglob("*"), ROOT / "rubrics.json"]) if p.is_file() and "__pycache__" not in p.parts}
    write(ROOT / "fixture-manifest.json", {"version": "1.1", "files": manifest, "revisions": {"E08": "1.1: action and owner reference made explicit"}, "oracle_separation": "executor receives cases/ only"})
    print(json.dumps({"cases": 8, "hashed_files": len(manifest), "E01_count": expected["count"], "E01_total": expected["amount_total"]}))


if __name__ == "__main__":
    main()
