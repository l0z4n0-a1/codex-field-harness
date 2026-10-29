"""Opt-in external process adapter. Live providers are disabled by default."""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import time
from uuid import uuid4


class DispatchError(RuntimeError):
    pass


def terminate_tree(process: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=15)
    else:
        import signal
        os.killpg(process.pid, signal.SIGKILL)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def classify_failure(stderr: str) -> str:
    lowered = stderr.lower()
    if "quota" in lowered or "rate limit" in lowered:
        return "quota"
    if "auth" in lowered or "unauthorized" in lowered or "login" in lowered:
        return "auth"
    if "invalid model" in lowered:
        return "invalid_model"
    return "transient_or_unknown"


def run(argv: list[str], cwd: pathlib.Path, output_dir: pathlib.Path, prompt: str,
        timeout_seconds: float = 600, *, provider: str = "fake", live_enabled: bool = False,
        run_id: str | None = None) -> dict:
    if provider != "fake" and not live_enabled:
        raise DispatchError("external live adapter disabled pending access and containment review")
    if not argv or not isinstance(argv, list) or any(not isinstance(x, str) for x in argv):
        raise ValueError("argv must be a list of literal strings")
    if not cwd.is_dir():
        raise FileNotFoundError(cwd)
    output_dir.mkdir(parents=True, exist_ok=False)
    run_id = run_id or uuid4().hex
    started = time.monotonic()
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8", creationflags=flags, start_new_session=os.name != "nt")
    try:
        stdout, stderr = process.communicate(prompt, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        terminate_tree(process)
        return {"run_id": run_id, "status": "canceled", "failure_kind": "timeout", "retry_allowed": False,
                "artifacts": [], "usage": None, "limitations": ["process tree canceled after watchdog"],
                "elapsed_seconds": round(time.monotonic() - started, 3)}
    (output_dir / "stdout.txt").write_text(stdout[:1_000_000], encoding="utf-8")
    (output_dir / "stderr.txt").write_text(stderr[:100_000], encoding="utf-8")
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = None
    failure = classify_failure(stderr)
    if not isinstance(parsed, dict) or parsed.get("run_id") != run_id:
        status = "failed" if process.returncode else "unknown"
        return {"run_id": run_id, "status": status, "failure_kind": "malformed_or_stale_result",
                "retry_allowed": False, "artifacts": [], "usage": None, "limitations": ["missing valid current-run JSON"],
                "elapsed_seconds": round(time.monotonic() - started, 3)}
    status = parsed.get("status", "unknown")
    if status not in {"success", "failed", "partial", "canceled", "unknown"}:
        status = "unknown"
    if process.returncode and status == "success":
        status = "failed"
    artifacts = []
    for item in parsed.get("artifacts", []):
        path = pathlib.Path(item)
        try:
            path.resolve().relative_to(output_dir.resolve())
        except ValueError:
            continue
        if path.is_file() and path.stat().st_mtime >= time.time() - (time.monotonic() - started) - 2:
            artifacts.append(str(path))
    retry_safe = (parsed.get("status") == "failed" and parsed.get("retry_safe") is True
                  and parsed.get("side_effect_uncertain") is False and not parsed.get("usage"))
    return {"run_id": run_id, "status": status, "failure_kind": failure if status == "failed" else None,
            "retry_allowed": status == "failed" and retry_safe and failure not in {"quota", "auth", "invalid_model"},
            "artifacts": artifacts, "usage": parsed.get("usage"), "limitations": parsed.get("limitations", []),
            "elapsed_seconds": round(time.monotonic() - started, 3)}


def run_with_retry(argv_factory, cwd: pathlib.Path, output_root: pathlib.Path, prompt: str,
                   *, provider: str = "fake", live_enabled: bool = False, timeout_seconds: float = 600) -> list[dict]:
    receipts = []
    for attempt in (1, 2):
        run_id = uuid4().hex
        receipt = run(argv_factory(run_id, attempt), cwd, output_root / f"attempt-{attempt}-{run_id}", prompt,
                      timeout_seconds, provider=provider, live_enabled=live_enabled, run_id=run_id)
        receipts.append(receipt)
        if not receipt["retry_allowed"]:
            break
    return receipts
