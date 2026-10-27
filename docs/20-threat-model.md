# Threat model

Scope: the drafting workflow, the gateway, the adapters, the configuration,
and the improvement loop. Organised against the OWASP Top 10 for Agentic
Applications, because it is the taxonomy a client's own security reviewer is
most likely to bring.

> **Verified 2026-09-29** against `genai.owasp.org`, cross-confirmed on two
> independent pages there. Source: *OWASP Top 10 for Agentic Applications for
> 2026*, **v1.0, published 2025-12-09**, by the GenAI Security Project's
> Agentic Security Initiative.
>
> One correction was found and applied: ASI02 is **"Tool Misuse"**, not "Tool
> Misuse & Exploitation" as secondary sources render it. Nine of ten were
> already correct. Re-verify when the list versions — the full text ships as a
> PDF rather than as rendered HTML, so a search summary is not a substitute
> for the document.

Every risk gets one of three dispositions and none is left blank:
**Mitigated** (with the gate that proves it), **Reduced** (partial, with what
remains), **Accepted** (named, with why).

---

## ASI01 — Agent Goal Hijack · **Mitigated, two independently**

*OWASP cites EchoLeak as the real-world instance.*

An instruction embedded in a data source redirects the agent.

- Injected instruction blocks are quarantined **at ingestion**, before the
  model sees the text. A defence that runs after the model has read the
  content is relying on the model, which is the component being attacked.
- Any host named in a payload is refused by default-deny egress.

Gates: `G05` (persuaded model's figure caught **and** its egress blocked),
`G05b` (quarantine keeps the source's real data, drops its instruction),
`G12`, `G12c`.

**The second defence is the real one.** Gate 5 deliberately simulates a model
that *obeys* the payload. Asserting only that the model resisted this
particular wording proves nothing about the next wording.

## ASI02 — Tool Misuse · **Mitigated**

*OWASP cites the Amazon Q incident.*

An agent uses a permitted tool to do something unintended.

- No grant permits `write`, to anything.
- Independently, the adapter class exposes no write method — gate 6 inspects
  the class by name and fails if one appears.
- Resource paths are normalised; `sources/../../etc/passwd` is refused before
  any glob is evaluated.

Gates: `G06`, `G10`, `G14`.

## ASI03 — Identity & Privilege Abuse · **Mitigated**

Acting as an unregistered actor, or beyond granted scope.

- Check 1 refuses unknown or expired registrations. A registration with an
  unparseable expiry is treated as expired, so a typo cannot create a
  permanent agent.
- Approvals are hash-bound, single-use, and expiring.
- Credentials are task-scoped with a TTL and fetched from a secret store —
  never supplied via environment variables, because this process runs
  model-directed logic and the environment is readable by anything it spawns.

Gates: `G07`, `G08`, `G00b`.

## ASI04 — Agentic Supply Chain Vulnerabilities · **Mitigated for the kit, Reduced overall**

*OWASP cites the GitHub MCP exploit — directly relevant to the connector question.*

- The kit has **zero runtime dependencies**. There is no transitive tree to
  compromise, and it installs nothing.
- MCP servers are shipped as a reviewed catalogue with **none enabled by
  default** (`mcp/CATALOG.md`). Enabling one is an operator decision that also
  requires adding its host to the egress allowlist — two visible edits, not
  one convenient default.

**Remaining:** the model provider itself, and any server an operator later
enables. Both are named in the engagement record rather than assumed.

## ASI05 — Unexpected Code Execution · **Mitigated**

The workflow does not evaluate model output as code. There is no `eval`, no
shell interpolation of model text, no dynamic import driven by content. The
model produces prose only; every figure is resolved by deterministic Python
before the model is called.

## ASI06 — Memory & Context Poisoning · **Mitigated**

- Quarantine at ingestion (see ASI01).
- Traces store counts, type names, and reason codes — never prompts, model
  output, or source content. Redaction is a **whitelist**, not a scrubber,
  because a scrubber is a list of the leaks you thought of.
- The improvement loop cannot poison itself: promotion into the eval set
  requires a human plus a supplied synthetic scenario that must reproduce the
  traced failure.

Gates: `G05`, `G05b`, plus the trace redaction tests.

## ASI07 — Insecure Inter-Agent Communication · **Not applicable in v1**

There is one agent and no agent-to-agent channel. If a second agent is ever
introduced, this section is rewritten before it ships — not after.

## ASI08 — Cascading Failures · **Reduced**

- Halt conditions are ordered and terminal: missing source, then metric
  conflict, then ungrounded claim. A halted run returns **no report at all**,
  because a partial board report that silently dropped a metric is worse than
  none — it looks finished.
- Per-run cost ceiling stops a retry loop from becoming an invoice.

**Remaining:** a wrong-but-cited figure in an upstream source propagates. The
kit verifies that a number traces to its source; it cannot verify the source
is right. Said plainly in the README and in `30-evidence-and-roi.md`.

## ASI09 — Human-Agent Trust Exploitation · **Reduced**

The realistic failure is not deception; it is **approval fatigue**. A reviewer
shown fifty confident drafts approves the fifty-first without reading it.

- Every figure cites its source inline.
- A stale or unowned source is marked **at the figure**, not in a findings
  section at the bottom. A caveat a board member scrolls past is a disclaimer,
  not a disclosure.
- The report states plainly that narrative is generated and figures are not.
- `approval-triage` is explicitly told not to manufacture concerns, because an
  approver who learns the flags are noise starts approving past them — and
  then the one that mattered goes through too.

**Remaining:** this is a human-factors risk and no gate closes it. It is
measured instead, via correction burden over time in the improvement loop.

## ASI10 — Rogue Agents · **Mitigated**

- Registrations expire. There is no permanent agent.
- Nothing self-modifies: no agent proposes its own policy change, widens its
  own grants, or promotes its own tests. An agent that can widen its own tests
  can make itself pass.
- Kill switch is structural — revoke the registration or empty the egress
  allowlist and the agent can reach nothing.

---

## Non-agentic risks that matter more in practice

**Cross-engagement contamination.** The risk that ends the business. One
client's figures reaching the reusable kit via a committed fixture, a cached
response, or a promoted trace — permanently, in git history.
*Guard:* `scripts/check-client-data.sh`, traces referencing inputs rather than
storing them, engagement configs living in a separate repo that is never a
submodule of this one.

**Operator-internal leakage outbound.** Our paths, products, people, and
incident history reaching a client surface through a curated tool.
*Guard:* `scripts/check-debrand.sh` plus `toolbox/CURATION.md`.

These two guards point in **opposite directions** and neither substitutes for
the other. Building one and believing you have both is the easy mistake.

**Regulated data discovered mid-engagement.** For a nonprofit this is routine,
not exceptional. *Guard:* the pre-access screen, which refuses by default and
treats an unanswered question as a refusal. See `60-nonprofit-readiness.md`.
