---
name: hold
description: Pause at a clean point and report exactly where things stand
operator_configures: []
---

# hold

Stop the current work at a clean point. Start nothing new.

Then report:

- The current track.
- The exact state of any half-finished change: which files were touched, what
  is applied, what is still pending.
- What the next action would be on resume.
- The risk of leaving things exactly as they are right now.

Write nothing further and take no new action until the operator explicitly
resumes.

If the half-finished state would be confusing to someone opening this
tomorrow - including you - say precisely which files are modified and why.
**An unexplained dirty working tree is the most expensive thing to leave
behind**, because the next person cannot tell a deliberate pause from an
abandoned attempt.
