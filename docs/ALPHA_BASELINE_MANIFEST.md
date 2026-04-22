# Alpha Baseline Manifest

This document freezes the Alpha baseline after PR #13 so future debugging, audit, and dogfood runs can trace the installed boundary set.

## 1. PR13 Infrastructure (The Foundation)

- Stage 20: Deterministic Bootstrap (Pinning SecretVault hashes).
- Stage 30: Agent-Browser Cage (Wrapper & process eradication).
- Privilege Drop: Dedicated unifai-operator (No-root execution).

## 2. Folded Intelligence (Oracle & Morpheus)

- Oracle Interpreter: Explicit detection for 401/403/503 (Codex/Gateway failures).
- Morpheus Daemon: Skeptical Memory logic (Codebase-first validation).
  ↳ Gen1 implementation: evidence integrity checker using SHA256 hash verification.
     Superseded in PR22 (Gen3): Morpheus redefined as write-only dreaming/reclamation
     lifecycle step. No decision authority. Trigger: task_completed log → dreaming
     (memory consolidation + context reset) → worker_dreamed log. The validation role
     was removed; governance enforcement moved entirely to world_physics layer.
- Delivery Path: Structured incident signaling via Telegram.
- MCP Interceptor Security Hardening: Active detection and blockage of governance-bypass parameters (dangerouslyBypassGovernance) inspired by prior agent-tool leak analysis.

## 3. Committed Traceability

- PR13 original baseline: ff6ec5f -> 9d94bd8.
- Debug-mode additions: c982f87 -> f9432bd.

## 4. Debug-Mode Consolidation Note

- Accepted PR13 baseline: deterministic bootstrap, SecretVault hash pinning, agent-browser cage, and no-root execution.
- Folded back from PR14 / PR15: Oracle incident interpretation, Morpheus skeptical memory, and Telegram incident delivery.
- Official alpha baseline in debug mode: the bundled set above; future failures should be traced by commit lineage, not by PR title alone.
