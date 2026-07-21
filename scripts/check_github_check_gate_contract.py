#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_github_check_gate.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


text = SCRIPT.read_text(encoding="utf-8")

required = [
    ('MAX_ANNOTATIONS_PER_LEVEL = 5', 'GitHub check-gate inspector caps per-level annotation output'),
    ('MAX_LOG_EXCERPT_LINES = 12', 'GitHub check-gate inspector caps failing-step log excerpts'),
    ('GENERIC_EXIT_MESSAGES = {', 'GitHub check-gate inspector recognizes generic exit-code annotations'),
    ('SHELL_CONTROL_LINES = {', 'GitHub check-gate inspector recognizes shell control lines that can mispoint root cause'),
    ('CHECK_NAME_SOURCE_HINTS = {', 'GitHub check-gate inspector defines check-name source hints for workflow annotations'),
    ('def github_get_paged(path: str, list_key: str | None = None, per_page: int = 100):', 'GitHub check-gate inspector defines paged GitHub fetching'),
    ('def github_get_optional(path: str, allowed_codes: set[int] | None = None):', 'GitHub check-gate inspector defines optional GitHub fetching for ref fallbacks'),
    ('def explain_http_error(exc: urllib.error.HTTPError, url: str, body: str) -> None:', 'GitHub check-gate inspector defines targeted HTTP error explanation'),
    ('_GH_AUTHENTICATED: bool | None = None', 'GitHub check-gate inspector caches gh authentication state for repeated API reads'),
    ('def gh_cli_authenticated() -> bool:', 'GitHub check-gate inspector can detect authenticated gh availability'),
    ('def github_get_via_gh(path: str):', 'GitHub check-gate inspector can satisfy JSON API reads through authenticated gh'),
    ('export GH_TOKEN/GITHUB_TOKEN before rerunning.', 'GitHub check-gate inspector suggests token auth on API auth/rate-limit failures'),
    ('appears invalid; refresh the token or clear it before rerunning.', 'GitHub check-gate inspector explains bad-token recovery'),
    ('not GitHub-visible yet; push the branch tip first or rerun with a GitHub-visible branch/ref.', 'GitHub check-gate inspector explains 422 unknown-ref recovery'),
    ('def load_file_at_ref(ref: str, path: str) -> list[str] | None:', 'GitHub check-gate inspector can load source files from an exact git ref'),
    ('["git", "show", f"{ref}:{path}"]', 'GitHub check-gate inspector shells out to git show for exact ref/path context'),
    ('def github_remote_branch_candidate(ref: str) -> str | None:', 'GitHub check-gate inspector can normalize GitHub remote-tracking refs to branch names'),
    ('["git", "remote", "get-url", remote]', 'GitHub check-gate inspector checks whether a remote-tracking ref belongs to a GitHub-backed remote'),
    ('f"repos/{repo}/git/ref/{kind}/{urllib.parse.quote(candidate, safe=\'/\')}"', 'GitHub check-gate inspector falls back to GitHub ref resolution for branch/tag refs'),
    ('remote-tracking refs must point at a GitHub-backed remote.', 'GitHub check-gate inspector explains the remote-tracking ref boundary'),
    ('def resolve_source_path(ref: str, annotation: dict, check_name: str) -> tuple[str, list[str]] | None:', 'GitHub check-gate inspector can fall back from directory-level annotations to hinted workflow files'),
    ('for candidate in CHECK_NAME_SOURCE_HINTS.get(check_name, []):', 'GitHub check-gate inspector consults per-check workflow hints when direct file lookup fails'),
    ('def find_nearby_failure_hint(lines: list[str], line_no: int) -> tuple[int, str] | None:', 'GitHub check-gate inspector can scan nearby lines for likely failure hints'),
    ('content == "exit 1"', 'GitHub check-gate inspector treats exit 1 as a nearby failure hint'),
    ('def print_annotation_source_context(ref: str, annotation: dict, check_name: str) -> None:', 'GitHub check-gate inspector defines source-context rendering for root annotations'),
    ('print(f"  source context ({path}:{start}-{end} @ {ref}):")', 'GitHub check-gate inspector prints source-context headers'),
    ('message in GENERIC_EXIT_MESSAGES and highlighted in SHELL_CONTROL_LINES', 'GitHub check-gate inspector detects generic shell-line annotations that can mislead diagnosis'),
    ('GitHub highlighted a generic shell control line', 'GitHub check-gate inspector warns when GitHub points at a generic shell control line'),
    ('nearest failure-looking line: {path}:{hint_line} — {hint_text}', 'GitHub check-gate inspector prints the nearest failure-looking line hint when available'),
    ('def summarize_annotations(ref: str, check_name: str, annotations: list[dict]) -> None:', 'GitHub check-gate inspector defines annotation summarization'),
    ('grouped.setdefault(level, []).append(ann)', 'GitHub check-gate inspector groups annotations by level'),
    ('priority = ["failure", "warning", "notice"]', 'GitHub check-gate inspector prioritizes failures ahead of warnings/notices'),
    ('"  likely root signal: "', 'GitHub check-gate inspector prints a root-signal summary'),
    ('print_annotation_source_context(ref, root, check_name)', 'GitHub check-gate inspector prints source context for the root signal when possible'),
    ('omitted = len(anns) - MAX_ANNOTATIONS_PER_LEVEL', 'GitHub check-gate inspector summarizes omitted annotations'),
    ('gh_data = github_get_via_gh(path)', 'GitHub check-gate inspector prefers authenticated gh JSON before raw urllib fallback'),
    ('explain_http_error(exc, url, body)', 'GitHub check-gate inspector routes HTTP failures through the explainer'),
    ('def run_gh_api_text(path: str) -> str | None:', 'GitHub check-gate inspector can query GitHub Actions logs through gh when available'),
    ('["gh", "api", path]', 'GitHub check-gate inspector shells out to gh api for Actions job logs'),
    ('def extract_run_id(details_url: str | None) -> int | None:', 'GitHub check-gate inspector can derive workflow run ids from details URLs'),
    ('def find_workflow_step_context(ref: str, check_name: str, step_name: str) -> tuple[str, int, list[str]] | None:', 'GitHub check-gate inspector can resolve workflow step source context'),
    ('needle = f"- name: {step_name}"', 'GitHub check-gate inspector locates workflow steps by exact step name'),
    ('def print_step_source_context(ref: str, check_name: str, step_name: str) -> None:', 'GitHub check-gate inspector prints workflow step source context'),
    ('workflow step context ({path}:{start}-{end} @ {ref}):', 'GitHub check-gate inspector renders workflow step source context headers'),
    ('def fetch_actions_job(repo: str, check_run: dict) -> dict | None:', 'GitHub check-gate inspector can fetch the matching Actions job for a failing check'),
    ('github_get_paged(f"repos/{repo}/actions/runs/{run_id}/jobs", list_key="jobs")', 'GitHub check-gate inspector paginates GitHub Actions jobs for the workflow run'),
    ('def fetch_actions_job_log(repo: str, job_id: int) -> list[str] | None:', 'GitHub check-gate inspector can fetch Actions job logs'),
    ('run_gh_api_text(f"repos/{repo}/actions/jobs/{job_id}/logs")', 'GitHub check-gate inspector fetches Actions job logs through gh api'),
    ('def extract_failing_step_log_excerpt(', 'GitHub check-gate inspector can extract a bounded log excerpt for the failing step window'),
    ('if "##[error]" in line or "[FAIL]" in line or "fatal:" in line:', 'GitHub check-gate inspector recognizes fatal/error markers inside step logs'),
    ('def print_log_excerpt(repo: str, check_run: dict, step: dict) -> None:', 'GitHub check-gate inspector prints failing-step log excerpts when available'),
    ('print("  failing step log excerpt:")', 'GitHub check-gate inspector labels failing-step log excerpts clearly'),
    ('def summarize_job_steps(ref: str, repo: str, check_name: str, check_run: dict) -> None:', 'GitHub check-gate inspector summarizes failing Actions job steps'),
    ('print("  failing job step(s):")', 'GitHub check-gate inspector prints failing job step headers'),
    ('print_step_source_context(ref, check_name, str(step.get("name") or ""))', 'GitHub check-gate inspector attaches workflow context to failing steps'),
    ('print_log_excerpt(repo, check_run, step)', 'GitHub check-gate inspector attaches log excerpts to failing steps'),
    ('summarize_job_steps(sha, repo, name, check_run)', 'GitHub check-gate inspector summarizes failing job steps before annotations'),
    ('summarize_annotations(sha, name, annotations)', 'GitHub check-gate inspector uses annotation summarization for failing checks'),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print('[PASS] GitHub check-gate contract looks sane')
