---
description: Run the pre-access screen for an engagement before anything is configured or connected
---
Run the pre-access screen and report the result. Do not write any configuration.

```
python3 scripts/configure.py --answers $ARGUMENTS --dry-run
```

Report the screen outcome and, if it passed, read the plain-English posture
summary back to the operator.

The screen refuses by default. An unanswered disclosure question is a
refusal, not a pass. If it refuses, report exactly which category or
precondition caused it — do not summarise it as "some checks failed", because
the specific category is the thing the operator has to go and ask about.

Ask the data owner, not the sponsor. The sponsor generally does not know what
is in the systems and will answer honestly and wrongly.
