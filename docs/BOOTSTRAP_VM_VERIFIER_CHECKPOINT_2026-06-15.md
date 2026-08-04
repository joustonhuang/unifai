# Bootstrap VM Verifier Checkpoint — 2026-06-15

## Branch
- Working branch: `transplant/fix-openclaw-config-path-and-local-mode-clean-stack`
- GitHub-visible branch head: `56aefc5`
- Latest tracked local head in the stack: `74d075e`
- Latest non-doc logic head in the local stack: `74d075e`
- Tracked local branch state at checkpoint: ahead by 94 commits over the GitHub-visible branch head

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
33. `9d8f26b` — `docs: refresh verifier checkpoint after parity handoff`
34. `29dce10` — `tests: cover doc-only publish parity handoff`
35. `4931289` — `tests: pin doc-only parity smoke coverage`
36. `da3d6a3` — `tests: pin publish history smoke coverage`
37. `63ed054` — `docs: refresh verifier checkpoint after history coverage`
38. `a2f36b6` — `scripts: align doc-only visible checkpoint handoff`
39. `0af6edd` — `docs: refresh verifier checkpoint after visible handoff align`
40. `e540d02` — `tests: pin freshness branch-state smoke coverage`
41. `91e4c63` — `tests: pin aligned refresh smoke coverage`
42. `62fff56` — `tests: pin aligned freshness smoke coverage`
43. `1ae800f` — `tests: cover aligned visible-ref tip leaks`
44. `bb0b797` — `tests: cover head tip leak freshness regressions`
45. `3083a31` — `docs: refresh verifier checkpoint after freshness coverage`
46. `864b681` — `tests: cover aligned freshness branch-state drift`
47. `2b10140` — `docs: refresh verifier checkpoint after aligned freshness drift`
48. `68d5405` — `docs: refresh branch reconcile publish handoff`
49. `d14b8f3` — `docs: stop branch reconcile handoff self-staleness`
50. `c46d074` — `scripts: check branch reconcile handoff`
51. `b291fb1` — `scripts: wire branch reconcile handoff into preflight`
52. `50d27f5` — `docs: refresh verifier checkpoint after preflight rerun`
53. `22b67ed` — `scripts: harden verifier checkpoint handoff refresh`
54. `254fd1a` — `docs: refresh verifier checkpoint after handoff hardening`
55. `f839edd` — `docs: stabilize verifier checkpoint handoff wording`
56. `c0589e3` — `docs: refresh post-preflight handoff state`
57. `11c76e0` — `docs: settle post-preflight handoff state`
58. `68306e0` — `tests: cover GITHUB_TOKEN host-readiness fallback`
59. `889eeab` — `docs: refresh verifier checkpoint after token coverage`
60. `32c0dc1` — `docs: settle token coverage handoff`
61. `0160eb0` — `tests: harden vm host readiness contract coverage`
62. `9c32439` — `docs: settle host readiness contract coverage handoff`
63. `bd61860` — `docs: refresh branch reconcile handoff`
64. `acea8e8` — `scripts: track branch-visibility checkpoint gate`
65. `cda64f0` — `docs: refresh checkpoint verification gates`
66. `5c50083` — `docs: settle checkpoint verification gates`
67. `659999f` — `tests: pin branch visibility preflight coverage`
68. `fbbc5b8` — `tests: pin github check gate preflight coverage`
69. `93c2da9` — `tests: pin checkpoint freshness preflight coverage`
70. `696b1ab` — `docs: refresh verifier checkpoint handoff`
71. `60a2219` — `docs: settle verifier checkpoint handoff wording`
72. `3f02079` — `docs: refresh branch reconcile handoff`
73. `e29a900` — `scripts: guard preflight checkpoint handoff dirtiness`
74. `e7f1f12` — `docs: refresh verifier checkpoint after dirty-state guard`
75. `bf704dd` — `docs: refresh verifier checkpoint after dirty-state guard`
76. `0783943` — `docs: refresh branch reconcile handoff state`
77. `177ea1b` — `tests: pin verifier preflight meta-contract coverage`
78. `7eee718` — `tests: pin verifier preflight wrapper meta-contract`
79. `74338af` — `docs: refresh verifier checkpoint after wrapper meta-contract`
80. `8e87b80` — `docs: settle verifier checkpoint after wrapper meta-contract`
81. `9453584` — `docs: refresh branch reconcile handoff state`
82. `ef14bee` — `tests: pin visible branch-reconcile handoff state`
83. `fea475c` — `docs: refresh verifier checkpoint after visible handoff coverage`
84. `e62de6f` — `docs: settle verifier checkpoint after visible handoff coverage`
85. `7fe219c` — `docs: refresh branch reconcile handoff after visible coverage`
86. `98b2160` — `scripts: ignore branch-reconcile handoff in publish parity`
87. `f1407e4` — `docs: refresh verifier checkpoint after publish parity handoff`
88. `60d9723` — `docs: settle verifier checkpoint after publish parity handoff`
89. `8192385` — `docs: refresh branch reconcile handoff after publish parity`
90. `0a42ae1` — `tests: pin checkpoint refresh tip handoff`
91. `7d15e13` — `docs: refresh publish boundary handoff state`
92. `145d920` — `docs: settle publish boundary clean state`
93. `0aef2c8` — `docs: refresh branch reconcile handoff state`
94. `74d075e` — `tests: cover publish parity inferred-ref failures`
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
- The current local hardening stack has moved well beyond that earlier nine-commit checkpoint chain on top of the GitHub-visible branch: the latest tracked commit is now `74d075e`, that same commit is also the latest non-doc logic head, the sandbox currently carries 3 uncommitted publish-boundary maintenance updates, and the branch is `ahead 94` over `fix/openclaw-config-path-and-local-mode`.
- The verifier no longer drops installer-phase VM failures on the floor: installer errors now emit the evidence bundle path plus installer-output, serial-log, and qemu-log excerpts, and that path is covered by a dedicated local smoke test.
- Bootstrap preflight now locks that installer-failure path into its own required coverage, so future verifier edits cannot silently drop it while still appearing preflight-green.
- The current local sandbox now carries 3 uncommitted publish-boundary maintenance updates beyond the tracked local stack:
  - `ci-artifacts/branch-reconcile-2026-07-10.md`
  - `docs/BOOTSTRAP_VM_VERIFICATION.md`
  - `docs/BOOTSTRAP_VM_VERIFIER_CHECKPOINT_2026-06-15.md`
- Fresh local verification at the current sandbox state is green again:
  - `python3 scripts/check_publish_stack_parity_contract.py`
  - `python3 scripts/check_compare_publish_branch_histories_contract.py`
  - `python3 scripts/check_github_branch_visibility_contract.py`
  - `python3 scripts/check_vm_verifier_checkpoint_freshness_contract.py`
  - `python3 scripts/check_vm_verifier_checkpoint_refresh_contract.py`
  - `python3 scripts/check_vm_host_readiness_contract.py`
  - `bash scripts/smoke_test_publish_stack_parity.sh`
  - `bash scripts/smoke_test_compare_publish_branch_histories.sh`
  - `python3 -B scripts/smoke_test_vm_verifier_checkpoint_freshness.py`
  - `python3 -B scripts/smoke_test_vm_verifier_checkpoint_refresh.py`
  - `bash scripts/bootstrap_installer_preflight.sh` (rerun with the publish-boundary maintenance bundle in place)
