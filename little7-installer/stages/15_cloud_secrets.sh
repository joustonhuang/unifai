#!/usr/bin/env bash
set -euo pipefail

echo "== Stage 15: Cloud LLM Secrets (optional) =="

CLOUD_ENV="/etc/little7/cloud.env"
SECRETS_DIR="/etc/little7/secrets"
OPENAI_GPG="${SECRETS_DIR}/openai_api_key.gpg"
KEY_ID="little7-secrets@local"

have_tty() {
  [ -e /dev/tty ]
}

prompt_tty() {
  # $1 = prompt
  local msg="$1"
  printf "%s" "$msg" > /dev/tty
  local ans=""
  IFS= read -r ans < /dev/tty || true
  printf "%s" "$ans"
}

prompt_secret_tty() {
  # $1 = prompt
  local msg="$1"
  printf "%s" "$msg" > /dev/tty
  local ans=""
  IFS= read -r -s ans < /dev/tty || true
  printf "\n" > /dev/tty
  printf "%s" "$ans"
}

########################################
# 1) Decide Cloud enable/disable
########################################

CLOUD_FLAG="${LITTLE7_CLOUD_LLM:-}"

if [ -z "$CLOUD_FLAG" ]; then
  if have_tty; then
    CLOUD_FLAG="$(prompt_tty "Enable Cloud LLM? (1=yes, 0=no) [0]: ")"
    CLOUD_FLAG="${CLOUD_FLAG:-0}"
  else
    CLOUD_FLAG="0"
  fi
fi

########################################
# 2) If disabled → write config and exit
########################################

if [ "$CLOUD_FLAG" != "1" ]; then
  echo "Cloud LLM disabled."
  sudo mkdir -p /etc/little7
  sudo tee "$CLOUD_ENV" >/dev/null <<'EOF'
LITTLE7_CLOUD_LLM=0
LITTLE7_CLOUD_PROVIDER=
EOF
  sudo chmod 0644 "$CLOUD_ENV"
  exit 0
fi

########################################
# 3) Prepare directories (root-owned)
########################################

sudo mkdir -p /etc/little7
sudo mkdir -p "$SECRETS_DIR"
sudo chown root:root "$SECRETS_DIR"
sudo chmod 700 "$SECRETS_DIR"

########################################
# 4) Ensure gpg exists
########################################

if ! command -v gpg >/dev/null 2>&1; then
  echo "ERROR: gpg not installed. Run stage 00_bigbang first."
  exit 1
fi

########################################
# 5) Create local host key if missing (RSA)
########################################

if ! sudo gpg --list-keys "$KEY_ID" >/dev/null 2>&1; then
  echo "Creating local GPG key for secrets (RSA): $KEY_ID"

  sudo tee /tmp/little7-gpg-key >/dev/null <<'EOF'
%no-protection
Key-Type: RSA
Key-Length: 3072
Subkey-Type: RSA
Subkey-Length: 3072
Name-Real: little7-secrets
Name-Email: little7-secrets@local
Expire-Date: 0
%commit
EOF

  sudo gpg --batch --gen-key /tmp/little7-gpg-key
  sudo rm -f /tmp/little7-gpg-key
else
  echo "Local GPG key already exists: $KEY_ID"
fi

########################################
# 6) Provider
########################################

PROVIDER="${LITTLE7_CLOUD_PROVIDER:-OPENAI}"

########################################
# 7) Acquire API key
########################################

API_KEY="${OPENAI_API_KEY:-}"

if [ -z "$API_KEY" ]; then
  if have_tty; then
    API_KEY="$(prompt_secret_tty "Enter OPENAI_API_KEY (input hidden): ")"
  else
    echo "ERROR: Non-interactive mode requires OPENAI_API_KEY env variable."
    exit 1
  fi
fi

if [ -z "$API_KEY" ]; then
  echo "ERROR: OPENAI_API_KEY cannot be empty."
  exit 1
fi

########################################
# 8) Encrypt and store secret (root-owned)
########################################

echo "Encrypting API key to: $OPENAI_GPG"
printf "%s" "$API_KEY" | sudo gpg --batch --yes --trust-model always \
  -e -r "$KEY_ID" -o "$OPENAI_GPG"

sudo chown root:root "$OPENAI_GPG"
sudo chmod 600 "$OPENAI_GPG"

########################################
# 9) Write config
########################################

sudo tee "$CLOUD_ENV" >/dev/null <<EOF
LITTLE7_CLOUD_LLM=1
LITTLE7_CLOUD_PROVIDER=${PROVIDER}
OPENAI_API_KEY_GPG=${OPENAI_GPG}
EOF
sudo chmod 0644 "$CLOUD_ENV"

echo "Cloud LLM enabled. Config: $CLOUD_ENV"
echo "Secret stored encrypted at: $OPENAI_GPG"
