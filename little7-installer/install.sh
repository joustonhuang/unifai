#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGES_DIR="${ROOT_DIR}/stages"

usage() {
  cat <<'EOF'
Usage:
  ./install.sh                 # run all stages (00..99) in order
  ./install.sh all             # same as above
  ./install.sh <NN>            # run a single stage number (e.g. 20)
  ./install.sh <NN_name>       # run a single stage file (e.g. 20_supervisor)
  ./install.sh list            # list detected stages
EOF
}

list_stages() {
  # Only accept files like 00_foo.sh .. 99_bar.sh
  find "$STAGES_DIR" -maxdepth 1 -type f -regextype posix-extended -regex '.*/[0-9]{2}_.+\.sh$' \
    | sort \
    | sed "s|^${STAGES_DIR}/||"
}

run_stage_file() {
  local file="$1"
  echo "==> Running stage: $(basename "$file")"
  bash "$file"
}

run_all() {
  local stages
  stages="$(list_stages)"
  if [ -z "$stages" ]; then
    echo "No stage files found in: $STAGES_DIR"
    exit 1
  fi

  while IFS= read -r s; do
    run_stage_file "${STAGES_DIR}/${s}"
  done <<< "$stages"
}

run_one() {
  local arg="$1"

  # If arg is exactly two digits, find matching file(s)
  if [[ "$arg" =~ ^[0-9]{2}$ ]]; then
    local matches
    matches="$(find "$STAGES_DIR" -maxdepth 1 -type f -name "${arg}_*.sh" | sort)"
    if [ -z "$matches" ]; then
      echo "Stage ${arg} not found (expected ${STAGES_DIR}/${arg}_*.sh)"
      exit 1
    fi

    # If multiple match (rare but possible), run all of them in lexical order
    while IFS= read -r f; do
      run_stage_file "$f"
    done <<< "$matches"
    return 0
  fi

  # Otherwise treat as a stage name (with or without .sh)
  if [[ "$arg" != *.sh ]]; then
    arg="${arg}.sh"
  fi

  local file="${STAGES_DIR}/${arg}"
  if [ ! -f "$file" ]; then
    echo "Stage file not found: $file"
    exit 1
  fi

  run_stage_file "$file"
}

main() {
  local cmd="${1:-all}"

  case "$cmd" in
    -h|--help|help)
      usage
      ;;
    list)
      list_stages
      ;;
    all|"")
      run_all
      ;;
    *)
      run_one "$cmd"
      ;;
  esac
}

main "$@"
