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
    ('GENERIC_EXIT_MESSAGES = {', 'GitHub check-gate inspector recognizes generic exit-code annotations'),
    ('SHELL_CONTROL_LINES = {', 'GitHub check-gate inspector recognizes shell control lines that can mispoint root cause'),
    ('CHECK_NAME_SOURCE_HINTS = {', 'GitHub check-gate inspector defines check-name source hints for workflow annotations'),
    ('def github_get_paged(path: str, list_key: str | None = None, per_page: int = 100):', 'GitHub check-gate inspector defines paged GitHub fetching'),
    ('def explain_http_error(exc: urllib.error.HTTPError, url: str, body: str) -> None:', 'GitHub check-gate inspector defines targeted HTTP error explanation'),
    ('export GH_TOKEN/GITHUB_TOKEN before rerunning.', 'GitHub check-gate inspector suggests token auth on API auth/rate-limit failures'),
    ('appears invalid; refresh the token or clear it before rerunning.', 'GitHub check-gate inspector explains bad-token recovery'),
    ('not GitHub-visible yet; push the branch tip first or rerun with a GitHub-visible branch/ref.', 'GitHub check-gate inspector explains 422 unknown-ref recovery'),
    ('def load_file_at_ref(ref: str, path: str) -> list[str] | None:', 'GitHub check-gate inspector can load source files from an exact git ref'),
    ('["git", "show", f"{ref}:{path}"]', 'GitHub check-gate inspector shells out to git show for exact ref/path context'),
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
    ('explain_http_error(exc, url, body)', 'GitHub check-gate inspector routes HTTP failures through the explainer'),
    ('summarize_annotations(sha, name, annotations)', 'GitHub check-gate inspector uses annotation summarization for failing checks'),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print('[PASS] GitHub check-gate contract looks sane')
