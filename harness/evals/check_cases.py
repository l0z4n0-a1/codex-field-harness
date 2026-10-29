"""Deterministic gates for synthetic E01, E02, E05 and manifest integrity."""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parent


def check_e01() -> dict:
    data = json.loads((ROOT / "cases" / "E01" / "input.json").read_text(encoding="utf-8"))
    expected = json.loads((ROOT / "oracles" / "E01.json").read_text(encoding="utf-8"))
    chosen = {}
    for row in data["rows"]:
        if "," in row["amount"]:
            raise ValueError("comma decimal rejected")
        if row["id"] not in chosen or row["updated_at"] >= chosen[row["id"]]["updated_at"]:
            chosen[row["id"]] = row
    result = {"rows": list(chosen.values()), "count": len(chosen),
              "amount_total": str(sum((Decimal(x["amount"]) for x in chosen.values()), Decimal(0)))}
    assert result == expected
    try:
        Decimal("3,35")
        raise AssertionError("comma unexpectedly accepted")
    except __import__("decimal").InvalidOperation:
        pass
    return {"status": "pass", "unique": result["count"], "total": result["amount_total"]}


def check_e02() -> dict:
    source = ROOT / "cases" / "E02"
    with tempfile.TemporaryDirectory() as temp:
        target = pathlib.Path(temp)
        for name in ("discount.py", "test_discount.py"):
            shutil.copyfile(source / name, target / name)
        before = subprocess.run([sys.executable, "-m", "unittest", "-q"], cwd=target, capture_output=True, text=True)
        text = (target / "discount.py").read_text(encoding="utf-8")
        assert "amount > Decimal('100')" in text
        (target / "discount.py").write_text(text.replace("amount > Decimal('100')", "amount >= Decimal('100')"), encoding="utf-8")
        after = subprocess.run([sys.executable, "-m", "unittest", "-q"], cwd=target, capture_output=True, text=True)
        assert before.returncode != 0 and after.returncode == 0, (before.stderr, after.stderr)
    return {"status": "pass", "before_failed": True, "after_passed": True, "source_fixture_unchanged": True}


def check_e05() -> dict:
    data = json.loads((ROOT / "cases" / "E05" / "input.json").read_text(encoding="utf-8"))
    expected = json.loads((ROOT / "oracles" / "E05.json").read_text(encoding="utf-8"))
    revenue = Decimal(data["monthly_revenue"])
    costs = sum((Decimal(x) for x in data["costs"].values()), Decimal(0))
    variation = Decimal(data["scenario_revenue_change"])
    values = {"base_contribution": str(revenue - costs),
              "low_contribution": str(revenue * (1 - variation) - costs),
              "high_contribution": str(revenue * (1 + variation) - costs)}
    assert all(Decimal(values[k]) == Decimal(expected[k]) for k in values)
    return {"status": "pass", **values}


def check_hashes() -> dict:
    manifest = json.loads((ROOT / "fixture-manifest.json").read_text(encoding="utf-8"))["files"]
    bad = [name for name, digest in manifest.items() if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest]
    assert not bad, bad
    return {"status": "pass", "files": len(manifest)}


if __name__ == "__main__":
    results = {"E01": check_e01(), "E02": check_e02(), "E05": check_e05(), "manifest": check_hashes()}
    print(json.dumps(results, ensure_ascii=False))
