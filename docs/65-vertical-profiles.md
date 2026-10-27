# Vertical profiles — and why adding one is your decision, not a config change

Almost all of this kit is vertical-neutral. The gateway's six checks, the
content-bound approvals, the egress allowlist, the cost ceiling, the
trace→eval loop and both guards care about *what an action is*, not about what
kind of organization is doing it. A path-traversal refusal is the same refusal
at a food bank and at an HVAC contractor.

Two questions are not neutral, because their correct answer depends on how the
organization is governed:

| Question | Nonprofit | Owner-operated business |
|---|---|---|
| Who can adopt an AI use policy? | The governing board. An executive signature is frequently **not authorized at all** | The owner or managing member who can bind the business |
| Which third-party agreements restrict data handling? | Grant and funder terms | Customer contracts, DPAs, insurance |

Flattening those into one sentence fails in both directions. Demand board
adoption from a sole proprietor and you have invented a requirement nobody can
satisfy, so it gets waived, and a waived gate teaches that gates are
negotiable. Accept "the person in charge signed it" from a nonprofit and you
may have an engagement that was never actually authorized — which is the
failure the gate exists to prevent.

So the vertical is **named explicitly** in `answers.json`, each profile carries
its own wording, and anything unrecognised is **refused rather than matched to
the nearest profile**.

## Status

| Key | Profile | State |
|---|---|---|
| `nonprofit` | Nonprofit or NGO with a governing board | **Signed and usable** |
| `owner_operated` | Owner-operated business (sole proprietor, LLC, partnership) | **Signed 2026-10-03 and usable** |

## How `owner_operated` was decided (2026-10-03)

It shipped disabled with its wording visible, so the open question could be
argued rather than assumed. The question was **separation of duties**: in a
nonprofit the board adopts the policy and a different person can stop the work,
and that split is doing real work. In an owner-operated business the owner is
both.

**Decision: one owner holding both roles is acceptable here.** They carry the
whole liability and there is nobody above them. Requiring a second signatory
would produce a spouse or a direct report rubber-stamping it, and a fake control
is worse than an acknowledged missing one because it reads as coverage in your
own documentation.

**But the reason the split mattered does not disappear.** A named stop authority
assumes that person can be impartial when the thing they commissioned starts
going wrong, and an owner cannot be. So the control was not dropped, it was
**moved**: from a person who decides in the moment to **conditions decided in
advance**. The `halt_conditions` precondition requires the stopping triggers to
be written down and objective — checkable facts, not "if it goes wrong."

That is the same move the rest of this kit makes everywhere else: a gate rather
than a good intention. **Gate 23** asserts the profile refuses without it, so the
compensating control cannot quietly become advice. **Gate 26** is the positive
control — gates 22, 23 and 24 are all refusals, and a refusal-only set would be
satisfied by a screen that rejects everything.

`halt_conditions` is required in **every** vertical, not just this one. It is a
tightening, it weakens nothing already signed, and a nonprofit board benefits
from the same pre-commitment.

## Enabling a profile

1. Answer its open question in writing, in the `sign_off` field of the profile
   in `src/field_suit/configure/screen.py`. Name who decided and when — "signed
   by X, date, on this basis". Not "reviewed".
2. Set `enabled=True`.
3. Add it to `VERTICALS` in `tools/engagement-setup.html` so the form can offer
   it. Gate 21 fails if the form and the screen disagree about the question
   *keys*; it does not check the dropdown, so this step is on you.
4. **Gate 23 will now fail**, because it asserts `owner_operated` is refused.
   That failure is the point: it forces the test to be rewritten deliberately
   by whoever made the decision, rather than the decision slipping in
   unnoticed. Re-point it at a profile that is still unsigned, or replace it
   with a case asserting the newly signed rule.
5. Write the vertical's own readiness document, the way
   [`60-nonprofit-readiness.md`](60-nonprofit-readiness.md) does for nonprofits:
   what differs, and what mechanism holds each difference. A profile without
   one is a label, not a design.

## Adding a profile that is not either of these

The same five steps, plus: work out what the two table rows above say for that
vertical *before* writing any code. If you cannot name who holds policy
authority and which agreements bind the data, you do not understand the
engagement well enough to configure it — which is the same conclusion the
pre-access screen reaches, one step earlier.

A vertical is not a market segment here. It is a governance shape. Two
businesses in different industries with the same ownership structure are the
same profile; a nonprofit and a B-corp in the same industry are not.
