# Standards map

What this kit aligns with, stated precisely enough to survive a security
reviewer's follow-up question.

> **The rule for this whole document.** Say *aligns with* or *is informed by*.
> Never say *compliant* or *certified* unless an accredited body has issued a
> certificate. The difference is the entire point of the distinction, and a
> client's auditor will know it even if the client does not.
>
> Everything below was current when written. **Re-verify before it appears in
> a client deliverable** — frameworks revise, deadlines move, and a stale
> citation is worse than no citation because it looks researched.

---

## NIST AI Risk Management Framework — the anchor

Voluntary US framework organised around four functions: **GOVERN, MAP,
MEASURE, MANAGE**.

**NIST AI 600-1**, the *Generative AI Profile*, supplements it with a
GenAI-specific risk taxonomy — around 200 suggested actions across twelve
named risks. One of the twelve is **Human-AI configuration**, which is
directly what the tier and approval model addresses.

Use AI 600-1 as a **layer on top of** the base framework, not a replacement:
the base gives you the governance structure, the profile gives you the
GenAI-specific mitigations.

| This kit | Function | Evidence |
|---|---|---|
| Authority tiers, named accountable roles | GOVERN | `docs/10-authority-tiers.md`, generated `AGENTS.md` |
| Source register, data classification, destination rules | MAP | `policy.json`, source register |
| Gate suite, correction burden over time | MEASURE | `evals/`, `improvement/` |
| Halt conditions, egress deny, cost ceiling, kill switch | MANAGE | `containment.json`, gates 12–13 |

## CSA Agentic AI RMF Profile — the agent-specific extension

Extends the base RMF to autonomous agents, covering four things base RMF does
not: autonomy classification, tool-use risk, runtime behavioural monitoring,
and delegation-chain accountability. Control identifiers use an `AG-` prefix.

| Control | What it asks for | Where it lives here |
|---|---|---|
| `AG-GV.1` Autonomy Tier Classification | Classify each agent's autonomy | `docs/10-authority-tiers.md`; tier is a field on every request |
| `AG-GV.2` Delegation Accountability | Document what may happen without approval, and when the agent must escalate | `policy.json` grants; `approval_required_at_tier` |
| `AG-GV.3` Agent Lifecycle Registry | Business owner, technical owner, review conditions | `agents` block with mandatory expiry; source register records role + holder |
| `AG-MP.1` Agent Tool Risk Classification | Classify tools by risk | Operations per grant; read-only adapters |
| `AG-MP.2` Action-Consequence Analysis | Analyse what an action causes | Halt precedence; human-only decision list |
| `AG-MS.1` Agentic Behavioral Telemetry | Runtime behavioural monitoring | `improvement/traces` |
| `AG-MS.2` Autonomy Calibration | Check autonomy is set correctly over time | Failure-mode clustering, recalibrate only on a persistent mode |
| `AG-MG.1` Agentic Incident Response | Named response procedure | Incident agents in the toolbox |
| `AG-MG.2` Behavioral Drift Detection | Detect drift | Cluster review on a cadence |
| `AG-MG.3` Agent Decommissioning | Retire agents deliberately | Registrations expire; no permanent agent |

> **Status matters.** This is published research from a labs programme, **not
> a ratified standard**. Cite it as alignment with a documented profile. A
> client who later discovers you implied it was a standard will re-read
> everything else you told them.

## OWASP Top 10 for Agentic Applications — the threat taxonomy

Used as the organising spine of `docs/20-threat-model.md`, with a disposition
per risk. This is the list a client's own security reviewer is most likely to
arrive holding, which is why the threat model is written against it rather
than against a structure of our own.

**Verified 2026-09-29** against `genai.owasp.org`: *OWASP Top 10 for Agentic
Applications for 2026*, v1.0, published 2025-12-09. The identifiers in
`docs/20-threat-model.md` are correct as written and safe to cite.

## ISO/IEC 42001 — the certifiable one

The AI Management System standard. This is the only item here a client can
actually be *certified* against, which makes it the right thing to position as
a **destination**, not a deliverable.

Useful, verifiable-as-of-writing context for an SMB or nonprofit conversation:

- Certification typically runs **4–9 months** for a small or mid-sized
  organization.
- Cost is meaningfully lower for an organization already holding ISO 27001 or
  9001, because 42001 shares the Annex SL high-level structure and can be
  integrated rather than built from scratch.
- Three-year certificate with annual surveillance audits.

What this kit contributes toward a future 42001 effort: an AI inventory, named
roles and owners, a written use policy, documented risk treatment, performance
monitoring, and a corrective-action loop. That is genuine groundwork. **It is
not a pre-audit and it does not shorten Stage 2.**

## EU AI Act — jurisdiction first

Only relevant if the organization places AI systems on the EU market or its
output is used in the EU. **Establish that before discussing it at all** —
most US nonprofits are out of scope, and raising it anyway manufactures
anxiety you then have to talk them down from.

If in scope, as of writing:

- The **Digital Omnibus** (Regulation (EU) 2026/1744, in force 2026-07-27)
  deferred Annex III standalone high-risk obligations from 2026-08-02 to
  **2027-12-02**, and Annex I product-embedded systems to **2028-08-02**.
- **Article 50 transparency duties did not move** and applied from
  **2026-08-02** — telling people they are interacting with an AI system, and
  labelling AI-generated content.

Note which of those two facts is the one most summaries get wrong: the
deferral was widely reported, the unchanged Article 50 date less so.

**Do not extrapolate any of this to US state law.** That is a separate,
fast-moving, state-by-state question.

## What to actually put in front of a client

One page, in this order:

1. **NIST AI RMF + AI 600-1** — what the governance model is built on.
2. **The tier table** with its CSA mapping — what the system will and will not
   do on its own.
3. **The threat model dispositions** — what was considered and what remains.
4. **ISO/IEC 42001** — where this leads if they want a certificate.

Leave EU AI Act out unless jurisdiction is established. Leave the control IDs
out unless a security reviewer is in the room; for an executive director they
are noise, and noise reads as evasion.
