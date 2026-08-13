#!/usr/bin/env bash
set -euo pipefail

echo "=== UnifAI Smoke Test: VM verifier preflight wrapper dry-run behavior ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRAPPER="$REPO_ROOT/scripts/run_vm_verifier_preflight.sh"
REAL_BASH="$(command -v bash)"
BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
DETACHED_WORKTREE_DIR="$(mktemp -d -t unifai-vm-preflight-detached-XXXXXX)"
STALE_FIXTURE_DIR="$(mktemp -d -t unifai-vm-preflight-stale-XXXXXX)"
cleanup() {
  git -C "$REPO_ROOT" worktree remove --force "$DETACHED_WORKTREE_DIR" >/dev/null 2>&1 || true
  rm -rf "$DETACHED_WORKTREE_DIR"
  rm -rf "$STALE_FIXTURE_DIR"
}
trap cleanup EXIT

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
if [ -z "$GITHUB_REMOTE" ]; then
  echo "[FAIL] Could not find a GitHub-backed remote for wrapper smoke coverage."
  exit 1
fi

VISIBLE_REMOTE_REF="$(resolve_visible_remote_ref "$GITHUB_REMOTE")"
if [ -z "$VISIBLE_REMOTE_REF" ]; then
  echo "[FAIL] Could not resolve a GitHub-visible remote ref for wrapper smoke coverage."
  exit 1
fi
VISIBLE_VERIFIER_REF="${VISIBLE_REMOTE_REF#refs/remotes/}"
VISIBLE_VERIFIER_REF="${VISIBLE_VERIFIER_REF#*/}"
BRANCH_VERIFIER_REF="$BRANCH"
BRANCH_UPSTREAM_REF=""
BRANCH_AHEAD_COUNT=0
if upstream_ref="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref "${BRANCH}@{upstream}" 2>/dev/null)"; then
  BRANCH_UPSTREAM_REF="$upstream_ref"
  case "$upstream_ref" in
    "$GITHUB_REMOTE"/*)
      BRANCH_VERIFIER_REF="${upstream_ref#*/}"
      ;;
  esac
  BRANCH_AHEAD_COUNT="$(
    git -C "$REPO_ROOT" rev-list --left-right --count "$BRANCH...$upstream_ref" |
      awk '{print $1}'
  )"
fi

VISIBLE_SHA="$(git -C "$REPO_ROOT" rev-parse "$VISIBLE_REMOTE_REF")"
git -C "$REPO_ROOT" worktree add --detach "$DETACHED_WORKTREE_DIR" HEAD >/dev/null
cp "$WRAPPER" "$DETACHED_WORKTREE_DIR/scripts/run_vm_verifier_preflight.sh"

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

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $BRANCH_VERIFIER_REF" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected branch case to run the check-gate command on the GitHub-visible verifier ref."
  exit 1
fi

if ! grep -q "Next: bash scripts/vm/verify_bootstrap_in_vm.sh $BRANCH_VERIFIER_REF" <<<"$BRANCH_OUTPUT"; then
  echo "[FAIL] Expected branch case to hand off the GitHub-visible verifier ref."
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

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $BRANCH_VERIFIER_REF" <<<"$DEFAULT_OUTPUT"; then
  echo "[FAIL] Expected default no-arg case to run the check-gate command on the GitHub-visible verifier ref."
  exit 1
fi

if ! grep -q "Next: bash scripts/vm/verify_bootstrap_in_vm.sh $BRANCH_VERIFIER_REF" <<<"$DEFAULT_OUTPUT"; then
  echo "[FAIL] Expected default no-arg case to hand off the GitHub-visible verifier ref."
  exit 1
fi

if [ "$BRANCH_AHEAD_COUNT" -gt 0 ]; then
  set +e
  VISIBLE_SHA_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "$VISIBLE_SHA" 2>&1)"
  VISIBLE_SHA_STATUS=$?
  set -e
  printf '%s\n' "$VISIBLE_SHA_OUTPUT"

  if [ "$VISIBLE_SHA_STATUS" -eq 0 ]; then
    echo "[FAIL] Expected GitHub-visible SHA case to fail when the current branch is ahead of its GitHub-visible upstream."
    exit 1
  fi

  if ! grep -q "resolves to the current GitHub-visible head for '$BRANCH', but local branch '$BRANCH' is ahead by $BRANCH_AHEAD_COUNT commit" <<<"$VISIBLE_SHA_OUTPUT"; then
    echo "[FAIL] Expected ahead-of-visible SHA failure message missing."
    exit 1
  fi

  if grep -q "scripts/check_vm_host_readiness.sh" <<<"$VISIBLE_SHA_OUTPUT"; then
    echo "[FAIL] Ahead-of-visible SHA case should fail before any preflight steps are planned."
    exit 1
  fi

  set +e
  VISIBLE_REMOTE_REF_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "$VISIBLE_REMOTE_REF" 2>&1)"
  VISIBLE_REMOTE_REF_STATUS=$?
  set -e
  printf '%s\n' "$VISIBLE_REMOTE_REF_OUTPUT"

  if [ "$VISIBLE_REMOTE_REF_STATUS" -eq 0 ]; then
    echo "[FAIL] Expected explicit remote-ref case to fail when the current branch is ahead of its GitHub-visible upstream."
    exit 1
  fi

  if ! grep -q "resolves to the current GitHub-visible head for '$BRANCH', but local branch '$BRANCH' is ahead by $BRANCH_AHEAD_COUNT commit" <<<"$VISIBLE_REMOTE_REF_OUTPUT"; then
    echo "[FAIL] Expected ahead-of-visible remote-ref failure message missing."
    exit 1
  fi

  if grep -q "scripts/check_vm_host_readiness.sh" <<<"$VISIBLE_REMOTE_REF_OUTPUT"; then
    echo "[FAIL] Ahead-of-visible remote-ref case should fail before any preflight steps are planned."
    exit 1
  fi
else
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

  if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $VISIBLE_VERIFIER_REF" <<<"$VISIBLE_REMOTE_REF_OUTPUT"; then
    echo "[FAIL] Expected explicit remote-tracking ref case to run the check-gate command on the GitHub-visible verifier ref."
    exit 1
  fi

  if ! grep -q "Next: bash scripts/vm/verify_bootstrap_in_vm.sh $VISIBLE_VERIFIER_REF" <<<"$VISIBLE_REMOTE_REF_OUTPUT"; then
    echo "[FAIL] Expected verifier handoff to normalize the explicit remote-tracking ref."
    exit 1
  fi
fi

set +e
REMOTE_HEAD_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "refs/remotes/$GITHUB_REMOTE/HEAD" 2>&1)"
REMOTE_HEAD_STATUS=$?
set -e
printf '%s\n' "$REMOTE_HEAD_OUTPUT"

if [ "$REMOTE_HEAD_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected symbolic remote HEAD alias case to fail fast."
  exit 1
fi

if ! grep -q "symbolic remote HEAD alias" <<<"$REMOTE_HEAD_OUTPUT"; then
  echo "[FAIL] Expected symbolic remote HEAD alias failure message missing."
  exit 1
fi

if ! grep -q "Use a concrete branch/ref such as refs/remotes/$GITHUB_REMOTE/<branch>, $GITHUB_REMOTE/<branch>, or the resolved branch name" <<<"$REMOTE_HEAD_OUTPUT"; then
  echo "[FAIL] Expected symbolic remote HEAD alias recovery guidance missing."
  exit 1
fi

if grep -q "python3 scripts/check_github_check_gate.py" <<<"$REMOTE_HEAD_OUTPUT"; then
  echo "[FAIL] Symbolic remote HEAD alias case should fail before the GitHub check-gate step."
  exit 1
fi

set +e
SHORT_REMOTE_HEAD_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "$GITHUB_REMOTE/HEAD" 2>&1)"
SHORT_REMOTE_HEAD_STATUS=$?
set -e
printf '%s\n' "$SHORT_REMOTE_HEAD_OUTPUT"

if [ "$SHORT_REMOTE_HEAD_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected short-form symbolic remote HEAD alias case to fail fast."
  exit 1
fi

if ! grep -q "symbolic remote HEAD alias" <<<"$SHORT_REMOTE_HEAD_OUTPUT"; then
  echo "[FAIL] Expected short-form symbolic remote HEAD alias failure message missing."
  exit 1
fi

if ! grep -q "Use a concrete branch/ref such as refs/remotes/$GITHUB_REMOTE/<branch>, $GITHUB_REMOTE/<branch>, or the resolved branch name" <<<"$SHORT_REMOTE_HEAD_OUTPUT"; then
  echo "[FAIL] Expected short-form symbolic remote HEAD alias recovery guidance missing."
  exit 1
fi

if grep -q "python3 scripts/check_github_check_gate.py" <<<"$SHORT_REMOTE_HEAD_OUTPUT"; then
  echo "[FAIL] Short-form symbolic remote HEAD alias case should fail before the GitHub check-gate step."
  exit 1
fi

mkdir -p "$STALE_FIXTURE_DIR/scripts"
git -C "$STALE_FIXTURE_DIR" init -q
git -C "$STALE_FIXTURE_DIR" config user.name "UnifAI Smoke"
git -C "$STALE_FIXTURE_DIR" config user.email "smoke@unifai.invalid"
printf 'seed\n' >"$STALE_FIXTURE_DIR/seed.txt"
git -C "$STALE_FIXTURE_DIR" add seed.txt
git -C "$STALE_FIXTURE_DIR" commit -qm "seed"
git -C "$STALE_FIXTURE_DIR" branch -M main
git -C "$STALE_FIXTURE_DIR" remote add origin https://github.com/example/unifai.git
git -C "$STALE_FIXTURE_DIR" update-ref refs/remotes/origin/main "$(git -C "$STALE_FIXTURE_DIR" rev-parse HEAD)"
git -C "$STALE_FIXTURE_DIR" branch --set-upstream-to=origin/main main >/dev/null
cp "$WRAPPER" "$STALE_FIXTURE_DIR/scripts/run_vm_verifier_preflight.sh"
printf 'ahead\n' >>"$STALE_FIXTURE_DIR/seed.txt"
git -C "$STALE_FIXTURE_DIR" add seed.txt
git -C "$STALE_FIXTURE_DIR" commit -qm "ahead local tip"
STALE_VISIBLE_SHA="$(git -C "$STALE_FIXTURE_DIR" rev-parse refs/remotes/origin/main)"

set +e
STALE_VISIBLE_SHA_OUTPUT="$(
  cd "$STALE_FIXTURE_DIR" &&
  UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh "$STALE_VISIBLE_SHA" 2>&1
)"
STALE_VISIBLE_SHA_STATUS=$?
set -e
printf '%s\n' "$STALE_VISIBLE_SHA_OUTPUT"

if [ "$STALE_VISIBLE_SHA_STATUS" -eq 0 ]; then
  echo "[FAIL] Expected stale visible SHA case to fail when the local branch is ahead of the published GitHub-visible head."
  exit 1
fi

if ! grep -q "resolves to the current GitHub-visible head for 'main', but local branch 'main' is ahead by 1 commit" <<<"$STALE_VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Expected stale visible SHA failure message missing."
  exit 1
fi

if ! grep -q "Push/reconcile the local tip first, or rerun against the exact published SHA only after the local checkpoint-handoff stack matches that GitHub-visible ref." <<<"$STALE_VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Expected stale visible SHA recovery guidance missing."
  exit 1
fi

if grep -q "scripts/check_vm_host_readiness.sh" <<<"$STALE_VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Stale visible SHA case should fail before any preflight steps are planned."
  exit 1
fi

DETACHED_VISIBLE_SHA_OUTPUT="$(
  cd "$DETACHED_WORKTREE_DIR" &&
  UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh "$VISIBLE_SHA"
)"
printf '%s\n' "$DETACHED_VISIBLE_SHA_OUTPUT"

if ! grep -q "Ref: $VISIBLE_SHA" <<<"$DETACHED_VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Expected explicit visible SHA to be preserved in detached-HEAD case."
  exit 1
fi

if ! grep -q "skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA" <<<"$DETACHED_VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Expected detached-HEAD visible-SHA case to skip branch visibility."
  exit 1
fi

if grep -q "\[DRY_RUN\] bash scripts/check_github_branch_visibility.sh" <<<"$DETACHED_VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Detached-HEAD visible-SHA case should not run branch visibility."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $VISIBLE_SHA" <<<"$DETACHED_VISIBLE_SHA_OUTPUT"; then
  echo "[FAIL] Expected detached-HEAD visible-SHA case to plan the check-gate command."
  exit 1
fi

DETACHED_REMOTE_REF_OUTPUT="$(
  cd "$DETACHED_WORKTREE_DIR" &&
  UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" scripts/run_vm_verifier_preflight.sh "$VISIBLE_REMOTE_REF"
)"
printf '%s\n' "$DETACHED_REMOTE_REF_OUTPUT"

if ! grep -q "Ref: $VISIBLE_REMOTE_REF" <<<"$DETACHED_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Expected explicit remote-tracking ref to be preserved in detached-HEAD case."
  exit 1
fi

if ! grep -q "skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA" <<<"$DETACHED_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Expected detached-HEAD remote-ref case to skip branch visibility."
  exit 1
fi

if grep -q "\[DRY_RUN\] bash scripts/check_github_branch_visibility.sh" <<<"$DETACHED_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Detached-HEAD remote-ref case should not run branch visibility."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $VISIBLE_VERIFIER_REF" <<<"$DETACHED_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Expected detached-HEAD remote-ref case to run the check-gate command on the GitHub-visible verifier ref."
  exit 1
fi

if ! grep -q "Next: bash scripts/vm/verify_bootstrap_in_vm.sh $VISIBLE_VERIFIER_REF" <<<"$DETACHED_REMOTE_REF_OUTPUT"; then
  echo "[FAIL] Expected detached-HEAD remote-ref case to normalize the verifier handoff ref."
  exit 1
fi

HEADS_REF_OUTPUT="$(UNIFAI_VM_PREFLIGHT_DRY_RUN=1 "$REAL_BASH" "$WRAPPER" "refs/heads/$BRANCH")"
printf '%s\n' "$HEADS_REF_OUTPUT"

if ! grep -q "Ref: $BRANCH" <<<"$HEADS_REF_OUTPUT"; then
  echo "[FAIL] Expected normalized branch ref missing in explicit refs/heads case."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] bash scripts/check_github_branch_visibility.sh $BRANCH" <<<"$HEADS_REF_OUTPUT"; then
  echo "[FAIL] Expected branch visibility command missing in explicit refs/heads case."
  exit 1
fi

if grep -q "skipping branch-alignment check and treating it as an explicit GitHub-visible ref/SHA" <<<"$HEADS_REF_OUTPUT"; then
  echo "[FAIL] Explicit refs/heads case should not skip branch visibility."
  exit 1
fi

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $BRANCH_VERIFIER_REF" <<<"$HEADS_REF_OUTPUT"; then
  echo "[FAIL] Expected explicit refs/heads case to run the check-gate command on the GitHub-visible verifier ref."
  exit 1
fi

if ! grep -q "Next: bash scripts/vm/verify_bootstrap_in_vm.sh $BRANCH_VERIFIER_REF" <<<"$HEADS_REF_OUTPUT"; then
  echo "[FAIL] Expected explicit refs/heads case to hand off the GitHub-visible verifier ref."
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

if ! grep -q "\[DRY_RUN\] python3 scripts/check_github_check_gate.py $BRANCH_VERIFIER_REF" <<<"$DOUBLE_DASH_OUTPUT"; then
  echo "[FAIL] Expected -- separator case to run the check-gate command on the GitHub-visible verifier ref."
  exit 1
fi

if ! grep -q "Next: bash scripts/vm/verify_bootstrap_in_vm.sh $BRANCH_VERIFIER_REF" <<<"$DOUBLE_DASH_OUTPUT"; then
  echo "[FAIL] Expected -- separator case to hand off the GitHub-visible verifier ref."
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
