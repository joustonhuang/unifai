#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_REPO = os.environ.get("REPO_SLUG", "joustonhuang/unifai")
DEFAULT_REQUIRED = ["Bootstrap Installer Preflight"]
OPTIONAL_IF_PRESENT = ["Core Modules & Exoskeleton E2E", "smoke-test"]
API_BASE = "https://api.github.com"
MAX_ANNOTATIONS_PER_LEVEL = 5
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


def github_get(path: str):
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


def resolve_sha(repo: str, ref: str) -> str:
    data = github_get(f"repos/{repo}/commits/{urllib.parse.quote(ref, safe='')}")
    sha = data.get("sha")
    if not sha:
        print(f"[FAIL] Could not resolve SHA for {repo}@{ref}", file=sys.stderr)
        raise SystemExit(1)
    return sha


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
