#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
STAGE50 = REPO_ROOT / "little7-installer" / "stages" / "50_openclaw.sh"
STAGE60 = REPO_ROOT / "little7-installer" / "stages" / "60_telegram.sh"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def passed(message: str) -> None:
    print(f"[PASS] {message}")


def require(text: str, needle: str, message: str) -> None:
    if needle not in text:
        fail(message)
    passed(message)


def extract_config(text: str) -> str:
    match = re.search(
        r"cat > \"\$\{OPENCLAW_CONFIG\}\" <<'EOF'\n(?P<body>.*?)\nEOF",
        text,
        re.DOTALL,
    )
    if not match:
        fail("Stage 50 config heredoc is extractable")
    return match.group("body")


stage50 = STAGE50.read_text(encoding="utf-8")
stage60 = STAGE60.read_text(encoding="utf-8")

for stage in (STAGE50, STAGE60):
    result = subprocess.run(
        ["bash", "-n", str(stage)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        fail(f"{stage.name} passes bash -n: {result.stderr.strip()}")
    passed(f"{stage.name} passes bash -n")

require(
    stage50,
    'OPENCLAW_CONFIG="${OPENCLAW_CONFIG_DIR}/openclaw.json"',
    "Stage 50 writes the canonical OpenClaw config path",
)
require(
    stage60,
    'OPENCLAW_CONFIG="${HOME}/.openclaw/openclaw.json"',
    "Stage 60 reads the canonical OpenClaw config path",
)
require(
    stage60,
    'pathlib.Path.home() / ".openclaw" / "openclaw.json"',
    "Stage 60 updates the same canonical config path",
)

if "openclaw.json5" in stage50 or "openclaw.json5" in stage60:
    fail("Installer stages do not reference the obsolete openclaw.json5 path")
passed("Installer stages do not reference the obsolete openclaw.json5 path")

config = extract_config(stage50)
require(config, 'mode: "local"', "Generated config enables gateway.mode=local")
require(
    config,
    'workspace: "~/.openclaw/workspace"',
    "Generated config pins the default workspace",
)
require(config, "enabled: false", "Telegram remains disabled until Stage 60")

for stale_model in ("codex-mini-latest", "openai-codex/gpt-5.4"):
    if stale_model in config:
        fail(f"Generated config does not pin stale model {stale_model}")
passed("Generated config leaves model selection to current OpenClaw configuration")

for secret_field in ("apiKey:", "OPENAI_API_KEY:", "ANTHROPIC_API_KEY:"):
    if secret_field in config:
        fail(f"Generated config does not persist secret field {secret_field}")
passed("Generated config does not persist provider secrets")

require(stage50, 'chmod 700 "${OPENCLAW_CONFIG_DIR}"', "Config directory is private")
require(stage50, 'chmod 600 "${OPENCLAW_CONFIG}"', "Config file is private")

print("[PASS] OpenClaw installer config contract looks sane")
