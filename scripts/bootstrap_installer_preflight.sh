#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${1:-$REPO_ROOT/ci-artifacts/bootstrap-preflight}"
REPORT_FILE="$REPORT_DIR/report.txt"
mkdir -p "$REPORT_DIR"

exec > >(tee "$REPORT_FILE")
exec 2>&1

pass() {
  echo "[PASS] $1"
}

fail() {
  echo "[FAIL] $1"
  exit 1
}

require_file() {
  local path="$1"
  [ -f "$path" ] || fail "Missing required file: ${path#$REPO_ROOT/}"
  pass "Found ${path#$REPO_ROOT/}"
}

require_grep() {
  local pattern="$1"
  local path="$2"
  grep -Eq "$pattern" "$path" || fail "Expected pattern '$pattern' in ${path#$REPO_ROOT/}"
  pass "Pattern '$pattern' present in ${path#$REPO_ROOT/}"
}

echo "== Bootstrap installer preflight =="
echo "Repo root: $REPO_ROOT"
echo "Report: $REPORT_FILE"

INSTALLER="$REPO_ROOT/installer.sh"
STAGE_INSTALLER="$REPO_ROOT/little7-installer/install.sh"

require_file "$INSTALLER"
require_file "$STAGE_INSTALLER"
require_file "$REPO_ROOT/little7-installer/config/supervisor-secretvault.lock"

if git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  git -C "$REPO_ROOT" submodule update --init --recursive supervisor/supervisor-secretvault
  pass "supervisor-secretvault submodule initialized"
fi

bash -n "$INSTALLER"
pass "installer.sh passes bash -n"

bash -n "$STAGE_INSTALLER"
pass "little7-installer/install.sh passes bash -n"

bash "$STAGE_INSTALLER" verify
pass "little7-installer/install.sh verify passed"

require_grep 'check_root\s*\(' "$INSTALLER"
require_grep 'check_os\s*\(' "$INSTALLER"
require_grep 'phase_8_validation\s*\(' "$INSTALLER"

for service in unifai-secretvault unifai-keyman unifai-supervisor unifai-openclaw; do
  require_grep "$service" "$INSTALLER"
done

require_grep 'curl -fsSL https://openclaw.ai/install.sh \| bash' "$REPO_ROOT/little7-installer/stages/50_openclaw.sh"
pass "Stage 50 uses official OpenClaw installer"

cat <<'EOF'

== Preflight summary ==
This preflight only proves installer structure and cheap sanity checks.
It does NOT prove a fresh VM can boot the stack end-to-end.
Run the local VM verifier after GitHub checks are green.
EOF
