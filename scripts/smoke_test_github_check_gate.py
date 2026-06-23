#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import importlib.util
import io
import urllib.error
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

rate_limit_error = urllib.error.HTTPError(
    "https://api.github.com/repos/joustonhuang/unifai/commits/visible-ref",
    403,
    "Forbidden",
    hdrs=None,
    fp=None,
)
stderr = io.StringIO()
with contextlib.redirect_stderr(stderr):
    module.explain_http_error(
        rate_limit_error,
        "https://api.github.com/repos/joustonhuang/unifai/commits/visible-ref",
        '{"message":"API rate limit exceeded for 203.0.113.7.","documentation_url":"https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"}',
    )
rate_limit_output = stderr.getvalue()
print(rate_limit_output, end="")
if "export GH_TOKEN/GITHUB_TOKEN" not in rate_limit_output:
    print("[FAIL] Expected token guidance missing from rate-limit error explanation.")
    raise SystemExit(1)
if "Unauthenticated GitHub API access can fail closed here" not in rate_limit_output:
    print("[FAIL] Expected unauthenticated rate-limit guidance missing.")
    raise SystemExit(1)

unknown_ref_error = urllib.error.HTTPError(
    "https://api.github.com/repos/joustonhuang/unifai/commits/not-on-github",
    422,
    "Unprocessable Entity",
    hdrs=None,
    fp=None,
)
stderr = io.StringIO()
with contextlib.redirect_stderr(stderr):
    module.explain_http_error(
        unknown_ref_error,
        "https://api.github.com/repos/joustonhuang/unifai/commits/not-on-github",
        '{"message":"No commit found for SHA: not-on-github","documentation_url":"https://docs.github.com/rest/commits/commits#get-a-commit","status":"422"}',
    )
unknown_ref_output = stderr.getvalue()
print(unknown_ref_output, end="")
if "not GitHub-visible yet" not in unknown_ref_output:
    print("[FAIL] Expected GitHub-visible ref guidance missing from 422 explanation.")
    raise SystemExit(1)

print("[PASS] GitHub check gate inspector behaves as expected.")
