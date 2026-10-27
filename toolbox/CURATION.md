# Curation — how a tool gets onto the shelf

A tool is **curated, never copied.** An internal tool carries bindings to the
environment it grew in: paths, hostnames, product names, people, and — most
dangerously — references to incidents that explain *why* a rule exists. The
rule is portable. The incident is not.

This file is the repeatable procedure. `scripts/check-debrand.sh` is its
automated backstop, and it runs **before** the first tool lands, not after.
A de-brand gate written after the shelf already exists has already let
something through once.

---

## The two guards point in opposite directions

Neither substitutes for the other, and it is easy to build one and believe you
have both:

| Guard | Direction | Failure it prevents |
|---|---|---|
| `check-client-data.sh` | client data must never flow **into** the kit | One engagement's figures reaching the reusable kit via a committed fixture or a log |
| `check-debrand.sh` | operator internals must never flow **out** through the toolbox | Our paths, products, people and incident history reaching a client surface |

---

## Readiness classes

Measure before deciding. Coupling is counted as occurrences of internal terms
against file length, and it is a **proxy for curation effort, not a measure of
portability** — a low count can still hide one fatal internal reference, and a
high count can be one repeated path.

| Class | Meaning | Action |
|---|---|---|
| **Port** | Low coupling, generic by design | De-brand, parameterise, ship |
| **Rewrite** | Right concept, wrong bindings throughout | Keep the pattern, write the tool fresh |
| **Do not ship** | Describes specific infrastructure, not a method | Stays internal. No amount of find-and-replace fixes this |

A tool in the **Rewrite** class is not a harder port. It is a different piece of
work, and treating it as a port is how internal detail survives into a client
document — the obvious terms get replaced and the reasoning around them stays.

---

## The checklist

Every item, every tool. No exceptions for "it's obviously fine".

1. **No product, organisation, or persona names.** Tools address *the
   operator*, never a person by name.
2. **No absolute paths, hostnames, service names, or unit names.**
3. **No incident references, leak counts, or failure histories.** The *lesson*
   survives; the *war story* does not. "A guard placed after the writes it
   protects is not a guard" is portable. "This happened to us in March and cost
   two days" is not, and it also tells a client something about our operational
   maturity that is none of their business.
4. **No internal voice.** Toolbox prose is plain and instructional. Personality
   belongs to the operator, not to the shipped artifact.
5. **Every removed binding becomes a declared field.** Add it to
   `operator_configures:` in the skill frontmatter rather than deleting it
   silently. A stripped tool must announce what it still needs, or the first
   person to use it will run it half-configured and get a confident wrong
   answer.
6. **Re-read the tool as a client would.** The question is not "is this
   accurate" but "does this tell them anything about us that they did not buy".

---

## Packaging

Each tool ships as an Agent Skill: `SKILL.md` with frontmatter and a body.

This is a token decision as much as a format one. Only the name and description
load at discovery; the body loads when the tool is actually relevant. An
operator can be aware of the whole shelf for less context than one activated
tool costs, which is what lets the shelf grow without making every session more
expensive. A tool whose body is only ever half-read is a tool that should have
been two tools.

Keep the `description` to one line and make it say *when to use this*, not just
what it is. Selection happens off that line alone.

---

## What the shelf is for

Three shelves, and the distinction is load-bearing:

- **posture/** — what the *operator declares*. A scope restriction on a
  session.
- **gates/** — report-only checks run at a decision point. They recommend;
  they never act.
- **flows/** — ordered multi-step procedures with recorded outcomes.

**Posture and tier are different axes and an engagement needs both.** A tier is
what the gateway *enforces*; a posture is what the operator *declares*. A
posture with nothing enforcing it is a promise. A gateway with no declared
posture gives the operator no way to narrow scope part-way through an
engagement without editing policy.

---

## Adopting a tool from outside

Everything above is for tools *you* wrote. Pulling from a community
aggregator — awesome-claude-code-subagents, a skills repository, an MCP list —
is a different risk class and deserves saying plainly:

**An agent or skill markdown file is not data. It is instructions that execute
with the adopting agent's full tool access.** No install step, no binary, no
sandbox. The prose is the payload. Copying one into `agents/` is closer to
running a shell script as yourself than to adding a library, and a star count
says nothing about it.

`scripts/screen-import.py` triages a candidate set:

```
python3 scripts/screen-import.py --dir ~/Downloads/some-subagent-pack
```

### What it is for, and what it is not

**For:** files you adopt *individually* from an untrusted aggregator. Measured
against a realistic pack, it isolated a file that read `~/.ssh/id_ed25519` and
`$GITHUB_TOKEN`, POSTed them to an external host, and instructed the agent not
to mention it — while passing two legitimate agents, including one holding
`Write` and `Bash`.

**Not for:** auditing a first-party vendor bundle. Screening one flagged 320 of
464 files, almost all `NET-HOST` and `REMOTE-EXEC` on legitimate API examples
in reference docs. At that rate the output is noise, and noise is what trains
you to skim past the one that mattered.

The reason is not a tuning failure. **For a vendor bundle the unit of trust is
the publisher, not the file.** Nobody reads 464 files, and a screener implying
you did is worse than one that admits it did not look. Decide the publisher;
screen the individual adoptions.

### CLEAN is not an endorsement

It means no pattern on the list appeared — a statement about the list. A
competent hostile file will not match a published pattern. Treat CLEAN as "read
it normally" and FLAGGED as "read it adversarially". The tool decides where to
look first; it never decides what is safe.

### Before enabling an MCP server

Different questions, in `mcp/CATALOG.md`. The one people miss: a server's
**tool descriptions** land in the agent's context before any tool runs, so a
hostile description is a skill-class injection arriving in a code-class
wrapper. Read the tool list, not the README.
