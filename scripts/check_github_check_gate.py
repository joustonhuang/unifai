#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import re
from datetime import datetime, timedelta, timezone
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_REPO = os.environ.get("REPO_SLUG", "joustonhuang/unifai")
DEFAULT_REQUIRED = ["Bootstrap Installer Preflight"]
OPTIONAL_IF_PRESENT = ["Core Modules & Exoskeleton E2E", "smoke-test"]
API_BASE = "https://api.github.com"
MAX_ANNOTATIONS_PER_LEVEL = 5
MAX_LOG_EXCERPT_LINES = 12
GENERIC_EXIT_MESSAGES = {
    "Process completed with exit code 1.",
}
SHELL_CONTROL_LINES = {
    "fi",
    "done",
    "then",
    "else",
    "elif",
    "}",
}
CHECK_NAME_SOURCE_HINTS = {
    "Bootstrap Installer Preflight": [
        ".github/workflows/bootstrap-preflight.yml",
        ".github/workflows/unifai-ci.yml",
    ],
    "smoke-test": [
        ".github/workflows/gaia-smoke.yml",
    ],
}
_GH_AUTHENTICATED: bool | None = None


def usage() -> int:
    print(
        "Usage: python3 scripts/check_github_check_gate.py <ref-or-sha> [check name ...]",
        file=sys.stderr,
    )
    print("Prints GitHub check-run status for a ref and explains failing gates.", file=sys.stderr)
    return 2


def explain_http_error(exc: urllib.error.HTTPError, url: str, body: str) -> None:
    print(f"[FAIL] GitHub API {exc.code} for {url}", file=sys.stderr)
    if body:
        print(body, file=sys.stderr)

    lower_body = body.lower()
    if exc.code in {401, 403, 429} and (
        "rate limit" in lower_body
        or "secondary rate limit" in lower_body
        or "bad credentials" in lower_body
        or exc.code in {401, 429}
    ):
        print(
            "[INFO] If this host should query private or rate-limited GitHub state, authenticate gh or export GH_TOKEN/GITHUB_TOKEN before rerunning.",
            file=sys.stderr,
        )
    if exc.code == 401 and "bad credentials" in lower_body:
        print(
            "[INFO] The configured GH_TOKEN/GITHUB_TOKEN appears invalid; refresh the token or clear it before rerunning.",
            file=sys.stderr,
        )
    if exc.code == 403 and "rate limit" in lower_body:
        print(
            "[INFO] Unauthenticated GitHub API access can fail closed here even when the branch/ref itself is valid.",
            file=sys.stderr,
        )
    if exc.code == 422 and (
        "no commit found for sha" in lower_body
        or "no commit found" in lower_body
        or "unprocessable entity" in lower_body
    ):
        print(
            "[INFO] This usually means the ref/SHA is mistyped or not GitHub-visible yet; push the branch tip first or rerun with a GitHub-visible branch/ref.",
            file=sys.stderr,
        )


def gh_cli_authenticated() -> bool:
    global _GH_AUTHENTICATED
    if _GH_AUTHENTICATED is not None:
        return _GH_AUTHENTICATED

    if not shutil.which("gh"):
        _GH_AUTHENTICATED = False
        return _GH_AUTHENTICATED

    try:
        auth = subprocess.run(
            ["gh", "auth", "status"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        _GH_AUTHENTICATED = False
        return _GH_AUTHENTICATED

    _GH_AUTHENTICATED = auth.returncode == 0
    return _GH_AUTHENTICATED


def github_get_via_gh(path: str):
    if os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"):
        return None
    if not gh_cli_authenticated():
        return None

    try:
        proc = subprocess.run(
            ["gh", "api", path],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def github_get(path: str):
    gh_data = github_get_via_gh(path)
    if gh_data is not None:
        return gh_data

    url = f"{API_BASE}/{path.lstrip('/')}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "unifai-check-gate",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        explain_http_error(exc, url, body)
        raise SystemExit(1) from exc


def github_get_optional(path: str, allowed_codes: set[int] | None = None):
    gh_data = github_get_via_gh(path)
    if gh_data is not None:
        return gh_data

    url = f"{API_BASE}/{path.lstrip('/')}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "unifai-check-gate",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        if allowed_codes and exc.code in allowed_codes:
            return None
        explain_http_error(exc, url, body)
        raise SystemExit(1) from exc


def github_get_paged(path: str, list_key: str | None = None, per_page: int = 100):
    items = []
    page = 1
    while True:
        sep = '&' if '?' in path else '?'
        data = github_get(f"{path}{sep}per_page={per_page}&page={page}")
        page_items = data.get(list_key, []) if list_key else data
        if not isinstance(page_items, list):
            print(f"[FAIL] Expected paged GitHub response list for {path}", file=sys.stderr)
            raise SystemExit(1)
        items.extend(page_items)
        if len(page_items) < per_page:
            return items
        page += 1


def github_remote_branch_candidate(ref: str) -> str | None:
    if ref.startswith("refs/remotes/"):
        parts = ref.split("/", 3)
        if len(parts) == 4:
            remote = parts[2]
            branch = parts[3]
        else:
            return None
    elif ref.startswith("refs/"):
        return None
    elif "/" in ref:
        remote, branch = ref.split("/", 1)
    else:
        return None

    try:
        proc = subprocess.run(
            ["git", "remote", "get-url", remote],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None

    url = proc.stdout.strip()
    if "github.com" not in url and not url.startswith("git@github.com:"):
        return None
    return branch or None


def local_branch_candidate(ref: str) -> str | None:
    if ref.startswith("refs/heads/"):
        branch = ref[len("refs/heads/") :]
        return branch or None
    return None


def resolve_sha(repo: str, ref: str) -> str:
    candidates: list[str] = []
    for candidate in [ref, local_branch_candidate(ref), github_remote_branch_candidate(ref)]:
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        data = github_get_optional(
            f"repos/{repo}/commits/{urllib.parse.quote(candidate, safe='')}",
            allowed_codes={404, 422},
        )
        if data and data.get("sha"):
            return str(data["sha"])

        for kind in ("heads", "tags"):
            ref_data = github_get_optional(
                f"repos/{repo}/git/ref/{kind}/{urllib.parse.quote(candidate, safe='/')}",
                allowed_codes={404},
            )
            if not ref_data:
                continue
            obj = ref_data.get("object") or {}
            sha = obj.get("sha")
            if sha:
                return str(sha)

    print(f"[FAIL] Could not resolve SHA for {repo}@{ref}", file=sys.stderr)
    print(
        "[INFO] Use a GitHub-visible branch, tag, or commit SHA; remote-tracking refs must point at a GitHub-backed remote.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def collect_check_run(check_runs, name: str):
    matches = [cr for cr in check_runs if cr.get("name") == name]
    return matches[-1] if matches else None


def print_check(prefix: str, check_run: dict):
    print(
        f"{prefix}{check_run.get('name')}: status={check_run.get('status')} conclusion={check_run.get('conclusion')}"
    )
    if check_run.get("html_url"):
        print(f"  details: {check_run['html_url']}")


def fetch_annotations(repo: str, check_run_id: int):
    return github_get_paged(f"repos/{repo}/check-runs/{check_run_id}/annotations")


def load_file_at_ref(ref: str, path: str) -> list[str] | None:
    try:
        proc = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return proc.stdout.splitlines()


def run_gh_api_text(path: str) -> str | None:
    if not gh_cli_authenticated():
        return None

    try:
        proc = subprocess.run(
            ["gh", "api", path],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return proc.stdout


def extract_run_id(details_url: str | None) -> int | None:
    if not details_url:
        return None
    match = re.search(r"/actions/runs/(\d+)(?:/|$)", details_url)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def resolve_source_path(ref: str, annotation: dict, check_name: str) -> tuple[str, list[str]] | None:
    path = annotation.get("path")
    if not path:
        return None

    try:
        line_no = int(annotation.get("start_line"))
    except (TypeError, ValueError):
        line_no = None

    direct = load_file_at_ref(ref, path)
    if direct is not None and (line_no is None or 1 <= line_no <= len(direct)):
        return path, direct

    fallback = (path, direct) if direct is not None else None
    for candidate in CHECK_NAME_SOURCE_HINTS.get(check_name, []):
        hinted = load_file_at_ref(ref, candidate)
        if hinted is None:
            continue
        if line_no is None or 1 <= line_no <= len(hinted):
            return candidate, hinted
        if fallback is None:
            fallback = (candidate, hinted)

    return fallback


def find_workflow_step_context(ref: str, check_name: str, step_name: str) -> tuple[str, int, list[str]] | None:
    needle = f"- name: {step_name}"
    for candidate in CHECK_NAME_SOURCE_HINTS.get(check_name, []):
        lines = load_file_at_ref(ref, candidate)
        if lines is None:
            continue
        for idx, line in enumerate(lines, start=1):
            if line.strip() == needle:
                return candidate, idx, lines
    return None


def find_nearby_failure_hint(lines: list[str], line_no: int) -> tuple[int, str] | None:
    start = max(1, line_no - 8)
    end = min(len(lines), line_no + 1)
    for current in range(end, start - 1, -1):
        content = lines[current - 1].strip()
        if content.startswith("echo ") and ("❌" in content or "CRITICAL" in content or "FAIL" in content):
            return current, content
        if content == "exit 1":
            return current, content
    return None


def print_annotation_source_context(ref: str, annotation: dict, check_name: str) -> None:
    raw_path = annotation.get("path")
    line = annotation.get("start_line")
    if not raw_path or line in {None, ""}:
        return

    try:
        line_no = int(line)
    except (TypeError, ValueError):
        return
    if line_no < 1:
        return

    resolved = resolve_source_path(ref, annotation, check_name)
    if not resolved:
        return

    path, lines = resolved
    if line_no > len(lines):
        return

    start = max(1, line_no - 2)
    end = min(len(lines), line_no + 2)
    print(f"  source context ({path}:{start}-{end} @ {ref}):")
    for current in range(start, end + 1):
        marker = ">" if current == line_no else " "
        print(f"    {marker} {current}: {lines[current - 1]}")

    message = str(annotation.get("message") or "")
    highlighted = lines[line_no - 1].strip()
    if message in GENERIC_EXIT_MESSAGES and highlighted in SHELL_CONTROL_LINES:
        hint = find_nearby_failure_hint(lines, line_no)
        print(
            "  note: GitHub highlighted a generic shell control line, so the true failure may be earlier in the same run block."
        )
        if hint:
            hint_line, hint_text = hint
            print(f"  nearest failure-looking line: {path}:{hint_line} — {hint_text}")


def print_step_source_context(ref: str, check_name: str, step_name: str) -> None:
    resolved = find_workflow_step_context(ref, check_name, step_name)
    if not resolved:
        return

    path, line_no, lines = resolved
    start = max(1, line_no - 1)
    end = min(len(lines), line_no + 4)
    print(f"  workflow step context ({path}:{start}-{end} @ {ref}):")
    for current in range(start, end + 1):
        marker = ">" if current == line_no else " "
        print(f"    {marker} {current}: {lines[current - 1]}")


def fetch_actions_job(repo: str, check_run: dict) -> dict | None:
    run_id = extract_run_id(check_run.get("details_url"))
    check_run_id = check_run.get("id")
    if run_id is None or check_run_id is None:
        return None

    jobs = github_get_paged(f"repos/{repo}/actions/runs/{run_id}/jobs", list_key="jobs")
    for job in jobs:
        if job.get("id") == check_run_id:
            return job
    for job in jobs:
        if job.get("name") == check_run.get("name"):
            return job
    return None


def fetch_actions_job_log(repo: str, job_id: int) -> list[str] | None:
    text = run_gh_api_text(f"repos/{repo}/actions/jobs/{job_id}/logs")
    if text is None:
        return None
    return text.splitlines()


def parse_github_timestamp(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw).astimezone(timezone.utc)
    except ValueError:
        return None


def parse_log_line_timestamp(line: str) -> datetime | None:
    token = line.split(" ", 1)[0]
    return parse_github_timestamp(token)


def extract_failing_step_log_excerpt(
    log_lines: list[str], started_at: str | None, completed_at: str | None
) -> list[str]:
    start_ts = parse_github_timestamp(started_at)
    end_ts = parse_github_timestamp(completed_at)
    if start_ts is None or end_ts is None:
        return []
    end_ts = end_ts + timedelta(seconds=1)

    bounded: list[tuple[int, str]] = []
    for idx, line in enumerate(log_lines):
        ts = parse_log_line_timestamp(line)
        if ts is None:
            continue
        if start_ts <= ts <= end_ts:
            bounded.append((idx, line))
    if not bounded:
        return []

    error_idx = None
    for idx, line in bounded:
        if "##[error]" in line or "[FAIL]" in line or "fatal:" in line:
            error_idx = idx
    # Prefer the last failure marker inside the step window because bootstrap preflight
    # intentionally runs many red-path smoke tests before the real terminal failure.
    if error_idx is None:
        return []

    start_idx = bounded[0][0]
    last_idx = bounded[-1][0]
    start = max(start_idx, error_idx - 4)
    end = min(last_idx + 1, error_idx + MAX_LOG_EXCERPT_LINES)
    return log_lines[start:end]


def print_log_excerpt(repo: str, check_run: dict, step: dict) -> None:
    job_id = check_run.get("id")
    if not isinstance(job_id, int):
        return
    log_lines = fetch_actions_job_log(repo, job_id)
    if not log_lines:
        return
    excerpt = extract_failing_step_log_excerpt(
        log_lines,
        step.get("started_at"),
        step.get("completed_at"),
    )
    if not excerpt:
        return
    print("  failing step log excerpt:")
    for line in excerpt:
        print(f"    {line}")


def summarize_job_steps(ref: str, repo: str, check_name: str, check_run: dict) -> None:
    job = fetch_actions_job(repo, check_run)
    if not job:
        return

    failing_steps = [
        step
        for step in job.get("steps", [])
        if step.get("conclusion") == "failure"
    ]
    if not failing_steps:
        return

    print("  failing job step(s):")
    for step in failing_steps:
        print(
            f"    - step {step.get('number')}: {step.get('name')}"
            f" (started {step.get('started_at')}, completed {step.get('completed_at')})"
        )
        print_step_source_context(ref, check_name, str(step.get("name") or ""))
        print_log_excerpt(repo, check_run, step)


def summarize_annotations(ref: str, check_name: str, annotations: list[dict]) -> None:
    if not annotations:
        print("  annotations: none exposed")
        return

    grouped: dict[str, list[dict]] = {}
    for ann in annotations:
        level = ann.get("annotation_level") or "notice"
        grouped.setdefault(level, []).append(ann)

    priority = ["failure", "warning", "notice"]
    root = next((anns[0] for level in priority for anns in [grouped.get(level, [])] if anns), None)
    if root:
        print(
            "  likely root signal: "
            f"{root.get('annotation_level')}: {root.get('path')} line {root.get('start_line')}"
            f" — {root.get('message')}"
        )
        print_annotation_source_context(ref, root, check_name)

    print("  annotations:")
    for level in priority + sorted(k for k in grouped if k not in priority):
        anns = grouped.get(level, [])
        for ann in anns[:MAX_ANNOTATIONS_PER_LEVEL]:
            print(
                f"    - {ann.get('annotation_level')}: {ann.get('path')}"
                f" line {ann.get('start_line')} — {ann.get('message')}"
            )
        omitted = len(anns) - MAX_ANNOTATIONS_PER_LEVEL
        if omitted > 0:
            print(f"    - {level}: … {omitted} more annotation(s) omitted")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        return usage()

    ref = sys.argv[1]
    required = sys.argv[2:] or DEFAULT_REQUIRED
    repo = DEFAULT_REPO

    sha = resolve_sha(repo, ref)
    print(f"Repo: {repo}")
    print(f"Ref: {ref}")
    print(f"SHA: {sha}")

    check_runs = github_get_paged(f"repos/{repo}/commits/{sha}/check-runs", list_key="check_runs")
    if not check_runs:
        print("[FAIL] No check runs found for this commit.")
        return 1

    failures = 0
    for name in required:
        check_run = collect_check_run(check_runs, name)
        if not check_run:
            print(f"[FAIL] Missing required check: {name}")
            failures += 1
            continue
        print_check("", check_run)
        if check_run.get("conclusion") != "success":
            failures += 1
            summarize_job_steps(sha, repo, name, check_run)
            annotations = fetch_annotations(repo, check_run["id"])
            summarize_annotations(sha, name, annotations)

    for name in OPTIONAL_IF_PRESENT:
        check_run = collect_check_run(check_runs, name)
        if not check_run:
            print(f"[INFO] Optional check not present: {name}")
            continue
        print_check("[INFO] ", check_run)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
