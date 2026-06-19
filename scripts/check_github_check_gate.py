#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_REPO = os.environ.get("REPO_SLUG", "joustonhuang/unifai")
DEFAULT_REQUIRED = ["Bootstrap Installer Preflight"]
OPTIONAL_IF_PRESENT = ["Core Modules & Exoskeleton E2E", "smoke-test"]
API_BASE = "https://api.github.com"
MAX_ANNOTATIONS_PER_LEVEL = 5


def usage() -> int:
    print(
        "Usage: python3 scripts/check_github_check_gate.py <ref-or-sha> [check name ...]",
        file=sys.stderr,
    )
    print("Prints GitHub check-run status for a ref and explains failing gates.", file=sys.stderr)
    return 2


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
        print(f"[FAIL] GitHub API {exc.code} for {url}", file=sys.stderr)
        if body:
            print(body, file=sys.stderr)
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


def summarize_annotations(annotations: list[dict]) -> None:
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
            summarize_annotations(annotations)

    for name in OPTIONAL_IF_PRESENT:
        check_run = collect_check_run(check_runs, name)
        if not check_run:
            print(f"[INFO] Optional check not present: {name}")
            continue
        print_check("[INFO] ", check_run)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
