#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
STAGE50 = REPO_ROOT / "little7-installer" / "stages" / "50_openclaw.sh"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


def extract_heredoc(text: str, prefix_pattern: str, terminator: str) -> str:
    pattern = re.compile(prefix_pattern + rf"\n(?P<body>.*?)\n{re.escape(terminator)}", re.S)
    match = pattern.search(text)
    if not match:
        fail(f"Could not extract heredoc for pattern: {prefix_pattern}")
    return match.group("body")


text = STAGE50.read_text(encoding="utf-8")

if 'OPENCLAW_CONFIG="${OPENCLAW_CONFIG_DIR}/openclaw.json"' not in text:
    fail("Stage 50 does not target ~/.openclaw/openclaw.json")
ok("Stage 50 targets the canonical ~/.openclaw/openclaw.json path")

config_body = extract_heredoc(text, r"cat > \"\$\{OPENCLAW_CONFIG\}\" <<'EOF'", "EOF")
launcher_body = extract_heredoc(text, r"sudo tee \"\$\{OPENCLAW_LAUNCHER\}\" >/dev/null <<'LAUNCHER'", "LAUNCHER")

checks = [
    ('gateway: {', 'OpenClaw config defines a gateway block'),
    ('mode: "local"', 'OpenClaw config enables gateway.mode=local'),
    ('workspace: "~/.openclaw/workspace"', 'OpenClaw config pins the default workspace'),
    ('default: "openai-codex/gpt-5.4"', 'OpenClaw config pins the expected default model'),
    ('enabled: false', 'Telegram stays disabled until later installer stages'),
]
for needle, message in checks:
    if needle not in config_body:
        fail(message)
    ok(message)

for forbidden in ('apiKey:', 'OPENAI_API_KEY:', 'ANTHROPIC_API_KEY:'):
    if forbidden in config_body:
        fail(f"OpenClaw config skeleton must not persist provider secrets ({forbidden})")
ok("OpenClaw config skeleton does not persist provider secrets")

launcher_checks = [
    ('openclaw gateway "$@"', 'Launcher executes OpenClaw through gateway entrypoint'),
    ('OPENAI_BASE_URL="http://127.0.0.1:${BILL_PROXY_PORT}"', 'Launcher injects OpenAI bill-proxy routing'),
    ('ANTHROPIC_BASE_URL="http://127.0.0.1:${BILL_PROXY_PORT}"', 'Launcher injects Anthropic bill-proxy routing'),
    ('OPENAI_API_KEY="$(cat "$GRANT_PATH")"', 'Launcher injects OpenAI credentials from SecretVault grants'),
    ('ANTHROPIC_API_KEY="$(cat "$GRANT_PATH")"', 'Launcher injects Anthropic credentials from SecretVault grants'),
]
for needle, message in launcher_checks:
    if needle not in launcher_body:
        fail(message)
    ok(message)

print("[PASS] Stage 50 OpenClaw config + launcher contract looks sane")
