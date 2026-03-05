#!/usr/bin/env bash
set -euo pipefail

echo "== Stage 16: Secrets Verification (per-key OK/FAIL) =="

CLOUD_ENV="/etc/little7/cloud.env"
SECRETS_DIR="/etc/little7/secrets"
DEBUG="${LITTLE7_DEBUG:-0}"

dbg() { if [ "$DEBUG" = "1" ]; then echo "[DEBUG] $*" >&2; fi; }

have_cmd() { command -v "$1" >/dev/null 2>&1; }

# Normalize path:
# - If absolute: keep
# - If filename only: treat as /etc/little7/secrets/<file>
norm_path() {
  local p="$1"
  if [[ "$p" == /* ]]; then
    echo "$p"
  else
    echo "${SECRETS_DIR}/${p}"
  fi
}

# Decrypt a .gpg file and return plaintext on stdout.
# On failure returns a single line like: FAIL:<reason>:<fullpath>
decrypt_gpg() {
  local gpg_file="$1"
  gpg_file="$(norm_path "$gpg_file")"

  dbg "decrypt_gpg(): fullpath=$gpg_file"

  # IMPORTANT: secrets dir is root:root 700, so existence checks must use sudo.
  if ! sudo test -f "$gpg_file"; then
    echo "FAIL:missing_file:${gpg_file}"
    return 0
  fi

  local out=""
  if ! out="$(sudo gpg -q -d "$gpg_file" 2>/dev/null)"; then
    echo "FAIL:decrypt_error:${gpg_file}"
    return 0
  fi

  if [ -z "$out" ]; then
    echo "FAIL:empty_secret:${gpg_file}"
    return 0
  fi

  echo "$out"
}

# curl wrapper returns: "<http_code> <curl_exit>"
http_check() {
  local url="$1"; shift
  local code=""
  local tmp=""
  tmp="$(mktemp)"
  set +e
  code="$(curl -sS -m 10 -o "$tmp" -w "%{http_code}" "$url" "$@")"
  local rc=$?
  set -e
  rm -f "$tmp"
  echo "${code} ${rc}"
}

verify_openai() {
  local api_key="$1"
  local code_rc
  code_rc="$(http_check "https://api.openai.com/v1/models" -H "Authorization: Bearer ${api_key}")"
  local code="${code_rc%% *}"
  local rc="${code_rc##* }"

  if [ "$rc" != "0" ]; then
    echo "FAIL:curl_rc_${rc}"
    return 0
  fi

  if [ "$code" = "200" ]; then
    echo "OK"
  else
    echo "FAIL:http_${code}"
  fi
}

# Provider routing:
# Add more providers later by implementing verify_<provider>() and adding cases here.
verify_provider() {
  local provider="$1"
  local api_key="$2"
  case "$provider" in
    OPENAI) verify_openai "$api_key" ;;
    *) echo "FAIL:unsupported_provider_${provider}" ;;
  esac
}

# Guess provider from file name or env var key name.
guess_provider() {
  local token="$1"
  token="$(echo "$token" | tr '[:lower:]' '[:upper:]')"
  token="${token##*/}"     # strip path
  token="${token%.GPG}"    # remove suffix
  token="${token%_API_KEY}"
  token="${token%_KEY}"
  case "$token" in
    OPENAI|OPENAI_API_KEY|OPENAI_API_KEY_GPG) echo "OPENAI" ;;
    *) echo "$token" ;;
  esac
}

# ---------- preflight ----------
if ! have_cmd curl; then
  echo "ERROR: curl not found."
  exit 1
fi

if ! have_cmd gpg; then
  echo "ERROR: gpg not found."
  exit 1
fi

if [ "$DEBUG" = "1" ]; then
  echo "[DEBUG] whoami=$(whoami)" >&2
  echo "[DEBUG] cloud.env exists: $([ -f "$CLOUD_ENV" ] && echo yes || echo no)" >&2
  echo "[DEBUG] secrets dir exists: $([ -d "$SECRETS_DIR" ] && echo yes || echo no)" >&2
  echo "[DEBUG] cloud.env content:" >&2
  sudo cat "$CLOUD_ENV" 2>/dev/null >&2 || true
  echo "[DEBUG] secrets dir listing:" >&2
  sudo ls -al "$SECRETS_DIR" 2>&1 >&2 || true
  echo "[DEBUG] find *.gpg under /etc/little7:" >&2
  sudo find /etc/little7 -maxdepth 3 -type f -name "*.gpg" -print 2>/dev/null >&2 || true
fi

declare -A seen=()

# 1) Collect from cloud.env (preferred)
if [ -f "$CLOUD_ENV" ]; then
  while IFS= read -r line; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/[[:space:]]//g')"
    [ -z "$line" ] && continue

    if [[ "$line" =~ ^([A-Z0-9_]+)_API_KEY_GPG=(.+)$ ]]; then
      p="${BASH_REMATCH[2]}"
      p="$(norm_path "$p")"
      dbg "cloud.env detected secret path: $p"
      seen["$p"]=1
    fi
  done < "$CLOUD_ENV"
fi

# 2) Collect from secrets dir (*.gpg)
if [ -d "$SECRETS_DIR" ]; then
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    p="$(norm_path "$p")"
    dbg "secrets dir detected secret path: $p"
    seen["$p"]=1
  done < <(sudo find "$SECRETS_DIR" -maxdepth 1 -type f -name "*.gpg" 2>/dev/null | sort)
fi

printf "\n%-8s  %-35s  %-6s  %s\n" "PROVIDER" "SECRET_FILE" "RESULT" "DETAIL"
printf "%-8s  %-35s  %-6s  %s\n" "--------" "-----------------------------------" "------" "------------------------------"

any_fail=0

# Deterministic order
for fullpath in $(printf "%s\n" "${!seen[@]}" | sort); do
  provider="$(guess_provider "$fullpath")"
  display="$(basename "$fullpath")"

  dec="$(decrypt_gpg "$fullpath")"
  if [[ "$dec" == FAIL:* ]]; then
    reason="$(echo "$dec" | cut -d: -f2)"
    path_in_msg="$(echo "$dec" | cut -d: -f3-)"
    printf "%-8s  %-35s  %-6s  %s\n" "$provider" "$display" "FAIL" "${reason} (${path_in_msg})"
    any_fail=1
    continue
  fi

  # Trim whitespace/newlines from decrypted secret (do NOT print it)
  key="$(echo -n "$dec" | tr -d '\r' | tr -d '\n' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"

  result="$(verify_provider "$provider" "$key")"
  if [ "$result" = "OK" ]; then
    printf "%-8s  %-35s  %-6s  %s\n" "$provider" "$display" "OK" "api_ok"
  else
    printf "%-8s  %-35s  %-6s  %s\n" "$provider" "$display" "FAIL" "${result#FAIL:}"
    any_fail=1
  fi
done

echo
if [ "$any_fail" = "1" ]; then
  echo "One or more secrets failed verification."
  exit 1
fi

echo "All detected secrets verified OK."
