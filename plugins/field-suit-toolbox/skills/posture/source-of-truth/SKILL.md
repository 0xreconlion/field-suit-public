---
name: source-of-truth
description: Lock scope - treat the named file or folder as canonical
operator_configures:
  - canonical_path  # the file or folder to treat as authoritative
---

# source-of-truth

Canonical source: the path the operator names when invoking this.

For the remainder of this task:

- Read it before answering any question it covers.
- Reconcile conflicting information **toward** it.
- Never create a competing copy of anything it owns.
- If another file disagrees with it, flag the divergence explicitly. Do not
  silently pick one and move on.
- If the work requires changing the canonical source itself, say so before
  editing it, and treat that as a decision rather than a step.

## Why this exists

The most common cause of a wrong figure in a report is not a bad calculation.
It is two files that both look authoritative, drifting apart, with nobody
having decided which one wins. This posture makes that decision explicit and
records it for the duration of the task.
