# After-action review — <engagement / incident>

```
date:
participants:
scope:
```

## What we set out to do

The decision from the workflow card, in the same words.

## What actually happened

Timeline from records, not recollection. Mark gaps — a missing record is a
finding about observability.

| When | What | Evidence |
|---|---|---|

## What went well

Specific and attributable. "Good collaboration" is not an entry.

## What did not

For each: the trigger (what surfaced it) and the **root cause** (why it
existed) in separate columns. They are different, and a log with only triggers
cannot tell a healthy loop from a broken one.

| Trigger | Root cause | What changed as a result |
|---|---|---|

A row where nothing changed was a retry in disguise.

## Repeat classes

Has anything here happened before with the **same root cause**? A recurrence
after a fix was attempted means the defect is upstream of where everyone is
looking. Escalate two levels, not one.

## Dispositions

Every open item gets exactly one. None is left blank.

| Finding | Fixed / Deferred / Accepted | Evidence, or date + owner, or who accepted |
|---|---|---|

A deferral without both a date and a named owner is an omission wearing a
label. Accepted risk is a legitimate outcome — a method with no name for it
does not remove those findings, it just stops counting them.

## Measurements

```
net_time_before:
net_time_after:          # including verification
correction_burden_trend:
baseline_reference:
```

## What we would tell the next engagement
