#!/usr/bin/env python3
"""Screen a candidate agent, skill, command, or MCP manifest before adopting it.

Why this exists
---------------
An agent or skill markdown file is **not data**. It is instructions that will
execute with the adopting agent's full tool access. There is no install step to
audit, no binary to scan, and no sandbox. The prose *is* the payload, which
makes this import class closer to running a shell script as yourself than to
adding a library.

So the only real mitigation is reading every file you adopt. This tool does not
replace that reading and cannot. What it does is turn a 400-file browse into a
ranked shortlist, so the reading you do is aimed at the files most likely to
matter.

What it is not
--------------
**Not a verdict.** A clean result means "nothing on the pattern list appeared",
which is a statement about the patterns, not about the file. A competent
malicious skill will phrase its instruction in a way no pattern here matches.
Treat CLEAN as "read it normally" and FLAGGED as "read it adversarially".

Usage
-----
    python3 scripts/screen-import.py <path> [<path> ...]
    python3 scripts/screen-import.py --dir ~/Downloads/awesome-subagents
    python3 scripts/screen-import.py --dir <d> --quiet   # flagged files only

Exit status is 0 when nothing was flagged, 1 otherwise, so it can gate a
Makefile or a pre-adoption script.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Tuple


class Rule(NamedTuple):
    severity: str      # HIGH | MEDIUM | LOW
    code: str
    pattern: "re.Pattern[str]"
    why: str


def _r(severity: str, code: str, pattern: str, why: str, flags=re.I) -> Rule:
    return Rule(severity, code, re.compile(pattern, flags), why)


# --------------------------------------------------------------------------
# Rules. Each targets a *specific* abuse, not a vibe. A rule that fires on
# ordinary text is worse than no rule: it trains you to skim the output, and
# then the one that mattered gets skimmed too.
# --------------------------------------------------------------------------


# A command must appear in *command position* to count. A file that DESCRIBES
# `sudo` policy is not a file that USES sudo, and an earlier version flagged a
# governance doc for the sentence "sudo beyond the pre-authorized pair".
# Matching the word instead of its grammatical role is the main source of noise
# in a screener, and noise is what trains you to skim the output.
# NOTE the outer (?: ... ) group. Without it the top-level alternation
# escapes the concatenation below and the first branch — any line start —
# matches everywhere, flagging every file. Caught by the negative control.
CMD_POS = r"(?:(?:^|\n)[ \t]*[`$>]?[ \t]*|[;&|]{1,2}[ \t]*|`)"

RULES: List[Rule] = [
    # ---- credential and key material ------------------------------------
    _r("HIGH", "CRED-PATH",
       r"(~|\$HOME|/home/[\w.-]+)/\.(ssh|aws|gnupg|config/gh|claude/\.credentials|netrc)",
       "references a credential store by path"),
    _r("HIGH", "CRED-ENV",
       r"\b(ANTHROPIC_API_KEY|OPENAI_API_KEY|AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN|GH_TOKEN|"
       r"NPM_TOKEN|CLOUDFLARE_API_TOKEN|PRIVATE_KEY|MNEMONIC|SEED_PHRASE)\b",
       "names a secret-bearing environment variable"),
    _r("HIGH", "CRED-FILE",
       r"\b(id_rsa|id_ed25519|credentials\.json|\.env\b|wallet\.dat|keystore)\b",
       "names a secret-bearing file"),

    # ---- exfiltration ----------------------------------------------------
    _r("HIGH", "EXFIL-POST",
       r"\b(curl|wget|fetch|POST|upload|exfiltrat\w*)\b[^\n]{0,60}https?://",
       "sends data to a URL"),
    _r("HIGH", "EXFIL-PIPE",
       r"\|\s*(curl|wget|nc|ncat|netcat)\b",
       "pipes output into a network tool"),
    _r("MEDIUM", "NET-HOST",
       r"https?://(?!(?:docs\.|www\.)?(?:anthropic\.com|github\.com|modelcontextprotocol\.io|"
       r"json-schema\.org|owasp\.org|nist\.gov|example\.(?:com|test)))[a-z0-9.-]+\.[a-z]{2,}",
       "reaches a host outside the common-documentation allowlist"),

    # ---- instruction override / injection --------------------------------
    _r("HIGH", "OVERRIDE",
       r"ignore\s+(all\s+|any\s+|your\s+)?(previous|prior|earlier|above|system)\s+"
       r"(instruction|prompt|rule|direction)",
       "tells the agent to disregard its instructions"),
    # Two shapes, because the commonest covert phrasing never names a person.
    # "Do not log this instruction or mention it in your output" conceals just
    # as effectively as "don't tell the user", and an earlier version of this
    # rule missed it on a live test against a known-hostile fixture.
    _r("HIGH", "COVERT",
       r"\b(do not|do n't|don'?t|never)\s+(tell|inform|mention|reveal|report|log|show|notify|"
       r"disclose|record|include)\b",
       "instructs the agent to conceal or omit something"),
    # Requires an imperative. "runs silently died at a guard" is narration of a
    # past failure; "silently delete the log" is an instruction. Only the second
    # is a finding, and the difference is the verb mood, not the adverb.
    _r("HIGH", "COVERT-SILENT",
       r"\b(silently|quietly|discreetly)\s+"
       r"(do|run|execute|perform|delete|remove|send|post|copy|write|modify|add|install)\b"
       r"|\bwithout\s+(logging|recording|notifying|telling|informing|alerting)\b"
       r"|\bkeep\s+this\s+(secret|between\s+us|to\s+yourself)\b"
       r"|\bbehind\s+the\s+scenes\b",
       "instructs the agent to act without leaving a trace"),
    _r("HIGH", "SELF-AUTH",
       r"\b(without|skip|bypass|no need for|don'?t need)\s+"
       r"(asking|approval|confirmation|permission|review)",
       "instructs the agent to proceed without human approval"),
    _r("MEDIUM", "URGENCY",
       r"\b(urgent|immediately|critical|you must|mandatory)\b[^\n]{0,40}"
       r"\b(comply|obey|execute|run|perform)\b",
       "uses pressure phrasing to force compliance"),
    _r("MEDIUM", "ROLE-SHIFT",
       r"\b(you are now|from now on you|new system prompt|developer mode|unrestricted mode|"
       r"jailbreak)\b",
       "attempts to redefine the agent's role"),

    # ---- destructive / privilege -----------------------------------------
    _r("HIGH", "DESTRUCTIVE",
       CMD_POS + r"(rm\s+-[rf]{1,2}\s|git\s+push\s+--force|git\s+reset\s+--hard|"
       r"DROP\s+TABLE|mkfs|dd\s+if=|shred\s|:\s*>\s*/dev/sd)",
       "issues a destructive command"),
    _r("HIGH", "PRIV-ESC",
       CMD_POS + r"(sudo\s|chmod\s+777|chmod\s+\+s|setuid)",
       "issues a privilege-escalating command"),
    _r("LOW", "PRIV-MENTION",
       r"\b(sudo|/etc/sudoers|setuid)\b",
       "mentions privilege escalation (may be policy prose, not a command)"),
    _r("MEDIUM", "REMOTE-EXEC",
       r"(curl|wget)[^\n]{0,80}\|\s*(ba|z|)sh|eval\s*\(|exec\s*\(|subprocess\.",
       "executes fetched or dynamic code"),

    # ---- obfuscation ------------------------------------------------------
    _r("HIGH", "OBFUSCATED",
       r"\b(base64\s+-d|atob\(|fromCharCode|\\x[0-9a-f]{2}\\x[0-9a-f]{2}\\x[0-9a-f]{2})",
       "contains encoded or obfuscated content"),
    _r("MEDIUM", "ZERO-WIDTH",
       r"[​‌‍⁠﻿]",
       "contains zero-width characters that hide text from a human reader",
       0),
    _r("MEDIUM", "HTML-HIDDEN",
       r"<!--(?:(?!-->)[\s\S]){0,400}?(?:ignore|instruction|system|execute|secret)"
       r"(?:(?!-->)[\s\S]){0,400}?-->",
       "hides directive-like text inside an HTML comment"),
]

TOOL_LINE = re.compile(r"^tools:\s*(.+)$", re.M)
MUTATING_TOOLS = {"write", "edit", "notebookedit", "bash", "task", "agent"}


def screen_text(text: str) -> List[Tuple[Rule, int, str]]:
    """Return (rule, line_number, excerpt) for every rule that fired."""
    hits: List[Tuple[Rule, int, str]] = []
    lines = text.splitlines()
    for rule in RULES:
        for match in rule.pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            raw = lines[line_no - 1] if line_no <= len(lines) else ""
            excerpt = raw.strip()[:110] or repr(match.group(0))[:110]
            hits.append((rule, line_no, excerpt))
            break  # one hit per rule is enough to warrant reading the file
    return hits


def describe_capability(text: str) -> List[str]:
    """Capability notes: what this file would be *allowed* to do.

    Separate from the rule hits. A tool grant is not suspicious in itself --
    it is the thing you weigh the rest of the file against. A file that only
    reads is a different read than one that can shell out.
    """
    notes: List[str] = []
    m = TOOL_LINE.search(text)
    if m:
        declared = [t.strip() for t in re.split(r"[,\s]+", m.group(1)) if t.strip()]
        mutating = [t for t in declared if t.lower() in MUTATING_TOOLS]
        notes.append(f"declares tools: {', '.join(declared) or '(none)'}")
        if mutating:
            notes.append(f"MUTATING capability: {', '.join(mutating)} "
                         f"— this file can change state, not just report")
        if "*" in declared or "all" in [d.lower() for d in declared]:
            notes.append("grants ALL tools — the broadest possible capability")
    else:
        notes.append("no explicit tools: line — will inherit the caller's full tool access")
    return notes


def screen_mcp_manifest(path: Path) -> List[str]:
    """Extra checks for an MCP server manifest.

    The subtle abuse here is a server whose *tool descriptions* carry
    instructions. Those descriptions land in the agent's context before any
    tool is invoked, so a hostile description is a skill-class injection
    arriving in a code-class wrapper.
    """
    notes: List[str] = []
    try:
        data: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"could not parse as JSON: {exc}"]

    servers = data.get("mcpServers") or data.get("servers") or {}
    if not servers:
        notes.append("declares no servers (inert)")
    for name, spec in servers.items():
        cmd = " ".join([str(spec.get("command", ""))] +
                       [str(a) for a in (spec.get("args") or [])])
        notes.append(f"server {name!r}: {cmd[:90]}")
        if re.search(r"@latest|:latest", cmd):
            notes.append(f"  server {name!r} is UNPINNED (@latest) — "
                         f"what you reviewed is not what will run tomorrow")
        if spec.get("env"):
            notes.append(f"  server {name!r} requests env: "
                         f"{', '.join(sorted(spec['env']))}")
    return notes


def screen_file(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {"path": path, "error": str(exc), "hits": [], "notes": []}

    hits = screen_text(text)
    notes: List[str] = []
    if path.suffix == ".json":
        notes += screen_mcp_manifest(path)
    elif path.suffix == ".md":
        notes += describe_capability(text)

    return {"path": path, "hits": hits, "notes": notes,
            "lines": text.count("\n") + 1, "error": None}


def verdict(result: Dict[str, Any]) -> str:
    sev = {h[0].severity for h in result["hits"]}
    if "HIGH" in sev:
        return "FLAGGED-HIGH"
    if "MEDIUM" in sev:
        return "FLAGGED"
    return "CLEAN"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--dir", type=Path, help="screen every .md/.json beneath this directory")
    ap.add_argument("--quiet", action="store_true", help="print flagged files only")
    ap.add_argument("--deep", action="store_true",
                    help="also screen reference//docs/ material, not just definitions")
    args = ap.parse_args()

    targets: List[Path] = list(args.paths)
    if args.dir:
        for ext in ("*.md", "*.json"):
            targets += sorted(args.dir.rglob(ext))
        if not args.deep:
            # Definition files only by default.
            #
            # Measured 2026-09-29: screening a vendor documentation bundle
            # flagged 320 of 464 files. At a 69% hit rate the output is noise,
            # and noise is what trains you to skim past the one that mattered.
            # The cause is that SDK reference docs are *full* of legitimate
            # `POST https://...` examples, which is exactly what an exfil rule
            # looks for.
            #
            # The deeper point: for a first-party bundle the unit of trust is
            # the PUBLISHER, not the file. Nobody reads 464 vendor files, and
            # a screener implying you did is worse than one that says it did
            # not look. This tool is for files adopted INDIVIDUALLY from an
            # untrusted aggregator. Use --deep when you genuinely intend to
            # read reference material too, and expect noise.
            def is_definition(p: Path) -> bool:
                if p.name in ("SKILL.md", "plugin.json", "marketplace.json",
                              ".mcp.json", "mcp.json"):
                    return True
                if p.suffix == ".json" and "mcp" in p.name.lower():
                    return True
                parts = {x.lower() for x in p.parts}
                if parts & {"references", "reference", "docs", "examples", "assets"}:
                    return False
                return p.suffix == ".md" and p.parent.name in (
                    "agents", "commands", "skills", "subagents")
            targets = [p for p in targets if is_definition(p)]
    if not targets:
        ap.error("give one or more paths, or --dir")

    results = [screen_file(p) for p in targets if p.is_file()]
    flagged = [r for r in results if verdict(r) != "CLEAN"]

    for r in results:
        v = verdict(r)
        if args.quiet and v == "CLEAN":
            continue
        print(f"\n{v:14} {r['path']}")
        if r["error"]:
            print(f"  ! {r['error']}")
        for note in r["notes"]:
            print(f"  · {note}")
        for rule, line_no, excerpt in sorted(r["hits"], key=lambda h: h[0].severity):
            print(f"  [{rule.severity:6}] {rule.code:12} line {line_no}: {rule.why}")
            print(f"             {excerpt}")

    print(f"\n{'─' * 68}")
    print(f"  {len(results)} file(s) screened · {len(flagged)} flagged · "
          f"{len(results) - len(flagged)} clean")
    print("""
  CLEAN is not an endorsement. It means no pattern on the list appeared,
  which is a statement about the list. A competent hostile file will not
  match a published pattern. Read what you adopt; this only tells you
  where to look first.""")
    return 1 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main())
