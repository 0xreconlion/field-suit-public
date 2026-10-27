#!/usr/bin/env python3
"""Run the gate suite.

Two suites, not two modes:

    python evals/run.py          offline, deterministic, no network, no API key
    python evals/run.py --live   the same cases against a real model

Both must be run and reported separately. An offline pass is not evidence of a
live pass, and an env-gated block that silently skips is a lie by default -- so
this runner refuses to report a live result it did not actually produce, and
prints the suite name on every line of output.

Exit status is 0 only when every case in the selected suite passed.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from field_suit.config import load_json, load_policy  # noqa: E402
from field_suit.types import Approval, ToolCallRequest  # noqa: E402

CASES_DIR = Path(__file__).resolve().parent / "cases"

PASS, FAIL, ERROR = "PASS", "FAIL", "ERROR"

GREEN, RED, YELLOW, DIM, BOLD, RESET = (
    "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[1m", "\033[0m"
)


def _colour(enabled: bool, code: str, text: str) -> str:
    return f"{code}{text}{RESET}" if enabled else text


class CaseFailure(Exception):
    """A case ran to completion and produced the wrong answer."""


def _expect(actual: Any, expected: Any, what: str) -> None:
    if actual != expected:
        raise CaseFailure(f"{what}: expected {expected!r}, got {actual!r}")


# --------------------------------------------------------------------------
# case runners, one per kind
# --------------------------------------------------------------------------

def run_gateway_case(case: Mapping[str, Any], fixture: Path) -> None:
    """A case decided purely by the gateway function."""
    from field_suit.gateway.decide import decide

    policy = load_policy(fixture / "policy.json")
    request = ToolCallRequest(**case["request"])

    approvals: Dict[str, Approval] = {}
    for apv_id, spec in case.get("approvals", {}).items():
        if spec.get("mint"):
            # Exercise the real issuing path rather than hand-building an
            # Approval, so mint and verify are tested against each other.
            from field_suit.approvals.issue import mint
            approvals[apv_id] = mint(
                request, spec["approver"], case.get("now", "2026-09-29T12:00:00Z"),
                ttl_minutes=spec.get("ttl_minutes", 30), approval_id=apv_id)
            continue
        if spec.get("bind_to_request"):
            binding = request.binding_hash()
        elif "bind_to_action" in spec:
            # An approval minted over a *different* action than the one now
            # being attempted. This is the replay case: same approval id,
            # same approver, same validity window, different content.
            from dataclasses import replace
            binding = replace(request, action=spec["bind_to_action"]).binding_hash()
        else:
            binding = spec["binding_hash"]
        approvals[apv_id] = Approval(
            approval_id=apv_id,
            binding_hash=binding,
            approver=spec["approver"],
            issued_at=spec["issued_at"],
            expires_at=spec["expires_at"],
        )

    now = case.get("now", "2026-09-29T12:00:00Z")
    decision = decide(request, policy, now, approvals)

    exp = case["expect"]
    _expect(decision.allowed, exp["allowed"], "decision.allowed")
    _expect(decision.reason, exp["reason"], "decision.reason")
    if "check" in exp:
        _expect(decision.check, exp["check"], "decision.check")

    if exp.get("adapter_has_no_write_method"):
        # Independent of the gateway: the adapter must not expose a write path
        # at all. Two reasons the same action fails, and this one survives a
        # policy misconfiguration.
        from field_suit.adapters import markdown_source
        writers = [
            n for n in dir(markdown_source.MarkdownSourceAdapter)
            if any(w in n.lower() for w in ("write", "save", "put", "delete", "update"))
        ]
        if writers:
            raise CaseFailure(
                f"adapter exposes mutating method(s) {writers!r}; it must have none"
            )


def run_containment_case(case: Mapping[str, Any], fixture: Path) -> None:
    """A case decided by egress or cost control."""
    exp = case["expect"]

    if "egress_attempt" in case:
        from field_suit.containment.egress import check_egress
        containment = load_json(fixture / "containment.json")
        decision = check_egress(case["egress_attempt"]["host"], containment)
        _expect(decision.allowed, exp["allowed"], "egress.allowed")
        _expect(decision.reason, exp["reason"], "egress.reason")
        return

    if "usage" in case:
        from field_suit.containment.cost import check_budget, project_usd
        budget = load_json(fixture / "cost-budget.json")
        decision = check_budget(case["usage"], budget)
        _expect(decision.allowed, exp["allowed"], "budget.allowed")
        _expect(decision.reason, exp["reason"], "budget.reason")
        if "projected_usd_over_ceiling" in exp:
            # Assert the *stated cause*, not just the verdict. A token-ceiling
            # breach and a dollar-ceiling breach share a reason code, so
            # without this the case could pass while the dollar projection was
            # wrong in either direction.
            projected = project_usd(case["usage"], budget.get("pricing_usd_per_mtok") or {})
            over = projected > float(budget["ceiling_usd"])
            _expect(over, exp["projected_usd_over_ceiling"],
                    f"projected ${projected:.4f} vs ceiling ${budget['ceiling_usd']}")
        return

    raise CaseFailure("containment case declares neither egress_attempt nor usage")


def run_workflow_case(case: Mapping[str, Any], fixture: Path) -> None:
    """A case that runs the drafting skill end to end."""
    from field_suit.skills.draft_impact_report import run as draft_run

    result = draft_run(case.get("scenario", {}), str(fixture), model=None)
    exp = case["expect"]

    if "outcome" in exp:
        _expect(result.outcome, exp["outcome"], "result.outcome")
    if "halt_reason" in exp:
        _expect(result.halt_reason, exp["halt_reason"], "result.halt_reason")
    if exp.get("report", "unset") is None:
        if result.report is not None:
            raise CaseFailure(
                "a halted run produced a report; a partial board report that "
                "silently dropped a metric is worse than none, because it "
                "looks finished"
            )
    if "missing_sources" in exp:
        _expect(sorted(result.missing_sources), sorted(exp["missing_sources"]),
                "result.missing_sources")
    if "conflict_metric" in exp:
        _expect(result.conflict_metric, exp["conflict_metric"], "result.conflict_metric")
    if "conflict_values" in exp:
        _expect(sorted(result.conflict_values), sorted(exp["conflict_values"]),
                "result.conflict_values")
    if "uncited_claims" in exp:
        got = [{"value": str(c.get("value"))} for c in result.uncited_claims]
        _expect(got, exp["uncited_claims"], "result.uncited_claims")
    if "flags" in exp:
        got_flags = sorted((f["type"], f.get("source_id")) for f in result.flags)
        want_flags = sorted((f["type"], f.get("source_id")) for f in exp["flags"])
        _expect(got_flags, want_flags, "result.flags")

    # gate 5: the two-part assertion
    if exp.get("report_must_contain"):
        if not result.report:
            raise CaseFailure(
                "no report was produced, so report_must_contain could not be "
                "checked. A case asserting what a report contains must not be "
                "satisfiable by producing no report"
            )
        for needle in exp["report_must_contain"]:
            if needle.lower() not in result.report.lower():
                raise CaseFailure(
                    f"report is missing {needle!r}: quarantining an injected "
                    f"instruction must not discard the source's legitimate data"
                )
    for needle in exp.get("report_must_not_contain", []):
        if result.report and needle.lower() in result.report.lower():
            raise CaseFailure(
                f"report contains {needle!r}, which came from the injected "
                f"instruction rather than from any source"
            )
    if "incident_logged" in exp:
        want = exp["incident_logged"]
        if not any(
            i.get("type") == want["type"] and i.get("source_id") == want["source_id"]
            for i in result.incidents
        ):
            raise CaseFailure(f"no incident logged matching {want!r}")
    if "egress_attempt" in exp:
        want = exp["egress_attempt"]
        match = [a for a in result.egress_attempts if a.get("host") == want["host"]]
        if not match:
            raise CaseFailure(
                f"expected an egress attempt to {want['host']!r} to have been "
                f"made and refused; none was recorded. The injected payload "
                f"must actually be exercised, not assumed unreachable"
            )
        _expect(match[0].get("allowed"), want["allowed"], "egress_attempt.allowed")
        _expect(match[0].get("reason"), want["reason"], "egress_attempt.reason")


def run_screen_case(case: Mapping[str, Any], fixture: Path) -> None:
    """A case decided by the pre-access screen, before anything is written."""
    from field_suit.configure.screen import run_screen

    result = run_screen(case["answers"])
    exp = case["expect"]
    _expect(result.passed, exp["passed"], "screen.passed")

    for needle in exp.get("refusal_contains", []):
        if not any(needle.lower() in r.lower() for r in result.refusals):
            raise CaseFailure(
                f"no refusal mentioned {needle!r}; refusals were {result.refusals!r}"
            )
    for needle in exp.get("unanswered_contains", []):
        if not any(needle.lower() in u.lower() for u in result.unanswered):
            raise CaseFailure(
                f"{needle!r} was not reported as unanswered. Silence must "
                f"refuse, never pass"
            )
    if "missing_precondition_count" in exp:
        _expect(len(result.missing_preconditions), exp["missing_precondition_count"],
                "screen.missing_preconditions count")



def run_contract_case(case: Mapping[str, Any], fixture: Path) -> None:
    """A case asserting that two surfaces still agree about the same list.

    The setup form and the pre-access screen ask the same questions. If a
    category is added to the screen and not to the form, the form silently
    stops asking it -- and a half-filled answers file then looks complete to
    the operator who filled it in. A writer and its reader are one unit; this
    is the test that fails when only one of them moves.
    """
    import re
    from field_suit.configure import screen as scr

    html = (REPO / case["html"]).read_text(encoding="utf-8")

    def js_keys(block: str) -> List[str]:
        m = re.search(r"const %s = \[(.*?)\n\];" % block, html, re.S)
        if not m:
            raise CaseFailure(f"could not find `const {block}` in {case['html']}")
        return re.findall(r'\["([a-z_]+)"', m.group(1))

    for block, attr in case["lists"].items():
        page = set(js_keys(block))
        py = set(getattr(scr, attr))
        missing, extra = py - page, page - py
        if missing:
            raise CaseFailure(
                f"{block}: the screen checks {sorted(missing)} but the form never "
                f"asks. A question the form omits is one the operator never "
                f"answers, and an unanswered question is a refusal they will not "
                f"understand"
            )
        if extra:
            raise CaseFailure(
                f"{block}: the form asks {sorted(extra)} but the screen ignores "
                f"it. The operator is being asked for something that changes "
                f"nothing"
            )


#: Directories `new-engagement.sh` vendors into a client package. A case that
#: reads anything outside these cannot run there.
VENDORED_PREFIXES = ("src/field_suit", "evals/", "fixtures/synthetic")


def run_packaging_case(case: Mapping[str, Any], fixture: Path) -> None:
    """Every case reading a non-vendored path must be marked operator-scoped.

    Found the hard way: gate 21 reads the operator's intake form, which is
    deliberately not shipped to a client, but the packager copied every case
    wholesale. So every package reported an ERR the client could never clear,
    about a file they do not have. ERR is never an acceptable resting state,
    least of all in the artifact you hand over.

    This asserts the two halves agree: a case needing operator-only files is
    labelled, and the packager's filter keys off that label.
    """
    packager = (REPO / "scripts/new-engagement.sh").read_text(encoding="utf-8")
    if "'scope')=='operator'" not in packager.replace(" ", ""):
        raise CaseFailure(
            "new-engagement.sh no longer filters on scope=='operator'; an "
            "operator-only gate would ship to a client and ERR there"
        )

    offenders = []
    for path in sorted(CASES_DIR.glob("*.json")):
        spec = json.loads(path.read_text(encoding="utf-8"))
        outside = [
            v for k, v in spec.items()
            if k in ("html", "script", "source") and isinstance(v, str)
            and not any(v.startswith(p) for p in VENDORED_PREFIXES)
        ]
        if outside and spec.get("scope") != "operator":
            offenders.append(f"{spec['id']} reads {outside} but is not scope=operator")
    if offenders:
        raise CaseFailure("; ".join(offenders))


RUNNERS = {
    "gateway": run_gateway_case,
    "containment": run_containment_case,
    "workflow": run_workflow_case,
    "screen": run_screen_case,
    "contract": run_contract_case,
    "packaging": run_packaging_case,
}


# --------------------------------------------------------------------------

def load_cases(selected: Optional[List[str]]) -> List[Dict[str, Any]]:
    cases = []
    for path in sorted(CASES_DIR.glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        case["_path"] = str(path)
        cases.append(case)
    if selected:
        wanted = {s.upper() for s in selected}
        cases = [c for c in cases if any(c["id"].upper().startswith(w) for w in wanted)]
        if not cases:
            raise SystemExit(f"no cases matched {selected!r}")
    return sorted(cases, key=lambda c: c["gate"])


def describe_expectation(case: Mapping[str, Any]) -> str:
    """One line stating what this case will assert once it can run.

    A red suite has to be readable on its own. Without this, every unbuilt
    case reports the same "not implemented yet" text and the output says
    nothing about coverage -- you would be reading four messages and calling
    it thirteen gates.
    """
    exp = case["expect"]
    if case["kind"] == "gateway":
        bits = [f"reason={exp['reason']}"]
        if "check" in exp:
            bits.append(f"at check {exp['check']}")
        if exp.get("adapter_has_no_write_method"):
            bits.append("and adapter exposes no write method")
        return "will assert: " + ", ".join(bits)
    if case["kind"] == "containment":
        return f"will assert: reason={exp['reason']}"
    if case["kind"] == "contract":
        return "will assert: form and screen ask the same questions"
    bits = []
    if "outcome" in exp:
        bits.append(f"outcome={exp['outcome']}")
    if exp.get("halt_reason"):
        bits.append(f"halt_reason={exp['halt_reason']}")
    for key in ("missing_sources", "conflict_metric", "uncited_claims"):
        if exp.get(key):
            bits.append(f"{key}={exp[key]!r}")
    if exp.get("flags"):
        bits.append("flags=" + ",".join(f["type"] for f in exp["flags"]))
    if exp.get("egress_attempt"):
        bits.append(f"egress {exp['egress_attempt']['host']} refused")
    if exp.get("report_must_not_contain"):
        bits.append("report excludes injected values")
    return "will assert: " + ", ".join(bits)


def run_case(case: Mapping[str, Any]) -> Tuple[str, str]:
    fixture = REPO / case["fixture"]
    runner = RUNNERS.get(case["kind"])
    if runner is None:
        return ERROR, f"unknown case kind {case['kind']!r}"
    try:
        runner(case, fixture)
        return PASS, ""
    except NotImplementedError as exc:
        # Unbuilt, not wrong. Report the blocker and this case's own
        # assertion, so the red line is specific to the gate.
        return FAIL, f"{str(exc).strip()}\n{describe_expectation(case)}"
    except CaseFailure as exc:
        return FAIL, str(exc)
    except Exception:
        return ERROR, traceback.format_exc(limit=3).strip().splitlines()[-1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", action="store_true",
                    help="run against a real model (separate suite, separate report)")
    ap.add_argument("--case", action="append",
                    help="run only matching case ids, e.g. --case G06")
    ap.add_argument("--no-colour", action="store_true")
    args = ap.parse_args()

    colour = sys.stdout.isatty() and not args.no_colour
    suite = "LIVE" if args.live else "OFFLINE"

    if args.live:
        print(_colour(colour, YELLOW,
                      "LIVE suite requested. Not implemented yet (milestone M4): "
                      "it needs a real model callable and a reachable, allowlisted "
                      "endpoint. Refusing to report a live result that was not "
                      "actually produced."))
        return 2

    cases = load_cases(args.case)
    print(f"{_colour(colour, BOLD, 'field-suit gate suite')}  "
          f"suite={suite}  cases={len(cases)}  "
          f"{_colour(colour, DIM, 'network=none  api_key=none')}\n")

    results = []
    for case in cases:
        status, detail = run_case(case)
        results.append((case, status, detail))
        tag = {PASS: (GREEN, "PASS"), FAIL: (RED, "FAIL"), ERROR: (YELLOW, "ERR ")}[status]
        print(f"  [{_colour(colour, tag[0], tag[1])}] "
              f"{_colour(colour, BOLD, case['id']):<50} gate {case['gate']:>2}  "
              f"{case['title']}")
        if detail:
            for line in detail.splitlines():
                print(f"         {_colour(colour, DIM, line)}")

    npass = sum(1 for _, s, _ in results if s == PASS)
    nfail = sum(1 for _, s, _ in results if s == FAIL)
    nerr = sum(1 for _, s, _ in results if s == ERROR)

    print()
    summary = f"{npass}/{len(results)} passed"
    if nfail:
        summary += f", {nfail} failed"
    if nerr:
        summary += f", {nerr} errored"
    print(f"  {_colour(colour, BOLD, summary)}  [suite={suite}]")

    if nerr:
        print(_colour(colour, YELLOW,
                      "  ERR means a case could not be evaluated at all. That is "
                      "distinct from FAIL and is never an acceptable resting state."))
    return 0 if (nfail == 0 and nerr == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
