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
    return github_get(f"repos/{repo}/check-runs/{check_run_id}/annotations")


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

    data = github_get(f"repos/{repo}/commits/{sha}/check-runs")
    check_runs = data.get("check_runs", [])
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
            if annotations:
                print("  annotations:")
                for ann in annotations:
                    print(
                        f"    - {ann.get('annotation_level')}: {ann.get('path')}"
                        f" line {ann.get('start_line')} — {ann.get('message')}"
                    )
            else:
                print("  annotations: none exposed")

    for name in OPTIONAL_IF_PRESENT:
        check_run = collect_check_run(check_runs, name)
        if not check_run:
            print(f"[INFO] Optional check not present: {name}")
            continue
        print_check("[INFO] ", check_run)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
