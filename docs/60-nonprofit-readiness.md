# Nonprofit readiness

**This is the `nonprofit` vertical profile — the first one, and currently the
only signed one.** It is not the kit's boundary. See
[`65-vertical-profiles.md`](65-vertical-profiles.md) for how a profile works and
what adding another takes; read this one as the worked example of what a profile
has to establish.

A nonprofit is not a small business with a different tax status. Four
differences change the design, and each one has a mechanism attached rather
than a good intention.

---

## 1. The sensitive data is the regulated kind, by default

A small business's worst case is a customer list. A nonprofit's **routine**
case is beneficiary records: health information, minors, eligibility
determinations, immigration status, housing and domestic-violence services. A
shelter's client list is a life-safety document, not a privacy matter.

Nobody volunteers this in an intake call. They are not concealing it — it is
so ordinary to them that it does not register as a disclosure. Ask "do you
have sensitive data?" and an organization holding all of the above will say
no, meaning it.

**Mechanism.** The pre-access screen names each category explicitly, refuses
by default, and treats an unanswered question as a refusal rather than a pass.
A first engagement runs on **aggregates the organization already publishes or
already reports to a funder** — which is sufficient for the reporting
workflow, and that is what makes it an easy boundary to hold rather than a
principled one you have to keep defending.

Gates `G16`, `G17`. Ask the **data owner**, not the sponsor.

## 2. Impact reporting is the right first workflow, and it is not a demo

Monthly and quarterly reporting to a board and to funders is real, recurring,
deadline-driven, and currently assembled by hand from scattered sources. It is
also the artifact the next grant renewal turns on.

That combination is rare and it is why this is the workflow the kit proves.
The strongest outcome is not the drafted report — it is that the organization
can now say which numbers are true, who owns each one, and what the AI is
allowed to touch, and can show a funder the evidence. **Sell the legibility;
the report is the vehicle.**

## 3. Adoption is a board decision, not an executive one

At most nonprofits the executive director cannot authorize data handling
alone, and an AI use policy without board adoption does not survive the first
staff objection.

**Mechanism.** Board adoption is a gate in the deployment sequence, before
Tier 1, and the screen refuses without it (`G19`). `docs/board-one-pager.md`
is written for a board — plain language, no control identifiers, no
architecture.

This also protects you. An engagement authorized by someone who could not
authorize it is a problem that surfaces late and lands on the consultant.

## 4. Turnover makes the owner problem worse

Staff and volunteer churn is higher than in a comparable business. The named
internal owner leaves more often, and an unowned system reverts in roughly
ninety days.

**Mechanism.** The source register records a **role plus a current holder**
with a confirmation date. An owner unconfirmed beyond the review window is
reported as a finding in its own right — separately from stale data, because
they have different fixes. Gate `G04` asserts both flags appear independently.

---

## Funding and grant terms

**Flag for verification; never guess.**

Federal awards under the Uniform Guidance (2 CFR 200) and individual funder
agreements can restrict subrecipient data handling and the use of
subprocessors. This is **agreement-specific and jurisdiction-specific**. Read
the actual terms or route to counsel. Do not state a compliance position from
a framework summary — including this one.

There is also a commercial trap worth checking early: an organization paying
from a restricted grant line with a named deliverable may be unable to
*accept* "your data isn't ready" as that deliverable, however true it is.
Establish how the engagement is funded before it starts, not at invoicing.

---

## Budget reality

A nonprofit cannot absorb a surprise API bill, and "it got expensive" is how a
pilot dies without anyone recording it as a failure.

**Mechanism.** Cost is a gate. A run projected over its ceiling halts and
reports rather than completing and billing (`G13`). The posture assumes
batching — a monthly board report is not interactive, so a 24-hour turnaround
is irrelevant against a monthly deadline and costs roughly half. Stable
context is cached; extraction and freshness sweeps route to a cheap model and
only genuine ambiguity reaches an expensive one.

Resolve live pricing at call time. Never quote stored rates to a client.

---

## The conversation that decides the engagement

Ask early, in these words:

> *If we find that the numbers you report to funders don't reconcile with
> each other, is that something you want to know?*

If the answer is yes, the engagement is viable and that finding is probably
your most valuable deliverable.

If the answer is anything else, stop. The kit halts on exactly that condition
by design, and an organization that does not want to hear it will experience
the halt as the tool being broken.
