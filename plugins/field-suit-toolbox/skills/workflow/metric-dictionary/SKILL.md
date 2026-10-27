---
name: metric-dictionary
description: Define every reported number exactly once, with one named source of truth, explicit extraction labels, and a written rule for disagreement.
operator_configures:
  - freshness_window_days
  - reconciliation_defaults   # what happens when two sources disagree
---

# metric-dictionary

This is the accuracy lever, not paperwork. A structured definition file is
consistently the highest-leverage artifact in a reporting workflow, and the
cheapest to produce.

## One entry per number

| Field | Rule |
|---|---|
| `id` | Stable identifier |
| `label` | What a human calls it |
| `definition` | Prose precise enough to settle an argument |
| `unit` | Always. "500" is not an answer |
| `source_of_truth` | Exactly one source |
| `corroborating_sources` | Others that also publish it |
| `extraction_labels` | The **exact** strings that identify it in a source |
| `reconciliation_rule` | What happens when they disagree |

## Extraction labels are exact, never fuzzy

List the literal labels. No keyword matching, no stemming, no "close
enough".

An extractor that infers which number in a document is the metric is the
single most likely place a wrong figure enters a report. "Total
participants" quietly binding to "Total unique participants served" is
exactly how it happens, and nothing downstream will catch it because the
number is real, cited, and wrong.

Two sources may spell the same metric differently — they usually do. That is
why the list is per-metric and adding a spelling is a visible diff someone
reviews.

## The definition has to settle an argument

Write it so two staff members who disagree can read it and find out who is
right. "Participants served" does not do that. "Distinct individuals who
attended at least one session of any program during the period,
de-duplicated across programs" does.

Money terms break in more ways than anything else. Decide explicitly whether
a figure includes or excludes tips, discounts, comps, refunds, in-kind, and
restricted funds. Each of those has ended an argument badly at a board
meeting somewhere.

## Halting is usually the right reconciliation rule

When two sources disagree, prefer `halt_on_conflict` over silently
preferring the source of truth.

A discrepancy with an unresolved cause is a finding about the organization's
operations, and it is frequently the most valuable thing the engagement
delivers. Quietly preferring one source hides exactly the problem you were
hired to surface.

Use `single_source` only when genuinely one source publishes the number.

## A metric with no declared labels

Resolves to nothing and is reported missing. That is intentional. An
undeclared metric must never be resolved by guesswork.
