# The toolbox

Working tools an organization picks up and configures, rather than a method it
has to implement. Each one is narrow, report-only unless stated, and declares
what an operator must set before it is useful.

## Install

The repository serves itself as a plugin marketplace:

```
/plugin marketplace add <this-repo>
/plugin install field-suit-toolbox@field-suit
```

Namespaced, so it cannot collide with tools the organization already has.
Versioned, so an engagement can pin a known-good shelf and upgrade
deliberately.

## Not tied to one runtime

Each tool is an Agent Skill — a `SKILL.md` with frontmatter and a body. The
body is the tool. It is written as instructions a competent person could
follow, so a team with no agent runtime at all can still run it by hand, and a
team on a different runtime can port it by moving one file.

The engagement configuration also generates an `AGENTS.md`, which is read by
most current agent runtimes. **No specific AI host is required to adopt this
kit**, which matters because a client's environment may prohibit the one you
would have chosen.

## Why skills and not one big instruction file

Only a tool's name and one-line description are loaded until the tool is
actually relevant; the body loads on use. The practical effect is that the
shelf can grow without making every session more expensive — being *aware of*
the whole toolbox costs less context than *using* one tool from it.

This is why a tool whose body is only ever half-relevant should be split in
two. Bundling unrelated guidance into one skill forfeits the entire benefit.

## What is on the shelf

### `skills/posture/` — what the operator declares

Scope restrictions set on a working session. These load into the main context
because constraining that session is their whole job.

| Tool | Use when |
|---|---|
| `read-only` | The boundary is not drawn yet and an accidental write costs more than a slow answer |
| `status` | You want the current picture and explicitly not the next action |
| `hold` | Work must stop at a clean point and be resumable by someone else |
| `source-of-truth` | Two documents both look authoritative and it is time to decide |

### `skills/workflow/` — how to build what the kit depends on

| Tool | Use when |
|---|---|
| `source-register` | Building or auditing the register every gate decides against |
| `metric-dictionary` | Defining the numbers, exactly once each |

### `agents/` — report-only reviewers

Separate context, restricted tools. **None of them declares a write tool**,
and the de-brand check enforces that by reading the frontmatter rather than
trusting the prose.

| Tool | Use when |
|---|---|
| `citation-audit` | Before a report or funder submission is treated as authoritative |
| `verification-gate` | Before a handoff, commit, or deploy |
| `approval-triage` | One pending action is genuinely ambiguous and a second isolated read would sharpen the ask |
| `incident-evidence` | An AI system produced a wrong, harmful, or unauthorized result |
| `incident-reviewer` | An evidence packet exists and needs an independent challenge |

Why agents and not skills: isolation is the value. A reviewer who has already
read the argument for doing something is a poor judge of whether it should be
done, and a restricted tool list makes "report-only" a property of the runtime
rather than a promise in a paragraph.

### `commands/` — thin entry points

`screen`, `gates`, `review-failures`. They run a script and report. They do
not decide, and none of them promotes, approves, or configures anything.

### `.mcp.json` — intentionally empty

Every MCP server is a new authorization surface and a new supply-chain
dependency. Enabling one takes **two** visible edits: an entry here, and its
host on the engagement's egress allowlist. See `mcp/CATALOG.md`, which also
records which commonly-recommended servers are **archived** rather than
official.

## Posture and authority tier are different things

A **tier** is what the gateway enforces — the system will refuse. A **posture**
is what the operator declares — the session will not attempt.

Both are needed. A posture with nothing enforcing it is a promise. A gateway
with no declared posture leaves an operator unable to narrow scope part-way
through an engagement without editing policy, which they will therefore not do.

## Adding a tool

Read `CURATION.md` first. Tools are curated, never copied, and
`scripts/check-debrand.sh` must pass before anything lands.
