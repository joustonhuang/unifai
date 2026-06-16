# Bootstrap VM Verifier Checkpoint — 2026-06-15

## Branch
- Working branch: `fix/openclaw-config-path-and-local-mode`
- GitHub-visible branch head: `5baa4b0`
- Local branch state at checkpoint: ahead by 12 commits

## Local commit stack after `5baa4b0`
1. `d8c9143` — `dev: add GitHub branch visibility check`
2. `517332a` — `dev: add GitHub check gate inspector`
3. `3063370` — `dev: fold check gate inspector into preflight`
4. `48bc63e` — `docs: clarify verifier preflight flow`
5. `3f57e39` — `scripts: add vm verifier preflight wrapper`
6. `588eb85` — `scripts: relax verifier preflight ref handling`
7. `e85623d` — `tests: guard verifier preflight wrapper contract`
8. `ab2a7b2` — `tests: smoke test verifier preflight wrapper`
9. `d18e5ff` — `docs: checkpoint vm verifier branch state`
10. `d0551e5` — `ci: pin bootstrap preflight actions to node24-safe majors`
11. `b5c3210` — `docs: refresh vm verifier checkpoint state`
12. `e724750` — `tests: smoke test github branch visibility gate`

## What is now true locally
- Bootstrap installer preflight remains green.
- The bootstrap-preflight workflow itself is now pinned to Node24-safe GitHub Action majors (`actions/checkout@v5`, `actions/setup-python@v6`, `actions/upload-artifact@v5`), and the workflow contract checker now fails locally if those pins drift.
- Bootstrap installer preflight now also smoke-tests the GitHub branch-visibility helper in a temporary repo, so the “is this branch actually GitHub-visible?” gate no longer relies on syntax-only coverage.
- The verifier path now has three distinct local guard layers before VM boot:
  1. branch visibility check
  2. GitHub required-check gate inspection
  3. one-command wrapper for the common preflight flow
- The wrapper is protected by:
  - syntax checking in bootstrap preflight
  - a contract checker (`scripts/check_vm_verifier_preflight_contract.py`)
  - a dry-run smoke test (`scripts/smoke_test_vm_verifier_preflight_wrapper.sh`)
- The verifier itself still has fail-closed smoke coverage for:
  - GitHub branch visibility divergence
  - forced red-path failure
  - GitHub fallback SHA-resolution failure

## Known real blocker
- First real VM proof still cannot start from this branch until these local commits become GitHub-visible.
- The last GitHub-visible ref tested was `5baa4b0`, and its required check `Bootstrap Installer Preflight` was red, so verifier execution stopped before VM boot.

## Recommended next move when external boundary opens
1. Make the current branch head GitHub-visible.
2. Run:
   ```bash
   bash scripts/run_vm_verifier_preflight.sh <github-visible-ref>
   ```
3. If that passes, run:
   ```bash
   bash scripts/vm/verify_bootstrap_in_vm.sh <github-visible-ref>
   ```
4. If the gate is red again, inspect it first with:
   ```bash
   python3 scripts/check_github_check_gate.py <github-visible-ref>
   ```

## Why this checkpoint exists
This branch now contains several small local hardening commits. The main risk is not code uncertainty but restart friction and losing the verified sequence. This note preserves the exact branch state and next action boundary.
