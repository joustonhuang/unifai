# Bootstrap VM Verifier Checkpoint — 2026-06-15

## Branch
- Working branch: `transplant/fix-openclaw-config-path-and-local-mode-clean-stack`
- GitHub-visible branch head: `22560dc`
- Latest tracked local head in the stack: `fd70521`
- Latest non-doc logic head in the local stack: `fd70521`
- Tracked local branch state at checkpoint: ahead by 43 commits over the GitHub-visible branch head

## Local commit stack after `5baa4b0`
1. `f4946cd` — `vm: require scp before verifier report copyback`
2. `c3dd862` — `docs: refresh vm verifier checkpoint handoff`
3. `a11ed88` — `docs: stabilize vm verifier checkpoint state`
4. `368306a` — `docs: settle publish-boundary handoff state`
5. `b08bbca` — `docs: refresh vm verifier checkpoint state`
6. `517fb5a` — `Fail closed on stale visible verifier refs`
7. `770c55c` — `docs: refresh vm verifier checkpoint handoff`
8. `a52708d` — `docs: stabilize vm verifier checkpoint state`
9. `a8fd1a9` — `docs: refresh branch reconcile handoff`
10. `d60a675` — `docs: refresh verifier checkpoint tracked-state wording`
11. `c162042` — `docs: settle verifier checkpoint after refresh`
12. `d3545e2` — `docs: settle verifier checkpoint after handoff refresh`
13. `f0ea7c4` — `tests: align freshness handoff wording`
14. `d57739d` — `docs: refresh verifier checkpoint after freshness sync`
15. `e39100a` — `docs: refresh branch reconcile handoff note`
16. `9095881` — `docs: refresh publish stack reconciliation note`
17. `738e084` — `docs: settle publish stack reconciliation note`
18. `adfadc7` — `docs: settle verifier checkpoint clean state`
19. `727c61a` — `docs: settle publish stack reconciliation counts`
20. `ff09dc0` — `scripts: allow publish reconciliation handoff noise`
21. `3508234` — `docs: refresh verifier checkpoint after parity allowlist`
22. `0645ea4` — `docs: settle verifier checkpoint after parity allowlist`
23. `8436a69` — `docs: refresh publish reconciliation after local preflight`
24. `b6d5618` — `docs: settle publish reconciliation after local preflight`
25. `54de5e2` — `docs: settle verifier checkpoint after local preflight`
26. `f244c03` — `scripts: stabilize verifier checkpoint self-maintenance`
27. `00e047e` — `docs: refresh verifier checkpoint after self-maintenance`
28. `40d79dc` — `docs: settle verifier checkpoint after self-maintenance`
29. `13312b7` — `scripts: stabilize clean checkpoint settle handoff`
30. `bef6417` — `docs: refresh verifier checkpoint after clean settle handoff`
31. `0eaa4b7` — `docs: settle verifier checkpoint after clean settle handoff`
32. `5e719ad` — `docs: refresh publish-boundary handoff artifacts`
33. `d0eea6c` — `docs: settle verifier checkpoint after handoff refresh`
34. `cc82711` — `docs: settle publish stack reconciliation note`
35. `69a1acf` — `Add runtime truth webui snapshot view`
36. `a56b49c` — `Fix webui startup route banner`
37. `470050e` — `Add dedicated runtime truth webui page`
38. `fb43f6b` — `docs: refresh verifier checkpoint after runtime truth webui tip`
39. `2569913` — `docs: settle verifier checkpoint after runtime truth webui tip`
40. `56533f1` — `docs: settle publish reconciliation after webui tip`
41. `5e718f7` — `scripts: stabilize publish reconciliation note tracking`
42. `b99ef75` — `docs: settle publish reconciliation after tracking fix`
43. `fd70521` — `scripts: verify recorded visible verifier head`
## What is now true locally
- Bootstrap installer preflight remains green.
- The bootstrap-preflight workflow itself is now pinned to Node24-safe GitHub Action majors (`actions/checkout@v5`, `actions/setup-python@v6`, `actions/upload-artifact@v5`), and the workflow contract checker now fails locally if those pins drift.
- Bootstrap installer preflight now also smoke-tests the GitHub branch-visibility helper in a temporary repo, so the “is this branch actually GitHub-visible?” gate no longer relies on syntax-only coverage.
- Bootstrap installer preflight now has its own explicit contract checker and an offline smoke test for the GitHub check-gate inspector, so the preflight scaffold and required-check diagnosis path are both self-tested instead of syntax-only guarded.
- The GitHub check-gate inspector is now more resilient on busy commits: it paginates through check runs and annotations, still prioritizes the likely root failure signal, and caps noisy annotation dumps with an omission summary.
- The verifier-preflight remote-boundary hardening bundle is now preserved as a clean local checkpoint commit: `7756061` (`dev: harden verifier preflight remote boundary`).
- Live host-readiness has improved since the older missing-QEMU note: the required verifier tools are present on this host, and the current live state is narrower (`/dev/kvm` is present but not writable, `gh` is installed and authenticated, no `GH_TOKEN`/`GITHUB_TOKEN` is exported).
- The verifier path now has three distinct local guard layers before VM boot:
  1. branch visibility check
  2. GitHub required-check gate inspection
  3. one-command wrapper for the common preflight flow
- The wrapper is protected by:
  - syntax checking in bootstrap preflight
  - a contract checker (`scripts/check_vm_verifier_preflight_contract.py`)
  - a dry-run smoke test (`scripts/smoke_test_vm_verifier_preflight_wrapper.sh`)
- The latest local hardening commit narrows one more mismatch between smoke coverage and real operator repos:
  - the preflight-wrapper smoke test now auto-detects the GitHub-backed remote instead of assuming a hard-coded `github` remote name
  - explicit local SHAs now have a dedicated fail-closed smoke path when no GitHub-backed remote can be detected at all
  - bootstrap preflight and its contract checkers now require that missing-GitHub-remote smoke path
  - the wrapper contract checker now also forbids the stale hard-coded smoke ref `github/fix/openclaw-config-path-and-local-mode`, so this exact GitHub-visible failure mode cannot quietly re-enter the local bundle
- Fresh local `bash scripts/bootstrap_installer_preflight.sh` reruns are green with the current publish-boundary maintenance bundle in place.
- `ci-artifacts/bootstrap-preflight/commit-candidate.txt` now captures the current local checkpoint, host-readiness snapshot, verification gates, and the exact next visible-ref move as a one-file handoff.
- The verifier/preflight stack now has fail-closed smoke coverage for:
  - GitHub branch visibility divergence
  - GitHub required-check success/failure inspection with annotations
  - forced red-path failure
  - GitHub fallback SHA-resolution failure
  - explicit local SHA preflight failure when no GitHub-backed remote exists
  - SSH-never-ready excerpt surfacing from serial/qemu logs
  - remote-verification failure excerpt surfacing from installer/report/serial/qemu logs
  - remote-verification failure when `report.txt` cannot be copied back from the VM
- Bootstrap installer preflight now also executes two more realistic local verifier-environment probes instead of only syntax-checking them:
  - a forced-TCG launch smoke path for `scripts/vm/verify_bootstrap_in_vm.sh`
  - a host-readiness helper smoke test for `scripts/check_vm_host_readiness.sh`
- The current local hardening stack has moved well beyond that earlier nine-commit checkpoint chain on top of the GitHub-visible branch: the latest tracked commit is now `fd70521`, that same commit is also the latest non-doc logic head, the sandbox currently carries 3 uncommitted publish-boundary maintenance updates, and the branch is `ahead 43` over `fix/openclaw-config-path-and-local-mode`.
- The verifier no longer drops installer-phase VM failures on the floor: installer errors now emit the evidence bundle path plus installer-output, serial-log, and qemu-log excerpts, and that path is covered by a dedicated local smoke test.
- Bootstrap preflight now locks that installer-failure path into its own required coverage, so future verifier edits cannot silently drop it while still appearing preflight-green.
- The current local sandbox now carries 3 uncommitted publish-boundary maintenance updates beyond the tracked local stack:
  - `ci-artifacts/bootstrap-preflight/commit-candidate.txt`
  - `ci-artifacts/vm-verifier-checkpoint-latest.md`
  - `docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md`
- Fresh local verification at the current sandbox state is green again:
  - `python3 scripts/check_publish_stack_parity_contract.py`
  - `python3 scripts/check_publish_stack_reconciliation_note.py`
  - `python3 scripts/check_publish_stack_reconciliation_note_contract.py`
  - `python3 scripts/check_compare_publish_branch_histories_contract.py`
  - `python3 scripts/check_branch_reconcile_handoff.py`
  - `python3 scripts/check_branch_reconcile_handoff_contract.py`
  - `python3 scripts/check_github_branch_visibility_contract.py`
  - `python3 scripts/check_vm_verifier_checkpoint_freshness_contract.py`
  - `python3 scripts/check_vm_verifier_checkpoint_refresh_contract.py`
  - `python3 scripts/check_vm_host_readiness_contract.py`
  - `bash scripts/smoke_test_publish_stack_parity.sh`
  - `bash scripts/smoke_test_compare_publish_branch_histories.sh`
  - `bash scripts/smoke_test_publish_stack_reconciliation_note.sh`
  - `bash scripts/smoke_test_branch_reconcile_handoff.sh`
  - `python3 -B scripts/smoke_test_vm_verifier_checkpoint_freshness.py`
  - `python3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py`
  - `bash scripts/bootstrap_installer_preflight.sh` (rerun with the publish-boundary maintenance bundle in place)
