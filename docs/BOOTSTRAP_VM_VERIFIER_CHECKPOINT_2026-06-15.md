# Bootstrap VM Verifier Checkpoint — 2026-06-15

## Branch
- Working branch: `transplant/fix-openclaw-config-path-and-local-mode-clean-stack`
- GitHub-visible branch head: `56aefc5`
- Latest tracked local head in the stack: `60a2b42`
- Latest non-doc logic head in the local stack: `60a2b42`
- Tracked local branch state at checkpoint: ahead by 32 commits over the GitHub-visible branch head

## Local commit stack after `5baa4b0`
1. `38a2e61` — `tests: align checkpoint refresh smoke with upstream ref`
2. `16b85ae` — `docs: refresh vm verifier boundary after smoke fix`
3. `2f62117` — `scripts: surface doc-only verifier checkpoint tip state`
4. `c4e5162` — `docs: refresh verifier checkpoint tip narrative`
5. `2ee7536` — `scripts: avoid doc-only checkpoint self-refresh loop`
6. `0064f75` — `docs: refresh verifier checkpoint after loop fix`
7. `b749009` — `docs: settle verifier checkpoint after loop fix`
8. `658ab2d` — `tests: lock verifier checkpoint tip-churn guards`
9. `3ad8f69` — `docs: refresh verifier checkpoint after tip-churn guards`
10. `b067834` — `docs: settle verifier checkpoint after tip-churn guards`
11. `22bd512` — `docs: refresh branch reconcile publish handoff`
12. `1e23487` — `scripts: ignore handoff-only verifier commits`
13. `584a5fd` — `docs: refresh verifier checkpoint after handoff fix`
14. `89ea230` — `docs: settle verifier checkpoint after handoff fix`
15. `7e2b3ce` — `docs: refresh branch reconcile publish handoff`
16. `08757c4` — `scripts: add stable verifier checkpoint alias`
17. `b1dc091` — `scripts/docs: normalize publish history refs`
18. `e4f7780` — `docs: refresh verifier checkpoint after publish ref normalization`
19. `07021dd` — `scripts/docs: normalize reviewed-drop ref forms`
20. `dbf94c6` — `docs: refresh verifier checkpoint after reviewed-drop refs`
21. `e291d8f` — `scripts: normalize refs-heads preflight inputs`
22. `9d1aac2` — `docs: refresh verifier checkpoint after preflight ref normalization`
23. `135d404` — `scripts: normalize refs-heads visibility inputs`
24. `89f872b` — `docs: refresh verifier checkpoint after visibility ref normalization`
25. `35a7757` — `scripts: normalize refs-heads check-gate inputs`
26. `18e3e3d` — `docs: refresh verifier checkpoint after check-gate ref normalization`
27. `4748903` — `scripts: normalize refs-heads vm verifier inputs`
28. `d7e3d8a` — `docs: refresh verifier checkpoint after vm verifier ref normalization`
29. `dc56858` — `scripts: normalize vm verifier remote refs`
30. `204fe73` — `scripts: normalize visibility remote refs`
31. `f8d6110` — `docs: refresh verifier checkpoint after visibility remote normalization`
32. `60a2b42` — `scripts: infer publish parity refs from handoff`
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
- The current local hardening stack has moved well beyond that earlier nine-commit checkpoint chain on top of the GitHub-visible branch: the latest tracked commit is now `60a2b42`, that same commit is also the latest non-doc logic head, the sandbox currently carries no additional uncommitted publish-boundary maintenance updates, and the branch is `ahead 32` over `fix/openclaw-config-path-and-local-mode`.
- The verifier no longer drops installer-phase VM failures on the floor: installer errors now emit the evidence bundle path plus installer-output, serial-log, and qemu-log excerpts, and that path is covered by a dedicated local smoke test.
- Bootstrap preflight now locks that installer-failure path into its own required coverage, so future verifier edits cannot silently drop it while still appearing preflight-green.
- The current local sandbox now carries no additional uncommitted publish-boundary maintenance delta beyond the tracked local stack.
- Fresh local verification at the current sandbox state is green again:
  - `python3 scripts/check_publish_stack_parity_contract.py`
  - `python3 scripts/check_compare_publish_branch_histories_contract.py`
  - `python3 scripts/check_vm_verifier_checkpoint_freshness_contract.py`
  - `python3 scripts/check_vm_verifier_checkpoint_refresh_contract.py`
  - `python3 scripts/check_vm_host_readiness_contract.py`
  - `bash scripts/smoke_test_publish_stack_parity.sh`
  - `bash scripts/smoke_test_compare_publish_branch_histories.sh`
  - `python3 -B scripts/smoke_test_vm_verifier_checkpoint_freshness.py`
  - `python3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py`
  - `bash scripts/bootstrap_installer_preflight.sh` (rerun with the publish-boundary maintenance bundle in place)
