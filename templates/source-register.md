# Source register — <organization>

Every source the workflow touches. The gateway decides against this; an
unregistered source is simply denied.

| source_id | owner_role | owner_holder | owner_confirmed | data_class | period | published | export_method | export_proven |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

## Rules

**Role and holder are two fields.** A name alone becomes an orphan the moment
that person leaves. A role alone is a source nobody checks.

**`owner_confirmed` is the date they confirmed it**, not the date you wrote it
down. An owner unconfirmed beyond the review window is a finding in its own
right, separate from stale data — they have different fixes.

**`export_proven` is yes only if you actually pulled one.** Attempt one real
export from every system during discovery. This is where engagements die, and
they die late if you skip it.

**`data_class` reflects what is in the file**, not where it is stored. A
spreadsheet on a shared drive holding participant names is restricted
regardless of the folder.

## Findings

| Source | Finding | Impact | Owner | Due |
|---|---|---|---|---|

Blanks in the table above belong here. The blanks are frequently the most
valuable thing discovery produces.
