#!/usr/bin/env bash
set -euo pipefail

read_env_list() {
  local __var_name="$1"
  local __target_var="$2"
  local __value="${!__var_name-}"
  local -n __target_ref="$__target_var"
  __target_ref=()
  while IFS= read -r line; do
    if [[ -n "$line" ]]; then
      __target_ref+=("$line")
    fi
  done <<< "$__value"
}

read_env_list "UNIFAI_PREFLIGHT_PRE_REFRESH_HANDOFF_PATHS" pre_refresh_handoff_paths
read_env_list "UNIFAI_PREFLIGHT_REFRESHED_HANDOFF_PATHS" refreshed_handoff_paths

if [ "${#refreshed_handoff_paths[@]}" -eq 0 ]; then
  exit 0
fi

declare -A pre_refresh_handoff_path_set=()
declare -a newly_dirty_handoff_paths=()
declare -a preexisting_dirty_handoff_paths=()

for path in "${pre_refresh_handoff_paths[@]}"; do
  pre_refresh_handoff_path_set["$path"]=1
done

for path in "${refreshed_handoff_paths[@]}"; do
  if [[ -n "${pre_refresh_handoff_path_set[$path]:-}" ]]; then
    preexisting_dirty_handoff_paths+=("$path")
  else
    newly_dirty_handoff_paths+=("$path")
  fi
done

if [ "${#newly_dirty_handoff_paths[@]}" -gt 0 ]; then
  printf '[FAIL] Bootstrap preflight refreshed checkpoint handoff artifacts but they are not committed yet:\n'
  printf '  - %s\n' "${newly_dirty_handoff_paths[@]}"
  if [ "${#preexisting_dirty_handoff_paths[@]}" -gt 0 ]; then
    printf '[INFO] Checkpoint handoff artifacts that were already dirty before this rerun and still need review:\n'
    printf '  - %s\n' "${preexisting_dirty_handoff_paths[@]}"
  fi
  echo "[INFO] Review/add/commit the refreshed verifier checkpoint handoff before treating this ref as preflight-green."
  exit 1
fi

printf '[FAIL] Bootstrap preflight checkpoint handoff artifacts were already dirty before refresh and are still not committed:\n'
printf '  - %s\n' "${preexisting_dirty_handoff_paths[@]}"
echo "[INFO] Review/add/commit the existing verifier checkpoint handoff dirtiness before treating this ref as preflight-green."
exit 1
