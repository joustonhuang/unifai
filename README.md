GPL-3.0 License
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
This software is licensed under the GNU General Public License v3.0 (GPL-3.0). See the LICENSE file for details.

# UnifAI

**A governed agentic AI operating system.**

**Run your own AI society -- locally.**

UnifAI is built on the **UnifAI Protocol** — a governance-first architecture with distinct physics, constitutional, and runtime layers.

UnifAI explores a structured approach where agents operate inside hard mechanics and constitutional law, rather than inheriting authority from capability.

The system was co-designed by Jouston Huang <jouston@linux.com> with assistance from Lyra, a cloud-based advanced LLM used for high-level reasoning.

---

# Philosophy

Most AI systems start with models and tools.

UnifAI starts with **governance**.

The project aims to build a governed agentic AI operating system in which AI agents, humans, and external models operate within a structured constitutional framework.

```
world physics
→ constitution
→ docker world (agents and tools)
```

The goal is to prevent uncontrolled agent behavior and build systems that remain **auditable, predictable, and controllable**.

---

# Lyra–Little7 Constitution (v0.3)

The UnifAI runtime follows a minimal governance framework with three explicit layers.

## Core Principle

**Authority belongs to World Physics and Constitution, not to agent capability.**

Supervisor is the enforcement boundary of the World Physics layer, not merely a coordinator.
Supervisor enforces authority boundaries but is not itself a sovereign actor.

The Supervisor must remain:

- minimal
- auditable
- human-understandable

## Three-Layer Structure

1. World Physics  
   hard mechanics and enforcement primitives:  
   Secret Safe, Bill/Budget gate, Fuse/Kill Switch, and Supervisor boundary
2. Constitution  
   governing law for all agents and mechanisms; amendments can be proposed, but Architect has final ratification authority
3. Docker World  
   operational runtime where resident and ephemeral agents actually execute work

---

# Global Invariant — Logging Is Mandatory

All agents must produce complete, structured, and traceable logs for every meaningful action.

No action is considered valid unless it is logged.

## Logging principles

- Every state transition must be logged
- Every decision must be attributable
- Every escalation must be traceable
- Every external interaction must be recorded
- Logs must be immutable once written
- Logs must be auditable by Neo
- Logs must be consumable by Wilson
- Logs must be usable by Morpheus
- Logs must be encrypted while remaining auditable

## Minimum required log fields

- timestamp
- agent_id
- task_id
- trace_id
- action_type
- input_summary
- output_summary
- decision_reason
- token_usage (if applicable)
- cost_estimate (if applicable)
- escalation_flag
- error_state (if any)

If an action is not logged, it is treated as non-existent or as a violation.

---

# Rule 0 — Secret Sovereignty

Secrets never leave the **World Physics Secret Safe boundary**.

Examples:

- LLM API keys
- messaging gateways
- system credentials
- external service tokens

Agents never directly access secrets.
Supervisor enforces access boundaries, while secret handling remains a separate world-physics primitive.

Rule:
> All secrets remain in Supervisor. Agents never hold secrets directly.

---

# Rule 1 — 3-Agent + 4-Ledger Governed Orchestration

We use a **3-agent + 4-ledger** layout to deal with task assignment and triage.

The system no longer uses **Keyman** as a central dispatcher.

Core architecture:

```text
Wilson -> Uncleared Ledger
Oracle -> Cleared + Agile Ledger
Gaia -> Current <-> JohnDoe
                 ^ Morpheus (Dreaming)
                 ^ Supervisor (Terminating)
```

This is a governed orchestration system, not a strict linear router.

The four ledgers are:
- Uncleared Ledger
- Cleared Ledger
- Agile Ledger
- Current Task Ledger

---

# Rule 2 — Wilson: Intake + Human Interface

Wilson has dual responsibilities.

Responsibilities:
- accept Architect input
- write Uncleared Ledger
- present human-readable logs
- never mutate raw logs

Logging:
- must log all input ingestion
- must log all human-facing summaries
- must preserve trace_id linkage

Constraints:
- Wilson does not execute tasks
- Wilson does not interpret deeply
- Wilson does not mutate raw logs

---

# Rule 3 — Oracle: Structuring Intelligence

Oracle transforms unclear input into structured, actionable representations.

Responsibilities:
- transform Uncleared into Cleared + Agile, using Uncleared and Cleared as context
- disambiguate intent
- structure tasks
- always reason with an advanced LLM (cloud, local, or hybrid)

Logging:
- must log reasoning steps in compressed but traceable form
- must log task transformation decisions
- must log prioritization decisions
- must log escalation triggers

Constraints:
- Oracle does not execute tasks
- Oracle does not directly control workers
- Oracle does not bypass governance layers

---

# Rule 4 — Gaia: Orchestration Layer

Gaia is responsible for execution planning and dispatch.

Responsibilities:
- assign tasks to JohnDoe
- maintain Current Task Ledger
- monitor performance
- mark JohnDoe for dreaming via Morpheus when needed

Logging:
- must log task assignment
- must log worker lifecycle state
- must log performance signals
- must log termination decisions

Constraints:
- Gaia is not a dictator
- Gaia does not invent tasks outside defined scope
- Gaia operates within governance constraints

---

# Rule 5 — JohnDoe: Ephemeral Worker Pool

JohnDoe are short-lived execution agents.

Responsibilities:
- execute tasks
- produce results

Logging:
- must log execution steps
- must log progress signals
- must log outputs
- must log escalation requests
- must log failure states

Lifecycle rule:
A JohnDoe exists only while producing value.

Termination must be logged with reason:
- no_progress
- loop_detected
- cost_exceeded
- task_completed

---

# Rule 6 — Keyman: Secret Gatekeeper

Keyman is no longer a central dispatcher.

Responsibilities:
- validate legitimacy of requests
- approve or deny access to secrets
- issue temporary secret usage grants

Logging:
- must log every validation decision
- must log scope approval
- must log denial reasons

Constraints:
- Keyman does not route tasks
- Keyman does not orchestrate workflows
- Keyman does not execute actions

---

# Rule 7 — Bill: Budget Gate

Bill is the budget / token / cost control primitive in World Physics.

Responsibilities:
- evaluate budget
- evaluate token approval or denial
- evaluate cost thresholds

Logging:
- must log budget evaluation
- must log token approval or denial
- must log cost thresholds

Bill does not hold API keys and must remain separate from ad hoc agent behavior.

---

# Rule 8 — Supervisor: Boundary Enforcement

Supervisor owns:
- secrets
- external calls
- enforcement boundaries
- worker termination

Logging:
- must log secret injection
- must log secret stripping
- must log external calls
- must log worker termination

All communication with the Architect must pass through Supervisor-owned governed paths.

---

# Rule 9 — Neo: Audit Layer

Neo consumes logs.

Responsibilities:
- detect anomalies
- detect missing logs
- detect inconsistent trace chains
- detect loop patterns
- detect abnormal persistence

Neo must be able to reconstruct any task purely from logs.

---

# Rule 10 — Morpheus: Memory Lifecycle

Morpheus consumes logs and artifacts.

Responsibilities:
- consolidate memory
- validate memory candidates
- prune low-value memory
- support dreaming for marked workers

Logging:
- must log consolidation steps
- must log validation confidence
- must log pruning decisions

Morpheus operates on logs and artifacts as source material.

---

# Governed Escalation

All escalation must be logged end-to-end with shared trace_id.

```text
JohnDoe
-> Oracle
-> Keyman
-> Bill
-> Supervisor
-> External reasoning
-> Supervisor return
-> Oracle
```

Each step must produce a log entry with shared trace linkage.

---

# Dual Mode Human Interface

Two reporting modes are supported.

## Debug Mode

Output:
A + B

A: engineering detail
- task_id
- agent_id
- trace_id
- timestamps
- duration
- token usage
- tool calls
- stderr

B: human-readable summary

## Normal Mode

Output:
B only

Human-focused summaries with noise removed.
WebUI is currently view-only.

---

# System Architecture (Simplified)

```text
Architect (human final ratifier)
  |
World Physics layer:
  - Supervisor (enforcement boundary)
  - Secret Safe
  - Bill (Budget gate)
  - Fuse / Kill Switch
  |
Constitution layer
  |
Docker World layer:
  - Resident agents: Wilson, Oracle, Gaia, Keyman, Bill, Neo, Morpheus, Lyra
  - Ephemeral agents: JohnDoe
```

---

# Final Principle

Capability belongs to agents, but authority belongs to physics and constitution.
No agent may gain authority merely by being more capable.
Architect is final constitutional authority.

No agent may bypass governance.

Logging is governance.
