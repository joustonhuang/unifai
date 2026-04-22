#!/usr/bin/env bash
set -euo pipefail

echo "== Stage 40: Local Model Runtime Registration =="

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/projects/unifai}"
CONFIG_DIR="${PROJECT_ROOT}/little7-installer/config"
ACTIVE_MODELS_FILE="${CONFIG_DIR}/active_models.yml"
ACTIVE_MODELS_TEMPLATE="${CONFIG_DIR}/active_models.yml.template"

log() {
  echo "[INFO] $*"
}

mkdir -p "${CONFIG_DIR}"

cat > "${ACTIVE_MODELS_TEMPLATE}" <<EOF2
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

if [[ ! -f "${ACTIVE_MODELS_FILE}" ]]; then
  cp "${ACTIVE_MODELS_TEMPLATE}" "${ACTIVE_MODELS_FILE}"
  log "Created ${ACTIVE_MODELS_FILE}"
else
  log "Left existing ${ACTIVE_MODELS_FILE} unchanged"
fi

cat <<EOF2

Bundled runtime provisioning paths have been removed.

Next step:
  1. Edit ${ACTIVE_MODELS_FILE}
  2. Set runtime/model_id values for the host-native or external model endpoints you want UnifAI to use

This stage now only prepares the model-selection config file.
EOF2
