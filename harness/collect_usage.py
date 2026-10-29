"""Normalize sanitized Codex JSONL usage into one receipt per attempt."""
from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone


def normalize(events: list[dict], run_id: str, task_id: str, attempt_id: str, model: str | None = None,
              cumulative_baseline: dict | None = None) -> dict:
    seen = set()
    last_total = None
    last_turn = None
    terminal = []
    malformed = False
    for event in events:
        fingerprint = json.dumps(event, sort_keys=True)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        typ = event.get("type")
        payload = event.get("payload")
        info = payload.get("info") if isinstance(payload, dict) else None
        total_usage = info.get("total_token_usage") if isinstance(info, dict) else None
        usage = event.get("usage") if isinstance(event.get("usage"), dict) else total_usage
        if typ == "turn.completed":
            terminal.append("success")
        elif typ in {"turn.failed", "error"}:
            terminal.append("failed")
        elif typ in {"turn.cancelled", "turn.canceled"}:
            terminal.append("canceled")
        elif typ == "malformed_json":
            malformed = True
        if isinstance(usage, dict):
            if typ == "thread/token_count" or total_usage is not None:
                last_total = usage
            else:
                last_turn = usage
    limitations = []
    status = terminal[0] if len(terminal) == 1 and not malformed else "unknown"
    if len(terminal) > 1:
        limitations.append("multiple terminal events; attempt outcome ambiguous")
    if malformed:
        limitations.append("malformed JSONL event; attempt outcome incomplete")
    usage = last_total if last_total is not None else last_turn
    usage_source = "cumulative" if last_total else ("last_event" if last_turn else None)
    if last_total is not None and cumulative_baseline is not None:
        if any(isinstance(value, int) and not isinstance(value, bool) and value < cumulative_baseline.get(key, 0)
               for key, value in last_total.items()):
            usage = None
            usage_source = "cumulative_reset_unattributed"
            limitations.append("cumulative counters decreased; attempt usage unknown")
        else:
            usage = {key: value - cumulative_baseline.get(key, 0) if isinstance(value, int) and not isinstance(value, bool) else value
                     for key, value in last_total.items()}
    elif last_total is not None:
        limitations.append("cumulative counters may include prior turns; pass baseline for resumed thread")
    def get(*keys: str) -> int | None:
        if usage is None:
            return None
        for key in keys:
            if key in usage and isinstance(usage[key], int) and not isinstance(usage[key], bool):
                return usage[key]
        return None
    input_tokens = get("input_tokens", "input")
    cached = get("cached_input_tokens", "cached_input", "cache_read_input_tokens")
    output_tokens = get("output_tokens", "output")
    reasoning = get("reasoning_output_tokens")
    if cached is not None and input_tokens is not None and cached > input_tokens:
        cached = None
        limitations.append("cached input exceeds input; cached count unknown")
    if reasoning is not None and output_tokens is not None and reasoning > output_tokens:
        reasoning = None
        limitations.append("reasoning output exceeds output; reasoning count unknown")
    if usage is None and not limitations:
        limitations.append("usage not exposed")
    return {"schema_version": "1.0", "run_id": run_id, "task_id": task_id, "attempt_id": attempt_id,
            "observed_at": datetime.now(timezone.utc).isoformat(), "model_configured": model, "model_resolved": None,
            "status": status, "terminal_events": len(terminal), "usage_source": usage_source,
            "input_tokens": input_tokens, "cached_input_tokens_included_in_input": cached,
            "output_tokens": output_tokens, "reasoning_tokens_included_in_output": reasoning,
            "elapsed_seconds": None, "attempts": 1, "human_review_minutes": None, "human_approval": None,
            "accepted_result": None, "monetary_cost": None, "monetary_cost_kind": None,
            "limitations": limitations}


def read_events(path: pathlib.Path) -> list[dict]:
    out = []
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            try:
                event = json.loads(line)
                out.append(event if isinstance(event, dict) else {"type": "malformed_json"})
            except json.JSONDecodeError:
                out.append({"type": "malformed_json"})
    return out


def normalize_legacy_record(record: dict) -> dict:
    """Map only safe metadata from old dispatch logs, never prompt or artifact text."""
    channel = record.get("channel", record.get("canal"))
    tokens = record.get("tokens") if isinstance(record.get("tokens"), int) else None
    return {"channel": channel, "status": record.get("status", record.get("verify")),
            "tokens": tokens, "usage_known": tokens is not None}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("input", type=pathlib.Path)
    p.add_argument("--run-id", required=True)
    p.add_argument("--task-id", required=True)
    p.add_argument("--attempt-id", required=True)
    p.add_argument("--model")
    p.add_argument("--elapsed-seconds", type=float)
    p.add_argument("--output", type=pathlib.Path, required=True)
    a = p.parse_args()
    receipt = normalize(read_events(a.input), a.run_id, a.task_id, a.attempt_id, a.model)
    receipt["elapsed_seconds"] = a.elapsed_seconds
    a.output.write_text(json.dumps(receipt, ensure_ascii=False) + "\n", encoding="utf-8")
