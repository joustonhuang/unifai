#!/usr/bin/env bash
set -euo pipefail

echo "== Stage 60: Telegram Gateway Configuration =="

DST_BASE="/opt/little7"
SV_DIR="${DST_BASE}/supervisor/supervisor-secretvault"
MASTER_KEY_FILE="/etc/little7/secretvault_master.key"
OPENCLAW_CONFIG="${HOME}/.openclaw/openclaw.json5"

# -----------------------------------------------------------------------
# 1. Verify dependencies from earlier stages
# -----------------------------------------------------------------------
[ -f "${SV_DIR}/src/cli.js" ]          || { echo "[FAIL] SecretVault not installed. Run Stage 20."; exit 1; }
[ -f "${OPENCLAW_CONFIG}" ]             || { echo "[FAIL] OpenClaw not installed. Run Stage 50."; exit 1; }
sudo test -f "$MASTER_KEY_FILE"         || { echo "[FAIL] Master key missing. Run Stage 20."; exit 1; }

MASTER_KEY="$(sudo cat "$MASTER_KEY_FILE")"
export SECRETVAULT_MASTER_KEY="$MASTER_KEY"
SV="node ${SV_DIR}/src/cli.js"

# -----------------------------------------------------------------------
# 2. Prompt for Telegram bot token (simulates WebUI input)
# -----------------------------------------------------------------------
echo ""
echo "You need a Telegram bot token to continue."
echo "If you don't have one:"
echo "  1. Open Telegram, search @BotFather (official, blue checkmark)"
echo "  2. Send /newbot — follow the prompts"
echo "  3. Copy the token BotFather gives you"
echo ""

if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
  BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
  echo "[INFO] Using TELEGRAM_BOT_TOKEN from environment."
else
  if [ -e /dev/tty ]; then
    printf "Enter your Telegram Bot Token: " > /dev/tty
    IFS= read -r BOT_TOKEN < /dev/tty
  else
    echo "[SKIP] Non-interactive mode and TELEGRAM_BOT_TOKEN not set. Skipping Telegram setup."
    echo "  To configure later: TELEGRAM_BOT_TOKEN=<token> bash stages/60_telegram.sh"
    exit 0
  fi
fi

if [ -z "${BOT_TOKEN:-}" ]; then
  echo "[SKIP] No token provided. Skipping Telegram setup."
  exit 0
fi

# -----------------------------------------------------------------------
# 3. Seed telegram-bot-token into SecretVault
# -----------------------------------------------------------------------
echo "[1/3] Seeding telegram-bot-token into SecretVault..."
SEED_OUT="$($SV seed --alias telegram-bot-token --value "$BOT_TOKEN" 2>&1)"
if echo "$SEED_OUT" | grep -q '"ok":true'; then
  echo "[OK] telegram-bot-token stored in SecretVault"
else
  echo "[FAIL] Could not seed token: $SEED_OUT"
  exit 1
fi

# -----------------------------------------------------------------------
# 4. Enable Telegram in OpenClaw config
# -----------------------------------------------------------------------
echo "[2/3] Enabling Telegram channel in OpenClaw config..."

# Update the openclaw.json5 to enable Telegram
# We don't write the token here — it's injected at runtime via OPENCLAW_BOT_TOKEN env var
python3 - <<'PYEOF'
import re, pathlib, sys

config_path = pathlib.Path.home() / ".openclaw" / "openclaw.json5"
content = config_path.read_text()

# Enable telegram in the config
content = re.sub(
    r'(telegram:\s*\{[^}]*?enabled:\s*)false',
    r'\g<1>true',
    content,
    flags=re.DOTALL
)

# Remove the comment about apiKey injection (it's already handled)
config_path.write_text(content)
print("openclaw.json5 updated: telegram.enabled = true")
PYEOF

# -----------------------------------------------------------------------
# 5. Update openclaw-start launcher to also inject bot token
# -----------------------------------------------------------------------
echo "[3/3] Updating openclaw-start launcher with Telegram token injection..."
LAUNCHER="${DST_BASE}/bin/openclaw-start"

sudo tee "${LAUNCHER}" >/dev/null <<'LAUNCHER_EOF'
#!/usr/bin/env bash
# openclaw-start — World Physics injection wrapper (with Telegram)
# Injects both ANTHROPIC_API_KEY and OPENCLAW_BOT_TOKEN from SecretVault.
set -euo pipefail

SV_CLI="/opt/little7/supervisor/supervisor-secretvault/src/cli.js"
MASTER_KEY_FILE="/etc/little7/secretvault_master.key"

[ -f "$MASTER_KEY_FILE" ] || { echo "[ERROR] Master key not found: $MASTER_KEY_FILE" >&2; exit 1; }
MASTER_KEY="$(cat "$MASTER_KEY_FILE")"
export SECRETVAULT_MASTER_KEY="$MASTER_KEY"

get_grant() {
  local alias="$1" purpose="$2"
  local result
  result="$(node "$SV_CLI" request \
    --alias "$alias" \
    --purpose "$purpose" \
    --agent oracle \
    --ttl 3600 2>&1)"
  if ! echo "$result" | grep -q '"ok":true'; then
    echo "[ERROR] SecretVault denied $alias: $result" >&2
    return 1
  fi
  echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['path'])"
}

echo "[openclaw-start] Requesting secrets from SecretVault..."

CODEX_PATH="$(get_grant codex-oauth openclaw-startup)"
export ANTHROPIC_API_KEY="$(cat "$CODEX_PATH")"

# Telegram token is optional — OpenClaw runs without it
if node "$SV_CLI" status 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
secrets_dir='/opt/little7/supervisor/supervisor-secretvault/secrets'
import pathlib
exit(0 if pathlib.Path(secrets_dir + '/telegram-bot-token.json').exists() else 1)
" 2>/dev/null; then
  TG_PATH="$(get_grant telegram-bot-token openclaw-startup || echo '')"
  if [ -n "$TG_PATH" ] && [ -f "$TG_PATH" ]; then
    export OPENCLAW_BOT_TOKEN="$(cat "$TG_PATH")"
    echo "[openclaw-start] Telegram token injected."
  fi
fi

echo "[openclaw-start] Starting OpenClaw..."
exec openclaw gateway "$@"
LAUNCHER_EOF

sudo chmod 0750 "${LAUNCHER}"
echo "[OK] openclaw-start updated with Telegram injection"

echo ""
echo "== Stage 60 complete =="
echo "  Telegram bot token stored in SecretVault."
echo "  OpenClaw will receive it at startup via openclaw-start."
echo ""
echo "  Next: start OpenClaw with: ${LAUNCHER}"
echo "  Then pair your Telegram account: openclaw pairing list telegram"
