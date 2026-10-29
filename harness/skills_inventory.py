"""Inventory enabled skill metadata without reading conversation history."""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import tomllib
from datetime import datetime, timezone


def inspect(home: pathlib.Path) -> dict:
    config = tomllib.loads((home / "config.toml").read_text(encoding="utf-8"))
    enabled = {name: value.get("enabled") for name, value in config.get("plugins", {}).items()}
    cache = home / "plugins" / "cache"
    rows = []
    for path in cache.glob("*/*/*/skills/*/SKILL.md"):
        version = path.parents[2].name
        plugin = path.parents[3].name
        marketplace = path.parents[4].name
        key = f"{plugin}@{marketplace}"
        if not enabled.get(key):
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        header = raw.split("---", 2)[1] if raw.startswith("---") and raw.count("---") >= 2 else ""
        name = re.search(r"(?m)^name:\s*[\"']?([^\r\n\"']+)", header)
        rows.append({"plugin": key, "version": version, "skill": name.group(1).strip() if name else path.parent.name,
                     "path": str(path), "frontmatter_characters": len(header), "body_characters": len(raw) - len(header),
                     "usage_evidence": None, "cleanup_decision": "unknown_until_user_usage_or_task_evidence"})
    rows.sort(key=lambda x: (x["plugin"], x["skill"], x["version"]))
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "enabled_plugins": enabled,
            "catalogued_skill_files": len(rows), "rows": rows,
            "limits": ["cache may include versions not loaded by current app", "metadata size is characters, not billed tokens",
                       "absence of usage evidence is not proof a skill is unused"]}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--home", type=pathlib.Path, required=True)
    p.add_argument("--output", type=pathlib.Path, required=True)
    a = p.parse_args()
    a.output.write_text(json.dumps(inspect(a.home), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
