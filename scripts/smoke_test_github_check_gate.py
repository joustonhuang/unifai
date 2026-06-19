#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import importlib.util
import io
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_github_check_gate.py"

spec = importlib.util.spec_from_file_location("check_github_check_gate", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def run_case(fake_github_get, argv: list[str]) -> tuple[int, str, str]:
    module.github_get = fake_github_get
    old_argv = module.sys.argv[:]
    module.sys.argv = argv
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = module.main()
    finally:
        module.sys.argv = old_argv
    return code, stdout.getvalue(), stderr.getvalue()


def success_get(path: str):
    if path == "repos/joustonhuang/unifai/commits/visible-ref":
        return {"sha": "abc123"}
    if path == "repos/joustonhuang/unifai/commits/abc123/check-runs?per_page=100&page=1":
        return {
            "check_runs": [
                {
                    "id": i,
                    "name": f"filler-{i}",
                    "status": "completed",
                    "conclusion": "success",
                    "html_url": f"https://example.invalid/filler-{i}",
                }
                for i in range(1, 101)
            ]
        }
    if path == "repos/joustonhuang/unifai/commits/abc123/check-runs?per_page=100&page=2":
        return {
            "check_runs": [
                {
                    "id": 211,
                    "name": "Bootstrap Installer Preflight",
                    "status": "completed",
                    "conclusion": "success",
                    "html_url": "https://example.invalid/preflight",
                }
            ]
        }
    raise AssertionError(f"unexpected path: {path}")


def failure_get(path: str):
    if path == "repos/joustonhuang/unifai/commits/bad-ref":
        return {"sha": "def456"}
    if path == "repos/joustonhuang/unifai/commits/def456/check-runs?per_page=100&page=1":
        return {
            "check_runs": [
                {
                    "id": 22,
                    "name": "Bootstrap Installer Preflight",
                    "status": "completed",
                    "conclusion": "failure",
                    "html_url": "https://example.invalid/failed-preflight",
                }
            ]
        }
    if path == "repos/joustonhuang/unifai/check-runs/22/annotations?per_page=100&page=1":
        return [
            {
                "annotation_level": "warning",
                "path": ".github",
                "start_line": i,
                "message": "Node.js 20 actions are deprecated.",
            }
            for i in range(1, 101)
        ]
    if path == "repos/joustonhuang/unifai/check-runs/22/annotations?per_page=100&page=2":
        return [
            {
                "annotation_level": "failure",
                "path": ".github/workflows/bootstrap-preflight.yml",
                "start_line": 71,
                "message": "Process completed with exit code 1.",
            }
        ]
    raise AssertionError(f"unexpected path: {path}")


print("=== UnifAI Smoke Test: GitHub check gate inspector ===")

code, stdout, stderr = run_case(success_get, [str(SCRIPT), "visible-ref"])
print(stdout, end="")
print(stderr, end="")
if code != 0:
    print("[FAIL] Expected success case to return exit code 0.")
    raise SystemExit(1)
if "Bootstrap Installer Preflight: status=completed conclusion=success" not in stdout:
    print("[FAIL] Expected success-case check status line missing.")
    raise SystemExit(1)
if "[INFO] Optional check not present: Core Modules & Exoskeleton E2E" not in stdout:
    print("[FAIL] Expected optional-check informational line missing in success case.")
    raise SystemExit(1)

code, stdout, stderr = run_case(failure_get, [str(SCRIPT), "bad-ref"])
print(stdout, end="")
print(stderr, end="")
if code != 1:
    print("[FAIL] Expected failure case to return exit code 1.")
    raise SystemExit(1)
if "Bootstrap Installer Preflight: status=completed conclusion=failure" not in stdout:
    print("[FAIL] Expected failure-case check status line missing.")
    raise SystemExit(1)
if "likely root signal: failure: .github/workflows/bootstrap-preflight.yml line 71 — Process completed with exit code 1." not in stdout:
    print("[FAIL] Expected root-signal summary missing from failure case.")
    raise SystemExit(1)
if "annotations:" not in stdout or "Node.js 20 actions are deprecated." not in stdout or "Process completed with exit code 1." not in stdout:
    print("[FAIL] Expected failure annotations missing from failure case.")
    raise SystemExit(1)
if "... 95 more annotation(s) omitted" not in stdout and "… 95 more annotation(s) omitted" not in stdout:
    print("[FAIL] Expected annotation omission summary missing from failure case.")
    raise SystemExit(1)

print("[PASS] GitHub check gate inspector behaves as expected.")
