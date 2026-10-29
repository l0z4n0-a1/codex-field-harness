"""Read-only metadata inventory for managed Codex Git worktrees."""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
from datetime import datetime, timezone


def git(path: pathlib.Path, *args: str) -> dict:
    argv = ["git", "--no-optional-locks", "-C", str(path), *args]
    result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    return {"exit_code": result.returncode, "stdout": result.stdout.strip(), "stderr_kind": "error" if result.returncode else None}


def inspect(root: pathlib.Path) -> dict:
    entries = []
    for slot in sorted(root.iterdir()):
        if not slot.is_dir():
            continue
        for tree in sorted(slot.iterdir()):
            pointer = tree / ".git"
            if not pointer.is_file():
                continue
            branch = git(tree, "branch", "--show-current")
            head = git(tree, "rev-parse", "HEAD")
            status = git(tree, "status", "--porcelain", "--untracked-files=normal")
            topology = git(tree, "worktree", "list", "--porcelain")
            upstream = git(tree, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
            ahead = git(tree, "rev-list", "--count", "@{upstream}..HEAD") if upstream["exit_code"] == 0 else None
            entries.append({"slot": slot.name, "path": str(tree), "pointer_present": True,
                            "branch": branch["stdout"] or "DETACHED" if branch["exit_code"] == 0 else None,
                            "head": head["stdout"] if head["exit_code"] == 0 else None,
                            "dirty": bool(status["stdout"]) if status["exit_code"] == 0 else None,
                            "status_line_count": len(status["stdout"].splitlines()) if status["exit_code"] == 0 else None,
                            "upstream": upstream["stdout"] if upstream["exit_code"] == 0 else None,
                            "ahead_count": int(ahead["stdout"]) if ahead and ahead["exit_code"] == 0 else None,
                            "topology_confirmed": topology["exit_code"] == 0 and str(tree).replace('\\', '/').lower() in topology["stdout"].replace('\\', '/').lower(),
                            "owner": None, "integration_status": "unknown", "retention": "retain_pending_owner_and_integration_review"})
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "root": str(root), "entries": entries,
            "policy": "no prune, reset, move, or deletion; dirty/untracked/unpushed is never automatic removal"}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=pathlib.Path, required=True)
    p.add_argument("--output", type=pathlib.Path, required=True)
    a = p.parse_args()
    a.output.write_text(json.dumps(inspect(a.root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
