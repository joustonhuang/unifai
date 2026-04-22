#!/usr/bin/env bash
set -euo pipefail

echo "== Uninstall helper =="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ACTIVE_MODELS_FILE="${REPO_ROOT}/little7-installer/config/active_models.yml"

cat <<'EOF2'
Bundled local runtime assets have been removed from this repository.

There is no repository-managed runtime to uninstall anymore.
If you previously installed external model runtimes or services, remove them
using their own host-native service manager or package workflow.
EOF2

# Offer to clean up the generated model config file.
if [[ -f "${ACTIVE_MODELS_FILE}" ]]; then
  echo ""
  echo "Found active model config: ${ACTIVE_MODELS_FILE}"

  if [[ "${PURGE_MODELS:-0}" == "1" ]]; then
    rm -f "${ACTIVE_MODELS_FILE}"
    echo "[OK] Removed ${ACTIVE_MODELS_FILE}"
  elif [[ -t 0 ]]; then
    read -r -p "Remove it? [y/N] " answer
    case "${answer}" in
      y|Y|yes|YES)
        rm -f "${ACTIVE_MODELS_FILE}"
        echo "[OK] Removed ${ACTIVE_MODELS_FILE}"
        ;;
      *)
        echo "[SKIP] Keeping ${ACTIVE_MODELS_FILE}"
        ;;
    esac
  else
    echo "[INFO] Set PURGE_MODELS=1 to remove it non-interactively."
  fi
else
  echo ""
  echo "[INFO] No active model config found at ${ACTIVE_MODELS_FILE} — nothing to clean up."
fi
