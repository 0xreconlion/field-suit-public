# Preconditions

This kit is used **after** process mapping and definition, not instead of it.
`scripts/configure.py` refuses to write anything until all six exist, and it
names which one is missing.

That refusal is the point. Configuring against guesses does not produce
obvious failures — it produces confident wrong answers, which are much harder
to notice and much more expensive when someone finally does.

---

| # | Precondition | The artifact | Why the kit cannot proceed without it |
|---|---|---|---|
| 1 | **One workflow, named and observed** | Workflow card with ten real instances | Ten instances, not three. Three shows you the happy path, which is the part that did not need you |
| 2 | **Every source named, owned, classified** | Source register: role **and** current holder, data class, export method proven | The gateway's resource scope and data-class checks decide against this. An unregistered source is simply denied |
| 3 | **Every number defined once** | Metric dictionary with one named source of truth and explicit extraction labels | This is the accuracy lever, not paperwork. A metric with no declared label is resolved by guesswork, and guesswork is how a wrong figure enters a board report |
| 4 | **A frozen baseline** | Signed before-picture, never recomputed | Every later claim is measured against it. A baseline you adjusted is not a baseline |
| 5 | **Human-only decision list** | Written, board-adopted | The tier model needs to know what no tier may reach |
| 6 | **A named accountable human** | Role plus current holder | Loop exit gate. Unowned, everything reverts in about ninety days |

---

## What "named and observed" actually means

Not "the director described it in a meeting." Observed means you watched the
task happen, wrote down the inputs, the handoffs, the exceptions, and the
rework, and collected ten real instances of the output.

The exceptions are the part people skip and the part that decides whether the
workflow is automatable at all. A task that is clean eight times in ten and
requires judgement twice is not an eighty-percent win — it is a task where
someone now has to check all ten to find the two.

## What "owned" actually means

A **role** and the **current holder**, separately, with a confirmation date.

Recording only a name produces an orphan the moment that person leaves.
Recording only a role produces a source nobody actually checks. Turnover in a
small organization is high enough that an owner confirmed eight months ago is
a finding rather than a record — which is why the freshness check flags
unconfirmed ownership as its own defect, distinct from stale data. They have
different fixes: one needs a fresh export, the other needs a person to say
"yes, still me."

## What "defined once" actually means

One metric, one definition, one source of truth — and a written rule for what
happens when a second source disagrees.

In the synthetic fixture two sources report unique participants as 486 and
492, with a known unresolved cause. The dictionary's rule is
`halt_on_conflict`, deliberately not `prefer_source_of_truth`. A six-person
gap with an explanation nobody has closed is a finding for a human. Quietly
preferring one source hides exactly the operational problem the engagement
was hired to surface.

---

## If a precondition is missing

The answer is not "configure it anyway". The answer is that **discovery is not
finished**, and saying so is a delivered finding with a document attached.

Most often the missing one is #2 or #3, and most often the reason is the same:
the export was assumed rather than attempted, or the number was assumed to
have one definition rather than checked. Both are cheap to discover in week
one and expensive to discover at the readout.
