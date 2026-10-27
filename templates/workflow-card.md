# Workflow card — <workflow name>

Filled during observation, not from a description in a meeting. If this was
written from what someone told you, mark it `observed: no` and treat every
figure in it as unverified.

```
workflow_id:
owner_role:
owner_holder:
observed_by:
observed_on:
instances_collected:     # must be 10. Three shows you the happy path
```

## The decision this changes

One decision, in the business's own words, that someone makes today and would
make differently. **If no decision changes, there is no project — there is a
demo.** Say so now, not in month three.

> 

Who is accountable when it is wrong? A name, not a department:

> 

## The task as it actually runs

| Step | Who | Input | Output | Typical time |
|---|---|---|---|---|

## Handoffs

Every point where the work leaves one person and arrives at another. Handoffs
are where time disappears and where nobody feels responsible for the delay.

| From | To | What is passed | How | Typical wait |
|---|---|---|---|---|

## Exceptions — the part that decides feasibility

Do not skip this. A task that is clean eight times in ten and needs judgement
twice is **not** an eighty percent win — it is a task where someone now has to
check all ten to find the two.

| Exception | Frequency | Who resolves it | How long |
|---|---|---|---|

## Rework

What gets sent back, by whom, and why. Rework that nobody logs is the single
most under-counted cost in the baseline.

## Ten real instances

| # | Date | Notes | Anything unusual |
|---|---|---|---|
| 1 | | | |

## Baseline

```
net_time_per_instance:      # including verification and exception handling
error_definition:           # agreed BEFORE measuring
error_rate:
frozen_on:
signed_by:
```

Never recompute the baseline. A baseline you adjusted is not a baseline.

## Manual fallback

What people do when the system is down. If the answer is "there isn't one",
that is both a design constraint and a risk — record it as both.
