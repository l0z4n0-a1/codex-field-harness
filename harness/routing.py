"""Resolve model routes from observed Codex configuration and catalog metadata."""
from __future__ import annotations

import argparse
import json
import pathlib
import tomllib
from datetime import datetime, timezone


def catalog(cache: dict) -> dict[str, set[str]]:
    result = {}
    for item in cache.get("models", []):
        if item.get("visibility") == "list":
            result[item["slug"]] = {v["effort"] for v in item.get("supported_reasoning_levels", [])}
    return result


def validate_route(model_id: str, effort: str, visible: dict[str, set[str]]) -> None:
    if model_id == "priority" or model_id not in visible:
        raise ValueError(f"model unavailable or hidden: {model_id}")
    if effort not in visible[model_id]:
        raise ValueError(f"effort unsupported by {model_id}: {effort}")


def build(home: pathlib.Path, cli_version: str, core_version: str) -> dict:
    config = tomllib.loads((home / "config.toml").read_text(encoding="utf-8"))
    raw = json.loads((home / "models_cache.json").read_text(encoding="utf-8"))
    visible = catalog(raw)
    now = datetime.now(timezone.utc).isoformat()
    paths = [("global", home / "config.toml")] + [(p.stem.removesuffix(".config"), p) for p in sorted(home.glob("*.config.toml"))]
    routes = []
    for name, path in paths:
        parsed = tomllib.loads(path.read_text(encoding="utf-8"))
        model = parsed.get("model", config.get("model"))
        effort = parsed.get("model_reasoning_effort", config.get("model_reasoning_effort"))
        validate_route(model, effort, visible)
        routes.append({"name": name, "surface": "codex_cli", "executable": "PATH cli", "version": cli_version,
                       "model_id": model, "effort": effort, "service_tier": parsed.get("service_tier", config.get("service_tier")),
                       "source": str(path), "observed_at": now, "status": "configured_not_benchmarked",
                       "fallback": "global", "escalation_trigger": "critical quality failure; diagnose before one targeted retest"})
    return {"schema_version": "1.0", "observed_at": now, "catalog_fetched_at": raw.get("fetched_at"),
            "catalog_client_version": raw.get("client_version"), "app_core_version": core_version,
            "visibility_rule": "only visibility=list may resolve; catalog visibility is not account entitlement",
            "service_tier_rule": "priority is a service tier, never a model_id",
            "routes": routes, "hidden_model_ids": [m["slug"] for m in raw.get("models", []) if m.get("visibility") != "list"],
            "promotion": {"state": "baseline", "reason": "no paired accepted-result comparison", "experiments_enabled": False}}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--home", type=pathlib.Path, required=True)
    p.add_argument("--cli-version", required=True)
    p.add_argument("--core-version", required=True)
    p.add_argument("--output", type=pathlib.Path, required=True)
    a = p.parse_args()
    a.output.write_text(json.dumps(build(a.home, a.cli_version, a.core_version), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
