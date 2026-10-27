# Stop conditions

When to halt rather than push through. Each of these is a **delivered
finding**, not a failure — but only if you say it at the moment it becomes
true. The same observation in month three is an excuse.

---

## Stop the engagement

**No decision changes.** If nobody can name a decision that would be made
differently, there is no project — there is a demo. Report that the
engagement is scoped wrong and stop. This finding is worth more than a
delivered demo nobody opens.

**No single decision-maker.** Two principals who disagree will relitigate
every gate, and the engagement becomes an arbitration you are not being paid
for.

**No internal owner can be named.** Unowned, everything reverts in about
ninety days. If nobody can be named it is a retainer or it is not a project.

**The board will not adopt the policy.** An executive signature is not a
substitute. Proceeding produces an engagement that is not actually
authorized, and the person exposed by that is you.

**Data cannot be exported from any system of record.** Not "is messy" —
cannot be got out at all. That is a systems-replacement project wearing an AI
costume.

## Stop and re-scope

**The pilot data turns out to include regulated records.** Health, minors,
eligibility, immigration, housing or DV services. Not a permanent no — it
means aggregates first, and that work is scoped separately with its own
review and its own agreement.

**A source has no owner and nobody will take it.** Fix the ownership before
building anything on top of it.

**The workflow selected turns out to be rare.** Ten real instances could not
be found. Frequency was one of the selection criteria for a reason.

**Funding cannot accept the honest deliverable.** If the engagement is paid
from a restricted line naming a specific output, and the real finding is "the
data isn't ready", surface that with the sponsor immediately. Do not discover
it at invoicing.

## Stop the build

**The gateway needs a seventh check.** That is a v2 decision with a written
reason, not a Tuesday. An authorization layer that keeps growing becomes the
product instead of the thing protecting the product.

**A gate cannot be made deterministic offline.** It is a live-suite case and
must be labelled as one. It is never quietly skipped — an env-gated block that
skips itself has not run, and counting it as passed is a lie by default.

**Any real client data appears in the kit.** Stop, purge, rewrite history,
rotate anything exposed. This is the risk that ends the business.

**A guard reports PASS while inspecting nothing.** Fix the guard before
trusting any result it has ever given you, including the historical ones.

## Stop the run

These are enforced in code, not left to judgement:

| Condition | What happens |
|---|---|
| A required source is missing | Halt. No partial report |
| Two sources disagree on one defined metric | Halt. The system does not pick one |
| A figure traces to no source | Halt. It is not softened into prose |
| Projected cost exceeds the ceiling | Halt before spending, not after |
| Egress to a non-allowlisted host | Refused |
| Approval expired, reused, or bound to different content | Refused |

---

## The rule about arguing

**A gate is never "mostly passed".** If there is a discussion about whether a
gate passed, it did not. The discussion is the evidence.

## The rule about repetition

One loop back to fix something is the process working. The same root cause
recurring *after someone already tried to fix it* means the defect is upstream
of where you are looking. Stop and go two steps back, not one.

Record the trigger **and** the root cause separately. Without both you cannot
tell a healthy loop from a broken one, and you will either halt a working
engagement or keep re-running a broken one.
