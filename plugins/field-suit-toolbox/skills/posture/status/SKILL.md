---
name: status
description: Report current state only - no writes, no edits, no extra work
operator_configures: []
---

# status

Report current state and nothing else.

Cover, in order:

1. The current track - what is actually being worked on right now.
2. Done / in flight / blocked.
3. Repository state for anything active: branch, uncommitted files, whether it
   is ahead or behind its remote.
4. Any background jobs, scheduled tasks or timers that are running.
5. Anything parked - deferred items that are still open.

Read-only commands only. No writes, edits, commits, or new work of any kind.

End by naming the next step. **Do not take it.** A status report that quietly
starts the work it was describing is no longer a status report, and the
operator has lost the one moment they had to redirect.
