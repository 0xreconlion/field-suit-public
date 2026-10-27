---
description: Review clustered failure modes and identify which lack permanent test coverage
---
```
python3 improvement/promote.py --clusters
```

Report the failure modes, most frequent first, and name any that no eval case
covers yet.

Recommend promotion only for a mode that is **representative** and
**recurring**. A single occurrence is an observation; promote it and the
suite fills with noise that later gets ignored wholesale.

Recommend a threshold change only for a mode persisting across several
reviews. Moving a threshold on one bad week is how a suite drifts toward
whatever the system currently happens to do.

You do not promote anything. Promotion requires a human running the command
with `--confirm` and supplying a synthetic scenario that reproduces the
failure.
