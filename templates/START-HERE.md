# Start here

This folder drafts your impact report from files you already have, and shows
where every number came from.

You do not need the internet to check it works. You do not need to install
anything. You do not need the person who set this up.

---

## The two commands

```
./verify.sh     Proves the safety rules still work.  Takes seconds.
./run.sh        Drafts this period's report.
```

That is the whole interface. Everything else is files you edit.

**Run `./verify.sh` first, and any time you want reassurance.** It checks that
the system still refuses the things it is supposed to refuse. If it ever says
anything other than all-passed, stop and ask for help before trusting a report.

---

## What goes where

| Folder | What you put there |
|---|---|
| `sources/` | The files your numbers come from, as Markdown |
| `config/metric-dictionary.json` | What each number means and which file it comes from |
| `reports/` | What comes out |
| `config/` | Settings. Only `metric-dictionary.json` is yours to edit — leave the others alone |
| `docs/` | The templates and the board one-pager |

---

## The one rule for a source file

Each number you want reported must appear on its own line, in bold, like this:

```
**Total people served (2026-08): 492**
```

Then in `config/metric-dictionary.json`, the `extraction_labels` entry must be that
exact label:

```
"extraction_labels": ["Total people served"]
```

**Exact.** Not close. If the file says *"Total people served"* and the
dictionary says *"Total participants"*, it will not match, and the system will
say the number is missing rather than guess.

That is on purpose. Guessing which number in a document is the right one is
how a wrong figure ends up in front of a board.

---

## What it will refuse to do

This is the useful part. It stops rather than producing something wrong:

- **A number it cannot trace to one of your files.** It stops. It will not
  round it off into a sentence.
- **Two of your files disagreeing about the same number.** It stops and shows
  you both. It does not pick one. *You will probably hit this, and it is
  usually the most valuable thing it tells you.*
- **A file it needs that is not there.** It stops. It does not quietly leave
  the number out — a report with something silently missing looks finished.
- **Out-of-date files.** It still writes the report, but marks the warning
  **next to the number**, not in a footnote at the end.
- **Instructions hidden inside one of your files.** If a document contains
  text telling the system what to do, it ignores it and records it. Documents
  are information, not orders.
- **Sending anything anywhere.** It has no permission to email, upload, or
  post. It reads your files and writes a report.
- **Changing any of your systems.** It cannot write to anything.

---

## When it stops

It tells you which of the above happened, and which file. Fix the file, run it
again. Nothing is broken — stopping *is* the feature.

If it stops on two files disagreeing: that is a real difference in your
records. Work out which is right, correct it at the source, and you have
improved something that was wrong before this existed.

---

## What it cannot tell you

Worth being clear about:

- **Whether a number is correct.** It checks that a number matches the file it
  came from. If the file is wrong, the report will be confidently wrong.
- **Whether your record-keeping is good.** It will show you where it is not.
- **Anything about rules your funders place on you.** If a grant agreement has
  conditions about how data is handled, someone qualified needs to read it.

---

## Who to keep responsible

Before you rely on this, one named person should own it — not a job title, a
person. If that person leaves and nobody takes over, switch it off rather than
let it run unattended.

Their name should be in `AGENTS.md` in this folder. If it says `(unnamed)`,
that is the first thing to fix.
