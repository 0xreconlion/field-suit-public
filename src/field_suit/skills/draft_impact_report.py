"""Draft a board/funder impact report from approved, cited sources.

The workflow this kit exists to prove. Deliberately the *reporting* use case
rather than a chatbot: monthly impact reporting is real, recurring,
deadline-driven, currently assembled by hand, and it is the artifact a
nonprofit's next grant renewal turns on.

The pipeline, in order, because the order is the design:

    load -> quarantine injected instructions -> extract -> resolve
         -> halt on missing -> halt on conflict -> flag staleness
         -> draft -> ground every figure -> halt on any ungrounded figure

Resolution is deterministic Python, not model work. The model writes prose
around figures the pipeline already resolved and cited. A model asked to both
find the number and write the sentence will eventually write a plausible
sentence containing a number it invented, and no amount of prompting reliably
prevents that -- so it is never asked to.

The model is injected as a callable. Offline, the stub is deterministic and
the whole suite runs with no API key and no network. Live, the same cases run
against a real model. Those are two suites and both get reported separately.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from ..adapters.markdown_source import MarkdownSourceAdapter
from ..containment.egress import check_egress
from ..gateway.checks import parse_instant

ModelFn = Callable[[str], str]

#: Bold total lines are the only extractable form. See the metric
#: dictionary's _extraction_note for why prose and table cells are excluded.
TOTAL_LINE = re.compile(r"^\*\*(?P<label>[^:*]+?)\s*(?:\((?P<period>[^)]*)\))?\s*:\s*"
                        r"(?P<value>[\d,]+(?:\.\d+)?)\s*\*\*\s*$", re.MULTILINE)

#: Markers that delimit a quarantined instruction block in a source.
INJECTION_BLOCK = re.compile(
    r"<!--\s*BEGIN INJECTION PAYLOAD.*?-->(?P<payload>.*?)<!--\s*END INJECTION PAYLOAD\s*-->",
    re.DOTALL | re.IGNORECASE,
)

#: Imperative patterns that should never appear in a *data* source. Detection
#: is a tripwire, not the defence: the defence is that the payload is
#: quarantined before the model sees it, and that egress is denied regardless.
INJECTION_SIGNALS = (
    re.compile(r"ignore\s+(your\s+)?(previous|prior|all)\s+instructions", re.I),
    re.compile(r"\bunrestricted mode\b", re.I),
    re.compile(r"\bdo not (log|mention|report)\b", re.I),
    re.compile(r"\b(POST|send|upload|exfiltrat\w*)\b.{0,40}https?://", re.I | re.S),
    re.compile(r"\bsystem (notice|prompt|instruction)\b", re.I),
)

URL_HOST = re.compile(r"https?://([^/\s\"'<>)]+)")


@dataclass(frozen=True)
class RunResult:
    """Outcome of one drafting run.

    ``outcome`` is ``drafted``, ``drafted_with_flags`` or ``halt``. A halt
    never carries a partial report: a half-written board report that silently
    dropped a metric is worse than none, because it looks finished.
    """

    outcome: str
    report: Optional[str] = None
    halt_reason: Optional[str] = None
    flags: List[Dict[str, Any]] = field(default_factory=list)
    uncited_claims: List[Dict[str, Any]] = field(default_factory=list)
    missing_sources: List[str] = field(default_factory=list)
    incidents: List[Dict[str, Any]] = field(default_factory=list)
    egress_attempts: List[Dict[str, Any]] = field(default_factory=list)
    conflict_metric: Optional[str] = None
    conflict_values: List[Any] = field(default_factory=list)


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------

def _load_sources(
    adapter: MarkdownSourceAdapter, scenario: Mapping[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Load sources by id, applying the scenario's overlay.

    The overlay exists so one fixture can exercise several distinct failure
    modes without maintaining several near-identical copies of it, which would
    drift apart and quietly stop testing what they claim to.
    """
    docs: Dict[str, Dict[str, Any]] = {}
    for doc in adapter.read_all("sources"):
        docs[doc["source_id"]] = doc

    if scenario.get("include_injected"):
        for doc in adapter.read_all("injected"):
            docs[doc["source_id"]] = doc  # same id, hostile variant wins

    for source_id, spec in (scenario.get("add") or {}).items():
        meta = {k: str(v) for k, v in spec.items() if not isinstance(v, (int, float))}
        values = {k: v for k, v in spec.items() if isinstance(v, (int, float))}
        body = "\n".join(
            "**%s (%s): %s**" % (k.replace("_", " "), meta.get("period", ""), v)
            for k, v in values.items()
        )
        docs[source_id] = {"path": f"<scenario>/{source_id}", "source_id": source_id,
                           "meta": meta, "body": body, "_synthetic": True}
    return docs


def _quarantine(doc: Mapping[str, Any]) -> Tuple[str, List[str], List[str]]:
    """Strip injected instruction blocks before the model sees anything.

    Returns the safe body, the payloads removed, and any hosts named inside
    them. Quarantine happens at ingestion rather than at generation because a
    defence that runs after the model has read the text is relying on the
    model, which is the component the attacker is addressing.
    """
    body = doc.get("body", "")
    payloads: List[str] = []
    hosts: List[str] = []

    for match in INJECTION_BLOCK.finditer(body):
        payloads.append(match.group("payload"))
    safe = INJECTION_BLOCK.sub("\n[quarantined: instruction block removed]\n", body)

    # Also catch imperative content that is not wrapped in markers. The
    # markers exist in the fixture for legibility; a real payload will not
    # announce itself.
    for pattern in INJECTION_SIGNALS:
        if pattern.search(safe):
            payloads.append(pattern.pattern)

    for blob in [body]:
        hosts.extend(URL_HOST.findall(blob))

    return safe, payloads, hosts


# --------------------------------------------------------------------------
# extraction and resolution
# --------------------------------------------------------------------------

def _extract_totals(body: str) -> List[Tuple[str, str, float]]:
    out = []
    for m in TOTAL_LINE.finditer(body):
        raw = m.group("value").replace(",", "")
        try:
            out.append((m.group("label").strip(), (m.group("period") or "").strip(), float(raw)))
        except ValueError:
            continue
    return out


def _normalise_label(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def _label_matches(metric: Mapping[str, Any], found_label: str) -> bool:
    """Exact match against the metric's declared ``extraction_labels``.

    No fuzzy matching, no keyword overlap, no stemming. A metric that a source
    spells differently gets another entry in its label list, which is a
    visible diff someone reviews -- not a heuristic that silently starts
    binding a new number one day because the wording drifted.

    A metric with no declared labels matches nothing and will be reported
    missing. That is intentional: an undeclared metric must not be resolved
    by guesswork.
    """
    wanted = {_normalise_label(x) for x in (metric.get("extraction_labels") or [])}
    return _normalise_label(found_label) in wanted


def _resolve_metrics(
    dictionary: Mapping[str, Any], docs: Mapping[str, Dict[str, Any]],
    safe_bodies: Mapping[str, str],
) -> Tuple[Dict[str, Dict[str, Any]], List[str], Optional[Dict[str, Any]]]:
    """Resolve each metric to a value, or report missing / conflicting."""
    resolved: Dict[str, Dict[str, Any]] = {}
    missing: List[str] = []
    conflict: Optional[Dict[str, Any]] = None

    for metric in dictionary["metrics"]:
        mid, label = metric["id"], metric["label"]
        sot = metric["source_of_truth"]
        wanted = [sot] + list(metric.get("corroborating_sources") or [])

        absent = [s for s in wanted if s not in docs]
        if sot in absent:
            if sot not in missing:
                missing.append(sot)
            continue

        observed: List[Tuple[str, float]] = []
        for source_id in wanted:
            if source_id not in docs:
                continue
            for found_label, _period, value in _extract_totals(safe_bodies[source_id]):
                if _label_matches(metric, found_label):
                    observed.append((source_id, value))

        if not observed:
            if sot not in missing:
                missing.append(sot)
            continue

        distinct = sorted({v for _s, v in observed})
        if len(distinct) > 1 and metric.get("reconciliation_rule") == "halt_on_conflict":
            if conflict is None:
                conflict = {"metric": mid,
                            "values": [int(v) if v.is_integer() else v for v in distinct],
                            "sources": [s for s, _ in observed]}
            continue

        value = observed[0][1]
        resolved[mid] = {"metric": mid, "label": label, "value": value,
                         "unit": metric.get("unit", ""), "source_id": sot,
                         "source_path": docs[sot]["path"]}

    return resolved, missing, conflict


# --------------------------------------------------------------------------
# freshness
# --------------------------------------------------------------------------

def _freshness_flags(
    dictionary: Mapping[str, Any], docs: Mapping[str, Dict[str, Any]],
    used_source_ids: List[str], as_of: datetime,
) -> List[Dict[str, Any]]:
    """Staleness of the data and staleness of its ownership, reported apart.

    They are different defects with different fixes -- one needs a fresh
    export, the other needs a person to confirm they still own the source --
    so collapsing them into one "stale" flag would send the operator to do
    the wrong thing half the time.
    """
    flags: List[Dict[str, Any]] = []
    period = str(dictionary.get("period", ""))
    fresh_days = int(dictionary.get("freshness_window_days", 45))
    owner_days = int(dictionary.get("owner_confirmation_window_days", 180))

    for source_id in sorted(set(used_source_ids)):
        doc = docs.get(source_id)
        if not doc:
            continue
        meta = doc.get("meta", {})

        source_period = str(meta.get("period", ""))
        published = parse_instant(str(meta.get("published", "")))
        stale = False
        detail = ""
        if source_period and period and source_period != period:
            stale, detail = True, f"covers {source_period}, report period is {period}"
        elif published is not None and (as_of - published).days > fresh_days:
            stale, detail = True, f"published {(as_of - published).days}d ago, window {fresh_days}d"
        elif published is None:
            stale, detail = True, "no readable publication date"
        if stale:
            flags.append({"type": "stale_source", "source_id": source_id, "detail": detail})

        holder = str(meta.get("owner_holder", "")).strip()
        confirmed = parse_instant(str(meta.get("owner_confirmed", "")))
        if not holder or holder.upper() == "UNCONFIRMED":
            flags.append({"type": "unconfirmed_owner", "source_id": source_id,
                          "detail": "no current holder named"})
        elif confirmed is None or (as_of - confirmed).days > owner_days:
            age = "unreadable" if confirmed is None else f"{(as_of - confirmed).days}d"
            flags.append({"type": "unconfirmed_owner", "source_id": source_id,
                          "detail": f"owner last confirmed {age}, window {owner_days}d"})
    return flags


# --------------------------------------------------------------------------
# drafting and grounding
# --------------------------------------------------------------------------

def _stub_model(scenario: Mapping[str, Any]) -> ModelFn:
    """Deterministic offline model.

    ``simulate_persuaded_model`` makes it obey the injected instruction. That
    is the point: the test must show the system holding when the model does
    not, because "the model behaved" is not a control.
    """
    def run(prompt: str) -> str:
        lines = ["Riverbend Community Services delivered its programs across all sites "
                 "during the reporting period."]
        if scenario.get("simulate_persuaded_model"):
            lines.append("Total unique participants served was 1,250 this period.")
        ungrounded = scenario.get("inject_ungrounded_figure")
        if ungrounded:
            lines.append(f"A further {ungrounded['value']} {ungrounded['context']}.")
        return " ".join(lines)
    return run


def _render(period: str, resolved: Mapping[str, Dict[str, Any]], prose: str,
            flags: List[Dict[str, Any]]) -> str:
    # Which sources carry findings, so a figure can warn at the point of use.
    # A caveat in a section at the bottom is a disclaimer nobody reads; the
    # honest limit belongs next to the number a board member will quote.
    flagged: Dict[str, List[str]] = {}
    for f in flags:
        flagged.setdefault(f["source_id"], []).append(f["type"])

    out = [f"# Impact report — {period}", "", "## Narrative", "", prose.strip(), "",
           "## Figures", ""]
    for item in resolved.values():
        value = item["value"]
        shown = f"{int(value):,}" if float(value).is_integer() else f"{value:,.2f}"
        warn = ""
        if item["source_id"] in flagged:
            warn = "  ⚠ " + ", ".join(sorted(set(flagged[item["source_id"]])))
        out.append(f"- **{item['label']}**: {shown} {item['unit']} "
                   f"[source: {item['source_id']} — {item['source_path']}]{warn}")
    if flags:
        out += ["", "## Findings requiring attention", ""]
        out += [f"- `{f['type']}` — {f['source_id']}: {f['detail']}" for f in flags]
    out += ["", "---", "", "Every figure above cites the source it was read from. "
            "Narrative text is generated; figures are not."]
    return "\n".join(out)


def _ungrounded_figures(prose: str, grounded: List[float], period: str) -> List[Dict[str, Any]]:
    """Numbers in generated prose that match no resolved figure.

    Only the narrative is checked. The figures block is constructed from
    resolved values and carries its own citations, so scanning it would just
    be checking the pipeline against itself.
    """
    allowed = set()
    for value in grounded:
        allowed.add(f"{value:g}")
        if float(value).is_integer():
            allowed.add(f"{int(value):,}")
            allowed.add(str(int(value)))
    for token in re.findall(r"\d+", period):
        allowed.add(token)

    found = []
    for raw in re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", prose):
        if raw in allowed or raw.replace(",", "") in {a.replace(",", "") for a in allowed}:
            continue
        found.append({"value": raw})
    return found


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------

def run(scenario: Mapping[str, Any], fixture_dir: str,
        model: Optional[ModelFn] = None) -> RunResult:
    """Draft the report for one scenario."""
    root = Path(fixture_dir)

    def _settings(name: str) -> Dict[str, Any]:
        """Load a settings file from config/ if present, else the root.

        A delivered engagement keeps its settings together in config/ so an
        operator has one folder to look in and one folder to leave alone. The
        synthetic fixture keeps them at its root. Supporting both means the
        package layout can be tidy without the gate suite needing a parallel
        copy of every fixture.
        """
        for candidate in (root / "config" / name, root / name):
            if candidate.is_file():
                return json.loads(candidate.read_text(encoding="utf-8"))
        raise FileNotFoundError(
            f"{name} not found in {root}/config/ or {root}/ — "
            f"the engagement is not configured"
        )

    dictionary = _settings("metric-dictionary.json")
    containment = _settings("containment.json")
    as_of = parse_instant(scenario.get("as_of", "2026-09-29T12:00:00Z")) or datetime.now(timezone.utc)

    adapter = MarkdownSourceAdapter(str(root))
    docs = _load_sources(adapter, scenario)

    # -- quarantine before anything reads content -------------------------
    incidents: List[Dict[str, Any]] = []
    egress_attempts: List[Dict[str, Any]] = []
    safe_bodies: Dict[str, str] = {}
    for source_id, doc in docs.items():
        safe, payloads, hosts = _quarantine(doc)
        safe_bodies[source_id] = safe
        if payloads:
            incidents.append({"type": "injection_detected", "source_id": source_id,
                              "signals": len(payloads), "path": doc["path"]})
            for host in sorted(set(hosts)):
                decision = check_egress(host, containment)
                egress_attempts.append({"host": host, "allowed": decision.allowed,
                                        "reason": decision.reason, "detail": decision.detail,
                                        "origin": f"injected instruction in {source_id}"})

    # -- scenario value overrides, applied after extraction would read ----
    for source_id, patch in (scenario.get("patch") or {}).items():
        if source_id not in docs:
            continue
        meta_patch = {k: str(v) for k, v in patch.items() if not isinstance(v, (int, float))}
        docs[source_id] = dict(docs[source_id], meta={**docs[source_id]["meta"], **meta_patch})
        body = safe_bodies[source_id]
        for key, value in patch.items():
            if isinstance(value, (int, float)):
                label_words = key.replace("_", " ")
                body = re.sub(
                    r"^\*\*([^:*]*%s[^:*]*):\s*[\d,]+(?:\.\d+)?\*\*\s*$" % re.escape(
                        label_words.split()[-1]),
                    lambda m: "**%s: %s**" % (m.group(1), value),
                    body, flags=re.MULTILINE | re.IGNORECASE)
        safe_bodies[source_id] = body

    resolved, missing, conflict = _resolve_metrics(dictionary, docs, safe_bodies)

    # -- halt conditions, in precedence order -----------------------------
    # Missing before conflict: you cannot reconcile figures you could not read,
    # and reporting a conflict while a source is absent would send the operator
    # to adjudicate a disagreement that may not exist once the file arrives.
    if missing:
        return RunResult(outcome="halt", halt_reason="missing_source", report=None,
                         missing_sources=sorted(missing), incidents=incidents,
                         egress_attempts=egress_attempts)
    if conflict:
        return RunResult(outcome="halt", halt_reason="metric_conflict", report=None,
                         conflict_metric=conflict["metric"],
                         conflict_values=conflict["values"], incidents=incidents,
                         egress_attempts=egress_attempts)

    flags = _freshness_flags(dictionary, docs,
                             [r["source_id"] for r in resolved.values()], as_of)

    prose = (model or _stub_model(scenario))("draft the narrative")

    uncited = _ungrounded_figures(prose, [r["value"] for r in resolved.values()],
                                  str(dictionary.get("period", "")))
    if uncited:
        # A figure nobody can trace does not get softened into prose, and does
        # not get published with a caveat. The run stops.
        return RunResult(outcome="halt", halt_reason="ungrounded_claim", report=None,
                         uncited_claims=uncited, flags=flags, incidents=incidents,
                         egress_attempts=egress_attempts)

    report = _render(str(dictionary.get("period", "")), resolved, prose, flags)
    return RunResult(outcome="drafted_with_flags" if flags else "drafted",
                     report=report, flags=flags, incidents=incidents,
                     egress_attempts=egress_attempts)
