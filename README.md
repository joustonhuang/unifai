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

# Rule 0 — Secret Sovereignty

Secrets never leave the **World Physics Secret Safe boundary**.

Examples:

- LLM API keys
- messaging gateways
- system credentials
- external service tokens

Agents never directly access secrets.  
Supervisor enforces access boundaries, while secret handling remains a separate world-physics primitive.

---

# Rule 1 — Task Routing Authority

All tasks must first be triaged by **Keyman**.

```

Agent request
↓
Supervisor
↓
Keyman (local LLM triage)
↓
easy / complex

```

Keyman only performs **task difficulty classification and routing**.

---

# Rule 2 — Local Execution (JohnDoe)

Simple tasks are executed by **JohnDoe**, a local LLM worker.

Characteristics:

- runs locally
- no secret access
- no external API calls

Typical workload:

- local reasoning
- shell automation
- data processing
- routine system tasks

JohnDoe may be replaced as hardware evolves.

---

# Rule 3 — External Oracle Invocation

Complex tasks require Advanced reasoning.

```

complex task
↓
Oracle request
↓
Supervisor selects reasoning provider
↓
reasoning provider execution

```

Reasoning providers may include:

- Lyra (Cloud-based Advanced LLM)
- Local high-capability LLM
- future reasoning providers such as another local machine running high-capability LLM

Important constraints:

- Oracle never sees API keys
- Oracle only receives Supervisor-returned results

---

# Rule 4 — System Guardian (Neo)

**Neo monitors system integrity.**

Signals monitored:

1. abnormal task failure rate
2. excessive token or API usage
3. high-risk behaviors

Examples:

- prompt injection attempts
- secret probing
- attempts to modify Supervisor
- memory manipulation

Escalation path:

```

Neo → Supervisor → Lyra consultation

```

Neo may recommend:

- pausing agents
- launching investigation
- system degradation mode

---

# Rule 5 — Kill Switch Authority

World Physics must support **Fuse / Kill Switch mechanisms**.

Capabilities:

- stop individual agents
- revoke API access
- terminate runaway loops
- no system restart required

Triggers may come from:

- Architect (Human)
- Neo
- Lyra (advisory)
- Supervisor policy

---

# Rule 6 — Budget Gate (Bill)

**Bill is the budget gate primitive in World Physics.**

Future UnifAI systems may interact with multiple generative AI services:

- GPT 5.2 or above
- Gemini 3.x or above
- Grok
- Claude
- MidJourney
- Gamma
- Canva
- future models

Bill responsibilities:

- token budget planning
- API call rate control
- resource allocation across models
- cost optimization

Bill does **not hold API keys** and must remain separate from ad hoc agent behavior.

---

# Rule 7 — Human Communication Gateway

All communication with the **Architect (Human)** must pass through the Supervisor.

Potential interfaces include:

- Telegram
- WhatsApp
- Email
- future control channels

Agents cannot directly contact humans.

```

Agent → Supervisor → notify_human()

```

---

# Rule 8 — Human Reporting (Mr. Wilson)

**Wilson is the human reporting agent.**

Role:

Reporter / Summarizer / Communication broker

Responsibilities:

- aggregate agent results
- produce human-readable summaries
- filter noise

Wilson has:

- no secret access
- no API access
- no direct communication ability

Only the Supervisor sends messages.

---

# Rule 9 — Spec & Question Ledger

To prevent agents from guessing requirements, the system maintains two ledgers.

### Specs Ledger

Stores confirmed specifications:

- scope
- constraints
- acceptance criteria
- version

---

### Questions Ledger

Unclear requirements are converted into structured questions.

```

question → Architect
answer → Specs Ledger

```

Agents read **Specs Ledger only**.

---

# Rule 10 — Dual Mode Human Interface

Two reporting modes are supported.

## Debug Mode

Output:

A + B

A: engineering detail

- task_id
- agent
- token usage
- tool calls
- stderr

B: human-readable summary

---

## Normal Mode

Output:

B only

Human-focused summaries with noise removed.

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
  - Resident agents: Wilson, Keyman, Oracle, Lyra, Neo
  - Ephemeral agents: JohnDoe
```

---

# Final Principle

Capability belongs to agents, but authority belongs to physics and constitution.  
No agent may gain authority merely by being more capable.  
Architect is final constitutional authority.

No agent may bypass governance.

---

# Morpheus (Dream Daemon)

## What is Morpheus

**Morpheus** is a background daemon responsible for **memory consolidation and restructuring**.

Its job is to:
- gather memory-relevant artifacts
- normalize memory representations
- assign confidence to memory candidates
- validate candidates against available real state
- rewrite memory structures into cleaner forms

Morpheus is **not** part of the execution path.

Morpheus is **not allowed** to:
- execute user tasks
- call tools on behalf of agents
- modify code
- modify infrastructure
- mutate external systems
- change world state
- bypass Supervisor
- issue commands to Oracle, Lyra, or other reasoning providers

Morpheus may only operate on **memory representations** and emit reviewable signals.

If a write path would affect runtime behavior outside memory representations, that action is out of scope.

---

## Why Morpheus Exists

UnifAI requires a controlled mechanism for memory evolution.

Without such a mechanism, the system accumulates several problems:

1. **Context window limitations**  
   Important state cannot remain in prompt context indefinitely.

2. **Memory drift**  
   Repeated summaries can gradually diverge from the original source.

3. **Hallucinated or unverified state**  
   A memory layer can accidentally preserve claims that were never validated.

4. **Unstructured growth**  
   Logs, notes, and ad hoc summaries become harder to query and harder to trust.

Morpheus exists to reduce these problems without turning memory maintenance into an uncontrolled autonomous behavior.

---

## Design Principles

### Skeptical Memory

Memory is treated as **hints, not truth**.

A stored memory item is not automatically treated as current fact.
Each item should remain attributable, inspectable, and revisable.

### Strict Write Discipline

Memory index updates occur only after successful validation against available evidence.

If validation is incomplete, Morpheus should preserve uncertainty rather than flatten it.

### Separation of Concerns

Execution, memory, and governance remain separate:

- execution decides what runs
- memory decides what is worth retaining
- governance decides what is permitted

Morpheus belongs to the memory layer, not the execution layer.

### Governance First

All Morpheus activity remains constrained by system rules.

Morpheus does not gain authority because it touches system memory.
It remains subordinate to world physics, constitutional boundaries, and audit review.

---

## Architecture Placement

Morpheus sits beside the operational runtime as a maintenance daemon.

It interacts with the rest of the system under explicit boundaries:

### Keyman
- Keyman may control or gate Morpheus triggers.
- Morpheus does not replace task triage.
- Morpheus does not self-authorize arbitrary runs.

### Bill
- Bill constrains Morpheus resource usage.
- Morpheus must run within explicit budget limits.
- Deep consolidation passes are budgeted, not free-running.

### Neo
- Neo provides audit and anomaly signals relevant to memory integrity.
- Morpheus may consume Neo findings during audit/validation stages.
- Morpheus may emit signals to Neo when it detects suspicious memory drift or repeated inconsistency.

### Oracle / Lyra
- No direct authority path.
- Morpheus does not directly invoke Oracle or Lyra by default.
- If future integrations require external reasoning assistance, that path must remain explicitly governed and separately budgeted.

### Supervisor
- TODO: clarify whether Morpheus is launched only via Supervisor or may also run as a separately scheduled maintenance daemon under Supervisor-observed constraints.
- Current design assumption: Morpheus must remain observable by governance even if not on the live execution path.

---

## Dream Pipeline

Morpheus operates in explicit phases.

### 1. Audit
Input is first inspected through available audit signals, including Neo output when present.

Purpose:
- detect anomalies
- detect contradiction
- detect unverified assertions
- detect stale or redundant memory candidates

### 2. Gather
Collect incremental memory inputs from:
- memory logs
- structured notes
- ledger files
- validated outputs
- project artifacts

Gather is incremental. It should not require full-history reprocessing on every pass.

### 3. Consolidate
Merge and normalize candidate memory entries.

Expected actions:
- deduplicate related entries
- merge overlapping summaries
- preserve uncertainty
- assign preliminary confidence
- assign source class

### 4. Validate
Check candidate memories against available real state.

Possible validation targets:
- codebase state
- config state
- ledger state
- current project files
- explicit human-confirmed records

If validation cannot be completed, the item should remain marked as inferred or speculative.

### 5. Prune
Remove or demote memory entries based on:
- low confidence
- age
- redundancy
- contradiction
- loss of relevance

Pruning must not silently destroy important evidence trails if the item still has audit value.

---

## Memory Model

Morpheus operates over three memory layers.

### INDEX
Examples:
- `MEMORY.md`

Properties:
- always in context
- compact
- high-signal only
- intended as the current memory index, not a raw journal

### KNOWLEDGE
Examples:
- topic files
- subsystem notes
- design references

Properties:
- loaded on demand
- more detailed than INDEX
- suitable for structured durable knowledge

### EPISODIC
Examples:
- append-only logs
- daily notes
- event traces

Properties:
- append-only by default
- rawest layer
- retains sequence and provenance
- not assumed to be clean or consolidated

### Optional metadata

Memory entries may carry:

- `confidence`
- `source`: `verified | inferred | speculative`

Optional future metadata may include:
- `validated_at`
- `staleness`
- `lineage`
- `supersedes`

TODO: define canonical metadata schema if Morpheus becomes a committed subsystem.

---

## Permission Model

Morpheus should be treated conservatively.

Allowed:
- read-only access to project data
- read access to memory artifacts
- rewrite of memory representations
- emission of audit signals

Not allowed:
- code modification
- config mutation outside memory files
- external system modification
- secret access for arbitrary use
- direct runtime control actions
- direct human messaging
- direct execution of operational tasks

Morpheus may emit **signals** to Neo or governance layers.  
It may not emit **actions**.

---

## Execution Modes

These modes are optional but useful for cost control.

### L1: Light Sweep
Purpose:
- small incremental cleanup
- duplicate detection
- stale entry review

Cost:
- lowest

Benefit:
- keeps memory from decaying between larger passes

### L2: Consolidation
Purpose:
- merge topic fragments
- normalize knowledge files
- refresh memory index

Cost:
- moderate

Benefit:
- better structural coherence

### L3: Deep Dream
Purpose:
- full cross-layer consolidation
- contradiction detection
- aggressive validation/pruning attempts

Cost:
- highest

Benefit:
- strongest restructuring pass, but most expensive and most likely to surface unresolved ambiguity

Bill should gate all nontrivial Morpheus runs.

---

## Known Limitations / Tech Debt

Current design assumptions still have unresolved gaps.

- No entropy-based trigger yet  
  Triggering logic is still manual or externally scheduled.

- Validation may be incomplete  
  Some memory candidates may not have a reliable ground-truth validation path.

- Confidence scoring heuristic is naive  
  Confidence assignment is currently heuristic, not formally calibrated.

- Integration with Neo is partial  
  Neo can conceptually support the audit phase, but the integration boundary is not yet fully specified.

- Supervisor launch boundary is still ambiguous  
  TODO: decide whether Morpheus is a Supervisor-managed subsystem, a scheduled daemon, or both.

- Memory schema is not yet canonical  
  INDEX / KNOWLEDGE / EPISODIC are structurally clear, but the exact file contract is still incomplete.

These are future-work items, not solved properties.

---

## Morpheus Boundary Summary

Morpheus may improve memory structure.  
Morpheus may not change world state.

Morpheus may rewrite memory representations.  
Morpheus may not rewrite governance, execution, or external reality.

Its role is maintenance under constraint, not autonomous action.

---

# Validation

Run the Gaia smoke test:

```bash
./scripts/smoke_test_gaia.sh
```

---

# Project Status

Early experimental architecture.

The goal is to explore **governed multi-agent AI systems** that can run even on modest hardware.

Reference node: **Little7**.
