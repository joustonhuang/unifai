#!/usr/bin/env bash
set -euo pipefail

echo "== Stage 40: Local Model Runtime Registration =="

# Derive paths from script location — never use $HOME defaults in an installer.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${INSTALLER_DIR}/.." && pwd)}"
CONFIG_DIR="${INSTALLER_DIR}/config"
ACTIVE_MODELS_FILE="${CONFIG_DIR}/active_models.yml"
ACTIVE_MODELS_TEMPLATE="${CONFIG_DIR}/active_models.yml.template"

log() {
  echo "[INFO] $*"
}

mkdir -p "${CONFIG_DIR}"

# Write template only if it does not already exist (idempotent).
if [[ ! -f "${ACTIVE_MODELS_TEMPLATE}" ]]; then
  cat > "${ACTIVE_MODELS_TEMPLATE}" <<'EOF2'
version: "0.1"

models:
  system_services:
    runtime: "external"
    model_id: ""
    role: "system_services"
    mcp_enabled: false

  local_reasoning:
    runtime: "external"
    model_id: ""
    role: "local_reasoning"
    mcp_enabled: true
EOF2
  log "Created template: ${ACTIVE_MODELS_TEMPLATE}"
fi

if [[ ! -f "${ACTIVE_MODELS_FILE}" ]]; then
  cp "${ACTIVE_MODELS_TEMPLATE}" "${ACTIVE_MODELS_FILE}"
  log "Created ${ACTIVE_MODELS_FILE}"
else
  log "Left existing ${ACTIVE_MODELS_FILE} unchanged"
fi

echo ""
echo "  Next step:"
echo "    1. Edit ${ACTIVE_MODELS_FILE}"
echo "    2. Set runtime/model_id for the host-native or external model endpoints UnifAI should use"
echo ""

# Gate: fail if any model_id field is still empty — Stage 50 (OpenClaw) requires this.
if ! ACTIVE_MODELS_FILE="${ACTIVE_MODELS_FILE}" python3 - <<'PY'
import sys, yaml, os
path = os.environ["ACTIVE_MODELS_FILE"]
data = yaml.safe_load(open(path)) or {}
models = data.get("models", {})
missing = [k for k, v in models.items() if not (v or {}).get("model_id")]
if missing:
    print("[ERROR] Empty model_id in: " + ", ".join(missing), file=sys.stderr)
    sys.exit(1)
PY
then
  echo "[ERROR] Configure model_id fields in ${ACTIVE_MODELS_FILE}, then re-run: ./install.sh 40"
  exit 1
fi

log "Model config validated — all model_id fields are populated."
log "Stage 40 complete."
