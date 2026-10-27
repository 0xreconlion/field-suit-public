---
name: source-register
description: Build or audit a source register: every source named, owned by a role AND a current holder, classified, and proven exportable.
operator_configures:
  - review_window_days   # how long an owner confirmation stays valid
  - data_classes         # the classification scheme in use
---

# source-register

Build the register that everything else depends on. A gateway can only
protect sources it knows about; an unregistered source is simply denied.

## One row per source

| Field | Rule |
|---|---|
| `source_id` | Stable. Never reuse an id for a different source |
| `owner_role` | The job, not the person |
| `owner_holder` | The person doing that job **today** |
| `owner_confirmed` | The date they last confirmed it. Not the date you wrote it down |
| `data_class` | public / internal / confidential / restricted |
| `period` | What the data covers |
| `published` | When it was produced |
| `export_method` | **Proven**, not assumed |

## Role and holder are two fields, not one

Recording only a name produces an orphan the moment that person leaves.
Recording only a role produces a source nobody actually checks. In an
organization with real turnover, an owner confirmed eight months ago is a
finding rather than a record.

Stale *data* and stale *ownership* are reported separately because they have
different fixes: one needs a fresh export, the other needs a person to say
"yes, still me."

## Prove the export. Do not assume it.

Attempt **one real export from every system**, during discovery.

This is where engagements die, and they die late if you skip it. "Clean the
data" presumes the data can be got out at all, and plenty of small-
organization systems have no export, no API, or a CSV someone has to request
on a cadence. Record what actually happened: the format, the effort, who had
to be asked, and how long it took.

If an export requires a person to do something manual every month, that is
not an integration. Write it down as a dependency with a name attached.

## Classify honestly

Classify by **what is in the file**, not by where it is stored or how it is
labelled. A spreadsheet on a shared drive holding participant names is
restricted regardless of the folder it sits in.

If a source mixes classes, split it or classify it at its highest. Never
average.

## What makes a register finished

Every source has a holder confirmed inside the review window, a proven
export method, and a class. A blank in any of those is a finding to report,
not a field to fill in later — the blanks are frequently the most valuable
thing discovery produces.
