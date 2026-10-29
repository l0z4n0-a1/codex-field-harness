"""Append privacy-limited real-task observations and summarize the H15 gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
from datetime import datetime, timezone

DEFAULT_LEDGER = pathlib.Path(__file__).resolve().parent / "telemetry" / "real-tasks.jsonl"
FIELDS = {
    "schema_version", "release_id", "task_id", "revision", "task_class", "route_id", "started_at", "completed_at",
    "real_user_task", "synthetic", "harness_self_test", "accepted_result", "acceptance_basis",
    "acceptance_evidence_ref", "acceptance_evidence_verified", "human_approval", "attempt_count",
    "retry_count", "input_tokens", "cached_input_tokens_included_in_input", "output_tokens",
    "monetary_cost", "execution_seconds", "wait_seconds", "integration_seconds",
    "human_review_seconds", "rework_seconds",
}
REQUIRED = FIELDS - {"route_id", "human_approval"}
NULLABLE_NUMBERS = {"input_tokens", "cached_input_tokens_included_in_input", "output_tokens",
                    "monetary_cost", "execution_seconds", "wait_seconds", "integration_seconds",
                    "human_review_seconds", "rework_seconds"}


def parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("timestamps must be ISO 8601 strings or null")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps require timezone")
    return parsed.astimezone(timezone.utc)


def validate(data: dict) -> dict:
    if not isinstance(data, dict) or set(data) - FIELDS or REQUIRED - set(data):
        raise ValueError("observation has unknown or missing fields; prompt/artifact text is not accepted")
    if data["schema_version"] != "1.0":
        raise ValueError("unsupported observation schema")
    if not isinstance(data["release_id"], str) or not data["release_id"].strip() or len(data["release_id"]) > 120:
        raise ValueError("release_id must identify the active candidate")
    if not isinstance(data["task_id"], str) or not data["task_id"].strip() or len(data["task_id"]) > 128:
        raise ValueError("task_id must be a short nonempty identifier")
    if not isinstance(data["task_class"], str) or not data["task_class"].strip() or len(data["task_class"]) > 80:
        raise ValueError("task_class must be a short freeform label")
    if "route_id" in data and data["route_id"] is not None and (not isinstance(data["route_id"], str) or len(data["route_id"]) > 120):
        raise ValueError("invalid route_id")
    for key in ("revision", "attempt_count", "retry_count"):
        if type(data[key]) is not int or data[key] < (0 if key == "retry_count" else 1):
            raise ValueError(f"invalid {key}")
    if data["retry_count"] >= data["attempt_count"]:
        raise ValueError("retry_count must be less than attempt_count")
    for key in ("real_user_task", "synthetic", "harness_self_test", "acceptance_evidence_verified"):
        if type(data[key]) is not bool:
            raise ValueError(f"{key} must be boolean")
    for key in ("accepted_result", "human_approval"):
        if key in data and data[key] is not None and type(data[key]) is not bool:
            raise ValueError(f"{key} must be boolean or null")
    for key in NULLABLE_NUMBERS:
        value = data[key]
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
            raise ValueError(f"{key} must be nonnegative or null")
        if key in ("input_tokens", "cached_input_tokens_included_in_input", "output_tokens") and value is not None and type(value) is not int:
            raise ValueError(f"{key} must be an integer or null")
    if data["input_tokens"] is not None and data["cached_input_tokens_included_in_input"] is not None and data["cached_input_tokens_included_in_input"] > data["input_tokens"]:
        raise ValueError("cached input is included in input, never greater")
    if data["acceptance_basis"] not in ("user", "objective_gate", "unknown"):
        raise ValueError("invalid acceptance_basis")
    ref = data["acceptance_evidence_ref"]
    if ref is not None and (not isinstance(ref, str) or not ref.strip() or len(ref) > 500):
        raise ValueError("invalid acceptance_evidence_ref")
    if data["acceptance_evidence_verified"] and (ref is None or data["accepted_result"] is None or data["acceptance_basis"] == "unknown"):
        raise ValueError("verified acceptance needs result, basis and evidence reference")
    started, completed = parse_time(data["started_at"]), parse_time(data["completed_at"])
    if started is None or (completed is not None and completed < started):
        raise ValueError("started_at required; completed_at must follow it")
    return {key: data.get(key) for key in sorted(FIELDS)}


def eligible(data: dict) -> bool:
    return (data["real_user_task"] and not data["synthetic"] and not data["harness_self_test"]
            and data["completed_at"] is not None and data["accepted_result"] is not None
            and data["acceptance_evidence_verified"])


def read_latest(ledger: pathlib.Path) -> tuple[dict[str, dict], int]:
    latest = {}
    count = 0
    if not ledger.exists():
        return latest, count
    for number, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), 1):
        try:
            receipt = json.loads(line)
            data = validate(receipt["observation"])
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid observation ledger line {number}: {exc}") from exc
        task_id = data["task_id"]
        previous = latest.get(task_id)
        if data["revision"] != (previous["observation"]["revision"] + 1 if previous else 1):
            raise ValueError(f"non-monotonic revision at ledger line {number}")
        digest = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        if receipt.get("observation_sha256") != digest:
            raise ValueError(f"observation digest mismatch at ledger line {number}")
        latest[task_id] = receipt
        count += 1
    return latest, count


def record(ledger: pathlib.Path, raw: dict) -> dict:
    data = validate(raw)
    latest, _ = read_latest(ledger)
    previous = latest.get(data["task_id"])
    if previous and data["release_id"] != previous["observation"]["release_id"]:
        raise ValueError("a task cannot change release_id across revisions")
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if previous and data["revision"] == previous["observation"]["revision"] and digest == previous["observation_sha256"]:
        return {"state": "already_recorded", "task_id": data["task_id"], "revision": data["revision"]}
    if data["revision"] != (previous["observation"]["revision"] + 1 if previous else 1):
        raise ValueError("revision must increase by exactly one; same revision with different data is a conflict")
    receipt = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(), "observation_sha256": digest,
               "eligible_preliminary": eligible(data), "observation": data}
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(receipt, ensure_ascii=False) + "\n")
    return {"state": "recorded", "task_id": data["task_id"], "revision": data["revision"],
            "eligible_preliminary": receipt["eligible_preliminary"]}


def summary(ledger: pathlib.Path, release_receipt: dict) -> dict:
    if not isinstance(release_receipt, dict) or not release_receipt.get("release_id"):
        raise ValueError("release receipt with release_id is required")
    release_start = parse_time(release_receipt.get("recorded_at_utc"))
    if release_start is None:
        raise ValueError("release receipt needs recorded_at_utc")
    latest, revisions = read_latest(ledger)
    all_rows = [receipt["observation"] for receipt in latest.values()]
    rows = [row for row in all_rows if row["release_id"] == release_receipt["release_id"] and parse_time(row["started_at"]) >= release_start]
    chosen = [row for row in rows if eligible(row)]
    accepted = sum(row["accepted_result"] is True for row in chosen)
    metrics = ("input_tokens", "output_tokens", "monetary_cost", "execution_seconds", "wait_seconds",
               "integration_seconds", "human_review_seconds", "rework_seconds")
    totals = {key: sum(row[key] for row in chosen) if chosen and all(row[key] is not None for row in chosen) else None for key in metrics}
    days = max(0.0, (datetime.now(timezone.utc) - release_start).total_seconds() / 86400)
    time_fields = ("execution_seconds", "wait_seconds", "integration_seconds", "human_review_seconds", "rework_seconds")
    total_time = sum(totals[key] for key in time_fields) if all(totals[key] is not None for key in time_fields) else None
    return {"release_id": release_receipt["release_id"], "revision_records": revisions,
            "distinct_tasks": len(rows), "outside_release_or_pre_rollout_tasks": len(all_rows) - len(rows),
            "eligible_real_tasks": len(chosen),
            "accepted": accepted, "rejected": len(chosen) - accepted,
            "total_attempts": sum(row["attempt_count"] for row in chosen),
            "total_retries": sum(row["retry_count"] for row in chosen),
            "pending_evidence_or_outcome": sum(row["real_user_task"] and not row["synthetic"] and not row["harness_self_test"] and not eligible(row) for row in rows),
            "known_metric_task_counts": {key: sum(row[key] is not None for row in chosen) for key in metrics},
            "totals_only_when_complete": totals,
            "input_tokens_per_accepted": totals["input_tokens"] / accepted if accepted and totals["input_tokens"] is not None else None,
            "money_per_accepted": totals["monetary_cost"] / accepted if accepted and totals["monetary_cost"] is not None else None,
            "total_seconds_per_accepted": total_time / accepted if accepted and total_time is not None else None,
            "window_days_since_release": days,
            "review_due": len(chosen) >= 10 or (days >= 14 and bool(chosen)),
            "production_validated": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("record", "summary"))
    parser.add_argument("--input", type=pathlib.Path)
    parser.add_argument("--ledger", type=pathlib.Path, default=DEFAULT_LEDGER)
    parser.add_argument("--release-receipt", type=pathlib.Path)
    args = parser.parse_args()
    if args.command == "record":
        if args.input is None:
            parser.error("record requires --input")
        result = record(args.ledger, json.loads(args.input.read_text(encoding="utf-8")))
    else:
        if args.release_receipt is None:
            parser.error("summary requires --release-receipt")
        result = summary(args.ledger, json.loads(args.release_receipt.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False))
