"""Persist a compact, revisioned task handoff with input integrity checks."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import tempfile
from datetime import datetime, timezone

REQUIRED = ["objective", "exclusions", "input_hash", "base", "owner", "active_decision",
            "revoked_decision", "data_constraint", "artifact", "gate", "blocker", "next_action"]


def hash_file(path: pathlib.Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def create(facts: dict, inputs: list[pathlib.Path]) -> dict:
    missing = [key for key in REQUIRED if key not in facts]
    if missing:
        raise ValueError(f"missing facts: {missing}")
    return {"schema_version": "1.0", "revision": 1, "updated_at": datetime.now(timezone.utc).isoformat(),
            "facts": facts, "inputs": [{"path": str(p), "revision": hash_file(p)} for p in inputs],
            "decisions": [{"value": facts["active_decision"], "status": "active"},
                          {"value": facts["revoked_decision"], "status": "revoked"}],
            "evidence": [], "next_action": facts["next_action"]}


def validate(state: dict) -> list[str]:
    errors = []
    errors.extend(f"missing fact: {key}" for key in REQUIRED if key not in state.get("facts", {}))
    active = {x["value"] for x in state.get("decisions", []) if x.get("status") == "active"}
    revoked = {x["value"] for x in state.get("decisions", []) if x.get("status") == "revoked"}
    if active & revoked or state.get("facts", {}).get("revoked_decision") in active:
        errors.append("revoked decision resurrected")
    for item in state.get("inputs", []):
        p = pathlib.Path(item["path"])
        if not p.is_file():
            errors.append(f"missing input: {p}")
        elif hash_file(p) != item["revision"]:
            errors.append(f"input hash mismatch: {p}")
    return errors


def save(path: pathlib.Path, state: dict, expected_revision: int | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".lock")
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError("writer conflict: state locked") from exc
    try:
        os.close(lock_fd)
        if path.exists():
            current = json.loads(path.read_text(encoding="utf-8"))
            if current["revision"] != expected_revision:
                raise RuntimeError("writer conflict: state revision changed")
            state["revision"] = current["revision"] + 1
        elif expected_revision is not None:
            raise RuntimeError("writer conflict: state disappeared")
        errors = validate(state)
        if errors:
            raise ValueError(errors)
        fd, temp = tempfile.mkstemp(prefix=".handoff-", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                json.dump(state, output, ensure_ascii=False, indent=2)
                output.write("\n")
            os.replace(temp, path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
    finally:
        lock.unlink(missing_ok=True)


def resume(path: pathlib.Path) -> dict:
    state = json.loads(path.read_text(encoding="utf-8"))
    errors = validate(state)
    if errors:
        raise ValueError(errors)
    return state
