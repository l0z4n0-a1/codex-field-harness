"""Synthetic process for E07. No network or real provider access."""
import json
import pathlib
import subprocess
import sys
import time

scenario, run_id = sys.argv[1:3]
prompt = sys.stdin.read()
if scenario == "timeout_with_child":
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    pathlib.Path(sys.argv[3]).write_text(str(child.pid), encoding="utf-8")
    time.sleep(60)
elif scenario == "malformed_json":
    print("{bad json")
elif scenario in {"auth_error", "quota_error"}:
    print(json.dumps({"run_id": run_id, "status": "failed", "artifacts": [], "usage": None, "limitations": []}))
    print("auth error" if scenario == "auth_error" else "quota limit", file=sys.stderr)
    sys.exit(1)
elif scenario == "partial_exit_zero":
    print(json.dumps({"run_id": run_id, "status": "partial", "artifacts": [], "usage": None, "limitations": ["tool denied"]}))
elif scenario == "stale_artifact":
    print(json.dumps({"run_id": "old-run", "status": "success", "artifacts": [sys.argv[3]], "usage": None, "limitations": []}))
elif scenario == "uncertain_side_effect":
    print(json.dumps({"run_id": run_id, "status": "failed", "side_effect_uncertain": True, "artifacts": [], "usage": None, "limitations": []}))
elif scenario == "transient_retry":
    print(json.dumps({"run_id": run_id, "status": "failed", "retry_safe": True,
                      "side_effect_uncertain": False, "artifacts": [], "usage": None, "limitations": []}))
    print("temporary network issue", file=sys.stderr)
    sys.exit(1)
elif scenario == "unknown_failure":
    print(json.dumps({"run_id": run_id, "status": "failed", "artifacts": [], "usage": None, "limitations": []}))
    print("unexpected provider failure", file=sys.stderr)
    sys.exit(1)
elif scenario == "success_exit_nonzero":
    print(json.dumps({"run_id": run_id, "status": "success", "retry_safe": True,
                      "side_effect_uncertain": False, "artifacts": [], "usage": None, "limitations": []}))
    print("teardown failed", file=sys.stderr)
    sys.exit(1)
elif scenario == "failed_after_usage":
    print(json.dumps({"run_id": run_id, "status": "failed", "retry_safe": True,
                      "side_effect_uncertain": False, "artifacts": [],
                      "usage": {"input_tokens": 100}, "limitations": []}))
    print("temporary network issue", file=sys.stderr)
    sys.exit(1)
else:
    print(json.dumps({"run_id": run_id, "status": "success", "artifacts": [], "usage": None,
                      "limitations": [], "echo": prompt, "argv_tail": sys.argv[3:]}))
