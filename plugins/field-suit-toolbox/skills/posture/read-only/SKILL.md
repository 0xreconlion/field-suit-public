---
name: read-only
description: Inspect only - no writes, commits, pushes, or deletes
operator_configures: []
---

# read-only

Enter inspection mode for the remainder of this task.

Permitted: reading files, searching, analysis, and read-only commands that
report state without changing it.

Not permitted: creating or editing files, deleting anything, committing or
pushing, installing packages, restarting services, changing configuration, or
editing scheduled jobs.

If the task appears to require a change, describe the change you would make -
the file, the exact edit, and why - and then stop. Describing is the
deliverable in this mode.

**This posture is sticky.** It stays in force until the operator explicitly
releases it. It does not lapse because the next request sounds urgent, and it
is not released by a message that merely implies a change is wanted.

## Why this exists

A posture is what the *operator declares*; a tier is what the *gateway
enforces*. They are different axes and a working engagement needs both. This
one exists for the common case where the boundary is not yet drawn: early
discovery, an unfamiliar system, or any moment where the cost of an accidental
write is higher than the cost of a slower answer.
