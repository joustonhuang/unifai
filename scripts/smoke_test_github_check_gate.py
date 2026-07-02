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


class FakeCompletedProcess:
    def __init__(self, stdout: str):
        self.stdout = stdout


def run_case(fake_github_get, argv: list[str], fake_subprocess_run=None) -> tuple[int, str, str]:
    old_github_get = module.github_get
    old_github_get_optional = module.github_get_optional
    module.github_get = fake_github_get
    module.github_get_optional = lambda path, allowed_codes=None: fake_github_get(path)
    old_argv = module.sys.argv[:]
    old_subprocess_run = module.subprocess.run
    module.sys.argv = argv
    if fake_subprocess_run is not None:
        module.subprocess.run = fake_subprocess_run
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = module.main()
            except SystemExit as exc:
                code = int(exc.code) if isinstance(exc.code, int) else 1
    finally:
        module.github_get = old_github_get
        module.github_get_optional = old_github_get_optional
        module.sys.argv = old_argv
        module.subprocess.run = old_subprocess_run
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


def remote_branch_get(path: str):
    if path == "repos/joustonhuang/unifai/commits/github%2Ffix%2Fvisible-branch":
        return None
    if path == "repos/joustonhuang/unifai/commits/refs%2Fremotes%2Fgithub%2Ffix%2Fvisible-branch":
        return None
    if path == "repos/joustonhuang/unifai/commits/refs%2Fremotes%2Forigin%2Ffix%2Fvisible-branch":
        return None
    if path == "repos/joustonhuang/unifai/commits/fix%2Fvisible-branch":
        return None
    if path == "repos/joustonhuang/unifai/commits/origin%2Ffix%2Fvisible-branch":
        return None
    if path == "repos/joustonhuang/unifai/git/ref/heads/refs/remotes/github/fix/visible-branch":
        return None
    if path == "repos/joustonhuang/unifai/git/ref/heads/refs/remotes/origin/fix/visible-branch":
        return None
    if path == "repos/joustonhuang/unifai/git/ref/heads/github/fix/visible-branch":
        return None
    if path == "repos/joustonhuang/unifai/git/ref/heads/origin/fix/visible-branch":
        return None
    if path == "repos/joustonhuang/unifai/git/ref/heads/fix/visible-branch":
        return {"object": {"sha": "feed123", "type": "commit"}}
    if path == "repos/joustonhuang/unifai/git/ref/tags/refs/remotes/github/fix/visible-branch":
        return None
    if path == "repos/joustonhuang/unifai/git/ref/tags/refs/remotes/origin/fix/visible-branch":
        return None
    if path == "repos/joustonhuang/unifai/git/ref/tags/github/fix/visible-branch":
        return None
    if path == "repos/joustonhuang/unifai/git/ref/tags/origin/fix/visible-branch":
        return None
    if path == "repos/joustonhuang/unifai/git/ref/tags/fix/visible-branch":
        return None
    if path == "repos/joustonhuang/unifai/commits/feed123/check-runs?per_page=100&page=1":
        return {
            "check_runs": [
                {
                    "id": 301,
                    "name": "Bootstrap Installer Preflight",
                    "status": "completed",
                    "conclusion": "success",
                    "html_url": "https://example.invalid/remote-branch-preflight",
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
                "start_line": 40,
                "message": "Process completed with exit code 1.",
            }
        ]
    raise AssertionError(f"unexpected path: {path}")


def directory_failure_get(path: str):
    if path == "repos/joustonhuang/unifai/commits/directory-ref":
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
                "path": ".github",
                "start_line": 71,
                "message": "Process completed with exit code 1.",
            }
        ]
    raise AssertionError(f"unexpected path: {path}")


def fake_subprocess_run(cmd, check, capture_output, text, timeout):
    if cmd == ["git", "remote", "get-url", "github"]:
        return FakeCompletedProcess("https://github.com/joustonhuang/unifai.git\n")
    if cmd == ["git", "remote", "get-url", "origin"]:
        return FakeCompletedProcess("https://gitlab.com/example/unifai.git\n")
    if cmd == ["git", "show", "def456:.github/workflows/bootstrap-preflight.yml"]:
        lines = [f"line {i}" for i in range(1, 57)]
        lines[37] = '      - name: Run bootstrap installer preflight'
        lines[38] = '        run: |'
        lines[39] = '          chmod +x scripts/bootstrap_installer_preflight.sh'
        lines[40] = '          ./scripts/bootstrap_installer_preflight.sh'
        lines[41] = ''
        return FakeCompletedProcess("\n".join(lines) + "\n")
    if cmd == ["git", "show", "def456:.github/workflows/unifai-ci.yml"]:
        lines = [f"workflow line {i}" for i in range(1, 181)]
        lines[68] = '            echo "❌ CRITICAL: Cannot parse pinned commit from lock file"'
        lines[69] = "            exit 1"
        lines[70] = "          fi"
        lines[71] = ''
        lines[72] = '          echo "📋 Pinned commit from lock:  $PINNED_COMMIT"'
        return FakeCompletedProcess("\n".join(lines) + "\n")
    if cmd == ["git", "show", "def456:.github"]:
        raise module.subprocess.CalledProcessError(returncode=128, cmd=cmd)
    raise AssertionError(f"unexpected subprocess command: {cmd}")


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

code, stdout, stderr = run_case(
    remote_branch_get,
    [str(SCRIPT), "github/fix/visible-branch"],
    fake_subprocess_run=fake_subprocess_run,
)
print(stdout, end="")
print(stderr, end="")
if code != 0:
    print("[FAIL] Expected GitHub remote-tracking branch case to return exit code 0.")
    raise SystemExit(1)
if "Ref: github/fix/visible-branch" not in stdout:
    print("[FAIL] Expected remote-tracking branch ref line missing.")
    raise SystemExit(1)
if "SHA: feed123" not in stdout:
    print("[FAIL] Expected remote-tracking branch SHA resolution missing.")
    raise SystemExit(1)

code, stdout, stderr = run_case(
    remote_branch_get,
    [str(SCRIPT), "refs/remotes/github/fix/visible-branch"],
    fake_subprocess_run=fake_subprocess_run,
)
print(stdout, end="")
print(stderr, end="")
if code != 0:
    print("[FAIL] Expected refs/remotes GitHub remote-tracking branch case to return exit code 0.")
    raise SystemExit(1)
if "Ref: refs/remotes/github/fix/visible-branch" not in stdout:
    print("[FAIL] Expected refs/remotes remote-tracking branch ref line missing.")
    raise SystemExit(1)
if "SHA: feed123" not in stdout:
    print("[FAIL] Expected refs/remotes remote-tracking branch SHA resolution missing.")
    raise SystemExit(1)

code, stdout, stderr = run_case(
    remote_branch_get,
    [str(SCRIPT), "refs/remotes/origin/fix/visible-branch"],
    fake_subprocess_run=fake_subprocess_run,
)
print(stdout, end="")
print(stderr, end="")
if code != 1:
    print("[FAIL] Expected non-GitHub remote-tracking branch case to fail closed.")
    raise SystemExit(1)
if "Could not resolve SHA for joustonhuang/unifai@refs/remotes/origin/fix/visible-branch" not in stderr:
    print("[FAIL] Expected non-GitHub remote-tracking branch failure line missing.")
    raise SystemExit(1)
if "remote-tracking refs must point at a GitHub-backed remote" not in stderr:
    print("[FAIL] Expected non-GitHub remote-tracking guidance missing.")
    raise SystemExit(1)

code, stdout, stderr = run_case(
    failure_get,
    [str(SCRIPT), "bad-ref"],
    fake_subprocess_run=fake_subprocess_run,
)
print(stdout, end="")
print(stderr, end="")
if code != 1:
    print("[FAIL] Expected failure case to return exit code 1.")
    raise SystemExit(1)
if "Bootstrap Installer Preflight: status=completed conclusion=failure" not in stdout:
    print("[FAIL] Expected failure-case check status line missing.")
    raise SystemExit(1)
if "likely root signal: failure: .github/workflows/bootstrap-preflight.yml line 40 — Process completed with exit code 1." not in stdout:
    print("[FAIL] Expected root-signal summary missing from failure case.")
    raise SystemExit(1)
if "source context (.github/workflows/bootstrap-preflight.yml:38-42 @ def456):" not in stdout:
    print("[FAIL] Expected direct-file source-context header missing from failure case.")
    raise SystemExit(1)
if "    > 40:           chmod +x scripts/bootstrap_installer_preflight.sh" not in stdout:
    print("[FAIL] Expected direct-file highlighted source-context line missing from failure case.")
    raise SystemExit(1)
if "annotations:" not in stdout or "Node.js 20 actions are deprecated." not in stdout or "Process completed with exit code 1." not in stdout:
    print("[FAIL] Expected failure annotations missing from failure case.")
    raise SystemExit(1)
if "... 95 more annotation(s) omitted" not in stdout and "… 95 more annotation(s) omitted" not in stdout:
    print("[FAIL] Expected annotation omission summary missing from failure case.")
    raise SystemExit(1)

code, stdout, stderr = run_case(
    directory_failure_get,
    [str(SCRIPT), "directory-ref"],
    fake_subprocess_run=fake_subprocess_run,
)
print(stdout, end="")
print(stderr, end="")
if code != 1:
    print("[FAIL] Expected directory-level failure case to return exit code 1.")
    raise SystemExit(1)
if "likely root signal: failure: .github line 71 — Process completed with exit code 1." not in stdout:
    print("[FAIL] Expected directory-level root-signal summary missing.")
    raise SystemExit(1)
if "source context (.github/workflows/unifai-ci.yml:69-73 @ def456):" not in stdout:
    print("[FAIL] Expected hinted source-context header missing from directory-level failure case.")
    raise SystemExit(1)
if "    > 71:           fi" not in stdout:
    print("[FAIL] Expected hinted highlighted source-context line missing from directory-level failure case.")
    raise SystemExit(1)
if "GitHub highlighted a generic shell control line" not in stdout:
    print("[FAIL] Expected generic-shell-line note missing from directory-level failure case.")
    raise SystemExit(1)
if "nearest failure-looking line: .github/workflows/unifai-ci.yml:70 — exit 1" not in stdout:
    print("[FAIL] Expected nearest failure-looking line hint missing from directory-level failure case.")
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

bad_credentials_error = urllib.error.HTTPError(
    "https://api.github.com/repos/joustonhuang/unifai/commits/visible-ref",
    401,
    "Unauthorized",
    hdrs=None,
    fp=None,
)
stderr = io.StringIO()
with contextlib.redirect_stderr(stderr):
    module.explain_http_error(
        bad_credentials_error,
        "https://api.github.com/repos/joustonhuang/unifai/commits/visible-ref",
        '{"message":"Bad credentials","documentation_url":"https://docs.github.com/rest","status":"401"}',
    )
bad_credentials_output = stderr.getvalue()
print(bad_credentials_output, end="")
if "appears invalid" not in bad_credentials_output:
    print("[FAIL] Expected invalid-token guidance missing from 401 explanation.")
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
