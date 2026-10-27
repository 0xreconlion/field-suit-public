# MCP catalog — reviewed, none enabled by default

**Nothing in this directory is active.** `.mcp.json` ships with an empty
server list. Enabling a server is an operator decision that requires **two
visible edits**, not one convenient default:

1. add the server to `.mcp.json`, and
2. add its host to the engagement's `containment.json` egress allowlist.

That is deliberate. Every MCP server is a new authorization surface and a new
supply-chain dependency — the two risks this kit spends most of its design
budget on. A connector that appears by default is one nobody decided to add.

> **Verified 2026-09-29** against the official `modelcontextprotocol/servers`
> repository. Re-verify before relying on any entry: reference servers get
> archived, and an archived server is not a maintained one.

---

## The baseline position: you probably need none of these

The kit's own adapter reads Markdown from a local directory and has no write
method. For a first engagement that is usually sufficient, and it has a
property no MCP server can match: **there is no capability to misconfigure.**

Add a connector when a real client's sources genuinely live somewhere else —
not because the architecture looks more complete with one.

---

## Reference servers — official, maintained

Seven are currently maintained in the official repository. Only two are a
sensible fit here.

| Server | Fit | Assessment |
|---|---|---|
| **Filesystem** — `npx -y @modelcontextprotocol/server-filesystem` | **Recommended, read-only** | Configurable access controls, scoped to named directories. Closest match to what the built-in adapter already does. Scope it to the source directory and nothing above it |
| **Git** — `uvx mcp-server-git` | **Conditional** | Reasonable if a client's sources are versioned. Read and search only; the kit never needs its write tools |
| **Time** — `uvx mcp-server-time` | Optional | Timezone handling for period boundaries. Low risk, low value — the freshness check already parses dates |
| **Fetch** — `uvx mcp-server-fetch` | **Do not enable** | It is an egress capability. The kit's central injection defence is that the exfiltration destination is unreachable; adding a general-purpose fetch tool hands that back. If a client genuinely needs remote content, allowlist the one specific host and justify it in writing |
| **Memory** — knowledge-graph persistent memory | **Do not enable** | Directly against this design. Sources are canonical; a separate mutable memory becomes a second, unsourced authority and a context-poisoning surface (ASI06). A figure must trace to a source, not to something the system remembered |
| **Everything** | Never in an engagement | Reference/test server only |
| **Sequential Thinking** | Not applicable | Reasoning aid, not a data source |

## Archived — do not treat as official

Several servers people still recommend have been **moved to
`servers-archived`**, including Google Drive, Slack, GitHub, GitLab,
PostgreSQL, SQLite, Sentry, Redis, Puppeteer, Brave Search, and Google Maps.

This matters because Google Drive is the first thing a nonprofit will ask
about — most of their sources are in it. The honest answer:

> The official connector for that is archived and no longer maintained.
> A third-party one may exist and may be fine, but adopting it is a
> supply-chain decision we would review and you would approve, not something
> I would switch on because it was convenient.

Do not present an archived server as an official one. A client who discovers
that later re-reads everything else you told them.

---

## Reviewing a third-party server

Every question answered before it is enabled. An unanswered one is a no.

1. **Who publishes it,** and is the source public and readable?
2. **What tools does it actually expose?** Read the tool list, not the
   README. A server described as read-only that ships a `delete` tool is
   read-only right up until it isn't.
3. **What credentials does it want,** at what scope, and can that scope be
   narrowed?
4. **What hosts does it reach?** Each one goes on the egress allowlist
   explicitly, or it cannot work — and if you cannot enumerate them, that is
   the answer.
5. **Is it pinned to a version,** and who reviews the upgrade?
6. **What breaks if it disappears?** A connector with no fallback is a
   dependency the client inherits at handoff.

Record the answers in the engagement file. "We reviewed it" is not a record.

## If you enable one

- Pin the version. Never float.
- Add only the hosts it needs, one at a time.
- Grant it the narrowest data class that works, and re-run the gate suite
  afterwards — particularly gates 6, 10, 12, and 14.
- Write down who reviews it, and when.

---

## A worked vetting: a local code-graph server

Useful as a template, because it shows what a real review turns up — which is
rarely "malicious" and often "a default nobody chose".

**The server.** A local code-graph MCP server (open source, published binary)
that indexes a codebase into SQLite and answers structural queries. Attractive
for a cost posture: it replaces broad file reads with targeted lookups.

**What the review found, in order:**

1. **No listening socket.** It runs as a stdio subprocess, not a network
   service. Good — nothing to reach from off-box.
2. **An update-check endpoint.** The binary contains a vendor-hosted counter
   URL, sitting in the same code path as the GitHub releases API and the
   platform/archive strings. That is a release-download counter, not a
   per-invocation beacon. Disable-able via an env var.
3. **An index scope of the entire home directory,** set in its config.
4. **`upload_enabled = true` in the config file** — on by default.
5. **No worker token configured**, so the upload path probably cannot
   authenticate.

**The disposition.** Items 1 and 2 are fine and would not block adoption. Item
3 alone is fine. **Items 3 and 4 together are the finding**: a whole-home index
plus a default-on upload flag is a decision nobody made, and item 5 is luck
rather than design — a token appearing later silently changes what the first
four mean.

Set the flag off explicitly, narrow the index root to the directories that need
it, and record both in the engagement file. Not because the tool is hostile —
there is no evidence of that — but because **"probably cannot" is not a
control**, and a default you did not choose is not a decision.

### The general lessons

- **Review the config, not just the code.** The code was unremarkable. The
  finding was two lines of TOML.
- **Combinations are findings even when the parts are not.** Broad scope is
  fine. Default-on upload is fine. Together they are not.
- **Missing credentials are not a control.** They are an accident that has not
  been corrected yet.
- **A binary that ships prompt text is normal and worth noticing.** MCP tool
  descriptions land in the agent's context before any tool runs. Benign here,
  and exactly the channel a hostile server would use — read the tool list.
