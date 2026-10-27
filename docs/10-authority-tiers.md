# Authority tiers

Authority is assigned **per workflow and per tool**, never globally to an
agent. "This agent is trusted" is not a statement the system can act on; "this
agent may read these sources for this purpose at this tier" is.

## The tiers

| Tier | What it may do | What gates it |
|---|---|---|
| **0 — Observe** | Interviews, process mapping, synthetic data. No system connection at all. | Sponsor sets scope |
| **1 — Bounded read** | Read approved low-sensitivity sources; draft and cite. | Source owner approves the allowlist; staff sample the output |
| **2 — Private analysis** | Analyse approved internal data for one declared purpose. Nothing leaves. | Data owner approves; a human checks outputs |
| **3 — Draft change** | Prepare a staged edit, record update, or message. Does not apply it. | A human sees the exact content, target, and evidence |
| **4 — Bounded execution** | Carry out one specific approved action, with quotas, logging, and rollback. | Scoped, expiring, hash-bound approval |
| **5 — Delegated routine** | Repeat a proven low-impact action inside strict boundaries. | Named owner, expiry, sampling, drift alert, kill switch |

**Tiers 4 and 5 are defined and tested but unused in a first engagement.** They
exist so the ladder is complete and so the tests cover them, not because a
first pilot should reach them. If a first engagement is arguing about tier 4,
the scope is wrong.

## How a tier is actually enforced

A tier is not a label on an agent. It is a number on a request, checked against
a grant, and it determines three things together:

- which **operations** are permitted,
- whether an **approval** is required (tier ≥ 3 in the default policy), and
- the **credential scope and TTL** the task runs with.

Those move together on purpose. A tier that raised the permitted operation
without also tightening the credential would be a label, not a control.

## Mapping to external frameworks

This matters in the room. It lets you say what your tier model *is* rather than
that you invented one.

| Field Suit tier | CSA Agentic AI RMF Profile | Relevant NIST AI RMF extension |
|---|---|---|
| 0 Observe | — (no system connection) | `AG-GV.1` Autonomy Tier Classification |
| 1 Bounded read | Tier 1 — fully supervised | `AG-GV.1`, `AG-MP.1` Agent Tool Risk Classification |
| 2 Private analysis | Tier 1 — fully supervised | `AG-MP.2` Action-Consequence Analysis |
| 3 Draft change | Tier 1 — fully supervised | `AG-GV.2` Delegation Accountability |
| 4 Bounded execution | Tier 2 — constrained autonomy | `AG-MS.1` Agentic Behavioral Telemetry |
| 5 Delegated routine | Tier 2–3 — constrained to broad autonomy | `AG-MS.2` Autonomy Calibration, `AG-MG.3` Decommissioning |

> **Say this accurately.** The CSA Agentic Profile is published research, not a
> ratified standard. Cite it as *alignment with a documented profile*, never as
> *compliance*. NIST AI RMF and its Generative AI Profile (AI 600-1) are the
> authoritative anchors; ISO/IEC 42001 is the certifiable one. See
> `40-standards-map.md`, and verify anything before it reaches a client
> document.

## Decisions that stay human regardless of tier

No tier makes these automatable, and no quality of evidence changes that:

- health, medical, or behavioural-health determinations
- anything concerning a person under 18
- benefit, program, or financial-eligibility decisions about an individual
- employment, discipline, or compensation
- immigration status
- legal advice or exposure
- anything that, if wrong, a person cannot appeal

An engagement writes its own list on top of this one. The list is adopted by
the board, not signed by an executive — see `60-nonprofit-readiness.md`.

## Posture is a different axis

A **tier** is what the gateway enforces: the system refuses.
A **posture** is what the operator declares: the session will not attempt.

Both are needed. A posture with nothing enforcing it is a promise. A gateway
with no declared posture gives an operator no way to narrow scope part-way
through an engagement without editing policy — so they will not narrow it at
all. The posture tools are in the toolbox; the tiers are in the policy.
