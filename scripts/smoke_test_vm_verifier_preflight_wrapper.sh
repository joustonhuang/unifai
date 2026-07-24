#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM verifier preflight wrapper dry-run behavior ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRAPPER="$REPO_ROOT/scripts/run_vm_verifier_preflight.sh"
REAL_BASH="$(command -v bash)"
BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
detect_github_remote() {
  local candidate=""
  local url=""

  if candidate="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref "$BRANCH@{upstream}" 2>/dev/null)"; then
    candidate="${candidate%%/*}"
    if [ -n "$candidate" ] && url="$(git -C "$REPO_ROOT" remote get-url "$candidate" 2>/dev/null)"; then
      case "$url" in
        *github.com*|git@github.com:*)
          printf '%s\n' "$candidate"
          return 0
          ;;
      esac
    fi
  fi

  for candidate in origin github; do
    if url="$(git -C "$REPO_ROOT" remote get-url "$candidate" 2>/dev/null)"; then
      case "$url" in
        *github.com*|git@github.com:*)
          printf '%s\n' "$candidate"
          return 0
          ;;
      esac
    fi
  done

  while IFS=$'\t' read -r candidate url; do
    case "$url" in
      *github.com*|git@github.com:*)
        printf '%s\n' "$candidate"
        return 0
        ;;
    esac
  done < <(git -C "$REPO_ROOT" remote -v | awk '$3 == "(fetch)" {print $1 "\t" $2}')

  return 1
}

resolve_visible_remote_ref() {
  local remote="$1"
  local upstream_ref=""
  local candidate=""

  if upstream_ref="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref "${BRANCH}@{upstream}" 2>/dev/null)"; then
    case "$upstream_ref" in
      "$remote"/*)
        if git -C "$REPO_ROOT" rev-parse --verify --quiet "refs/remotes/$upstream_ref" >/dev/null; then
          printf '%s\n' "refs/remotes/$upstream_ref"
          return 0
        fi
        ;;
    esac
  fi

  while IFS= read -r candidate; do
    [ -n "$candidate" ] || continue
    case "$candidate" in
      "refs/remotes/$remote/HEAD")
        continue
        ;;
      *)
        printf '%s\n' "$candidate"
        return 0
        ;;
    esac
  done < <(git -C "$REPO_ROOT" for-each-ref --format='%(refname)' "refs/remotes/$remote")

  return 1
}
LOCAL_ONLY_SHA="$(
  GIT_AUTHOR_NAME="UnifAI Smoke" \
  GIT_AUTHOR_EMAIL="smoke@unifai.invalid" \
  GIT_COMMITTER_NAME="UnifAI Smoke" \
  GIT_COMMITTER_EMAIL="smoke@unifai.invalid" \
  git -C "$REPO_ROOT" commit-tree \
    "$(git -C "$REPO_ROOT" rev-parse HEAD^{tree})" \
    -p "$(git -C "$REPO_ROOT" rev-parse HEAD)" \
    -m "smoke local-only sha" \
    2>/dev/null
)"
GITHUB_REMOTE="$(detect_github_remote)"
VISIBLE_REMOTE_REF="$(resolve_visible_remote_ref "$GITHUB_REMOTE")"
VISIBLE_SHA="$(git -C "$REPO_ROOT" rev-parse "$VISIBLE_REMOTE_REF")"

BRANCH_OUTPUT="$("$REAL_BASH" "$WRAPPER" --dry-run "$BRANCH")"
printf '%s\n' "$BRANCH_OUTPUT"

if ! grep -q "Mode: dry-run" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected dry-run mode banner missing for branch case."
  exit 1
fi

if ! grep -q "Ref: $BRANCH" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected branch ref missing in --dry-run flag case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] bash scripts/check_vm_host_readiness.sh" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected host-readiness command missing in branch case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] bash scripts/check_github_branch_visibility.sh $BRANCH" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected branch visibility command missing in branch case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $BRANCH" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected check-gate command missing in branch case."
  exit 1
fi

DEFAULT_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER")"
printf '%s\n' "$DEFAULT_OUTPUT"

if ! grep -q "Ref: $BRANCH" <<<"$DEFAULT_OUTPUT"; then
  echo "[FAIL] Expected current branch to be used when no ref is provided."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] bash scripts/check_github_branch_visibility.sh $BRANCH" <<<"$DEFAULT_OUTPUT"; then
  echo "[FAIL] Expected branch visibility command missing in default no-arg case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $BRANCH" <<<"$DEFAULT_OUTPUT"; then
  echo "[FAIL] Expected check-gate command missing in default no-arg case."
  exit 1
fi

VISIBLE_SHA_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "$VISIBLE_SHA")"
printf '%s\n' "$VISIBLE_SHA_OUTPUT"

if ! grep -q "skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA" <<<"$VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Expected explicit-ref skip message missing in GitHub-visible SHA case."
  exit 1
fi

if grep -q "\[DRY_RUN\] bash scripts/check_github_branch_visibility.sh" <<<"$VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Branch visibility command should not run in GitHub-visible SHA case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] bash scripts/check_vm_host_readiness.sh" <<<"$VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Expected host-readiness command missing in GitHub-visible SHA case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $VISIBLE_SHA" <<<"$VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Expected check-gate command missing in GitHub-visible SHA case."
  exit 1
fi

VISIBLE_REMOTE_REF_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "$VISIBLE_REMOTE_REF")"
printf '%s\n' "$VISIBLE_REMOTE_REF_OUTPUT"

if ! grep -q "Ref: $VISIBLE_REMOTE_REF" <<<"$VISIBLE_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Expected remote-tracking ref missing in explicit remote-ref case."
  exit 1
fi

if ! grep -q "skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA" <<<"$VISIBLE_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Expected explicit-ref skip message missing in remote-tracking ref case."
  exit 1
fi

if grep -q "\[DRY_RUN\] bash scripts/check_github_branch_visibility.sh" <<<"$VISIBLE_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Branch visibility command should not run in explicit remote-tracking ref case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $VISIBLE_REMOTE_REF" <<<"$VISIBLE_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Expected check-gate command missing in explicit remote-tracking ref case."
  exit 1
fi

DOUBLE_DASH_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" -- "$BRANCH")"
printf '%s\n' "$DOUBLE_DASH_OUTPUT"

if ! grep -q "Ref: $BRANCH" <<<"$DOUBLE_DASH_OUTPUT"; then
  echo "[FAIL] Expected branch ref missing when passed after --."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] bash scripts/check_github_branch_visibility.sh $BRANCH" <<<"$DOUBLE_DASH_OUTPUT"; then
  echo "[FAIL] Expected branch visibility command missing when ref is passed after --."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $BRANCH" <<<"$DOUBLE_DASH_OUTPUT"; then
  echo "[FAIL] Expected check-gate command missing when ref is passed after --."
  exit 1
fi

set +e
UNKNOWN_OPTION_OUTPUT="$("$REAL_BASH" "$WRAPPER" --bogus 2>&1)"
UNKNOWN_OPTION_STATUS=$?
set -e
printf '%s\n' "$UNKNOWN_OPTION_OUTPUT"

if [ "$UNKNOWN_OPTION_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected unknown option case to fail."
  exit 1
fi

if ! grep -q "Unknown option: --bogus" <<<"$UNKNOWN_OPTION_OUTPUT"; then
  echo "[FAIL] Expected unknown option failure message missing."
  exit 1
fi

set +e
EXTRA_ARG_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "$BRANCH" extra-arg 2>&1)"
EXTRA_ARG_STATUS=$?
set -e
printf '%s\n' "$EXTRA_ARG_OUTPUT"

if [ "$EXTRA_ARG_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected extra argument case to fail."
  exit 1
fi

if ! grep -q "Unexpected extra argument: extra-arg" <<<"$EXTRA_ARG_OUTPUT"; then
  echo "[FAIL] Expected extra argument failure message missing."
  exit 1
fi

set +e
LOCAL_ONLY_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "$LOCAL_ONLY_SHA" 2>&1)"
LOCAL_ONLY_STATUS=$?
set -e
printf '%s\n' "$LOCAL_ONLY_OUTPUT"

if [ "$LOCAL_ONLY_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected local-only SHA case to fail fast."
  exit 1
fi

if ! grep -q "exists locally but is not reachable from any GitHub-visible branch" <<<"$LOCAL_ONLY_OUTPUT"; then
  echo "[FAIL] Expected local-only SHA visibility failure message missing."
  exit 1
fi

if grep -q "python3 scripts/check_github_check_gate.py $LOCAL_ONLY_SHA" <<<"$LOCAL_ONLY_OUTPUT"; then
  echo "[FAIL] Local-only SHA case should fail before the GitHub check-gate step."
  exit 1
fi

echo "[PASS] VM verifier preflight wrapper dry-run behaves as expected."
