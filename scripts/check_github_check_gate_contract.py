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
    ('def github_get_paged(path: str, list_key: str | None = None, per_page: int = 100):', 'GitHub check-gate inspector defines paged GitHub fetching'),
    ('def explain_http_error(exc: urllib.error.HTTPError, url: str, body: str) -> None:', 'GitHub check-gate inspector defines targeted HTTP error explanation'),
    ('export GH_TOKEN/GITHUB_TOKEN before rerunning.', 'GitHub check-gate inspector suggests token auth on API auth/rate-limit failures'),
    ('appears invalid; refresh the token or clear it before rerunning.', 'GitHub check-gate inspector explains bad-token recovery'),
    ('not GitHub-visible yet; push the branch tip first or rerun with a GitHub-visible branch/ref.', 'GitHub check-gate inspector explains 422 unknown-ref recovery'),
    ('def summarize_annotations(annotations: list[dict]) -> None:', 'GitHub check-gate inspector defines annotation summarization'),
    ('grouped.setdefault(level, []).append(ann)', 'GitHub check-gate inspector groups annotations by level'),
    ('priority = ["failure", "warning", "notice"]', 'GitHub check-gate inspector prioritizes failures ahead of warnings/notices'),
    ('"  likely root signal: "', 'GitHub check-gate inspector prints a root-signal summary'),
    ('omitted = len(anns) - MAX_ANNOTATIONS_PER_LEVEL', 'GitHub check-gate inspector summarizes omitted annotations'),
    ('explain_http_error(exc, url, body)', 'GitHub check-gate inspector routes HTTP failures through the explainer'),
    ('summarize_annotations(annotations)', 'GitHub check-gate inspector uses annotation summarization for failing checks'),
]

for needle, message in required:
    if needle not in text:
        fail(message)
    ok(message)

print('[PASS] GitHub check-gate contract looks sane')
