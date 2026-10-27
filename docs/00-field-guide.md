# Field guide

How to run an engagement with this kit. Read `PRECONDITIONS.md` first — if
those are not in place, none of this applies yet.

This kit is **not a method**. The method is whatever delivery process you
already run. This is the executable layer that sits underneath it: contracts,
gates, a working workflow, and a tool shelf. If you find yourself explaining
the kit as a methodology, something has gone wrong — a second competing
process is the most reliable way to end up running neither.

---

## The shape of an engagement

Nothing below starts before the one above it finishes.

### 1. Before any access

Signed, in writing, before anything connects:

- Confidentiality and data-handling agreement
- A named sponsor
- A named **stop authority** — someone who can halt this at any moment
- Excluded areas, written down
- A retention rule
- The human-only decision list

### 2. Board adoption

The AI use policy is **adopted by the governing board**, not signed by an
executive. At most nonprofits the executive director cannot authorize data
handling alone, and a policy without board adoption does not survive the
first staff objection.

Use `docs/board-one-pager.md`. It is written for a board, not for you.

### 3. Pre-access screen

```
python3 scripts/configure.py --template > answers.json
python3 scripts/configure.py --answers answers.json --dry-run
```

Ask the **data owner**, not the sponsor. The sponsor generally does not know
what is in the systems, and will answer honestly and wrongly.

It refuses by default. An unanswered question is a refusal.

### 4. Tier 0 — observe

Interviews and process mapping on synthetic data. No connection.

Produce the workflow card: inputs, handoffs, exceptions, rework, and **ten
real instances**. Ten, not three. Three instances shows you the happy path,
which is the part that did not need you.

### 5. Source register and one real export per system

Attempt **one real export from every system**, during discovery.

This is where engagements actually die, and they die late if you skip it.
"Clean the data" presumes the data can be got out at all, and a great many
small-organization systems have no export, no API, or a CSV on a fixed
cadence someone has to request. Promising a report before you have pulled one
export is how you end up building a data-entry job.

Record each source's owner as a **role plus the current holder**. In an
organization with high turnover, a role with no current holder is a finding,
not a blank.

### 6. Freeze the baseline

Snapshot the before-picture, get it signed, and **never recompute it**. Every
claim you make later is measured against this. A baseline you adjusted is not
a baseline.

### 7. Configure

```
python3 scripts/configure.py --answers answers.json --out ../engagement-<client>
```

The engagement config lives in **its own private repository**. It is never a
submodule of the kit, and no client data ever enters this repo.

`--dry-run` prints the posture in plain English. **Read it aloud to the
sponsor.** If a line surprises them, the configuration is wrong even though it
validated.

### 8. Shadow mode

Staff do the work as they always have. The system drafts in parallel. Nobody
depends on it. You are measuring, not deploying.

### 9. Measure net time — including verification

The only number that counts is **net** time: the task plus the human checking
of it. A system that halves drafting time and doubles review time has
achieved nothing, and will be discovered to have achieved nothing at the worst
possible moment.

### 10. Handoff

Named operator, rehearsed rollback (executed once, on purpose, before
handover), after-action review, and every security finding dispositioned:
**Fixed** with evidence, **Deferred** with a date and an owner, or **Accepted
risk** by a named human in writing. A deferral without both a date and an
owner is an omission wearing a label.

---

## The conversation you must be willing to have

**If the data is too poor, the deliverable is the cleanup project, not a
chatbot.**

Say it at the source register, not at the readout. It is a delivered finding
with documents attached, and it is worth more than a demo nobody uses — but
only if you say it in week one. In month three it is an excuse.

Check how the engagement is funded before you start. An organization paying
from a restricted grant line with a named deliverable may not be able to
*accept* "your data isn't ready" as that deliverable, however true it is. That
is a conversation to have with the sponsor up front, not with the funder
later.

---

## Running the pieces

```
./scripts/bootstrap.sh                      # what interpreter, no installs
python3 evals/run.py                        # the gate suite, offline
python3 evals/run.py --live                 # separate suite, separate report
python3 improvement/promote.py --clusters   # failure modes, review cadence
./scripts/check-client-data.sh              # no client data in the kit
./scripts/check-debrand.sh                  # no internals on a client surface
```

Run the last two before anything leaves your machine. They guard **opposite
directions** and neither substitutes for the other.

---

## Things that will bite you

- **A demo is not a pilot.** A demo proves the happy path exists. Shadow mode
  proves the decision moves.
- **"Basically agreed" is not signed.** It is the phrase that precedes the
  most expensive misunderstanding in the engagement.
- **A conflict is not an error to resolve on their behalf.** Two sources
  disagreeing about one defined number is a finding about their operation, and
  it is frequently the most valuable thing you deliver.
- **An unowned source reverts within about ninety days.** If nobody can be
  named, it is a retainer or it is not a project.
