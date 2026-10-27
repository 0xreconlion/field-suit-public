"""Pre-access screen and precondition check.

Both run **before** any configuration is written and before any connection is
made. A guard placed after the thing it protects is not a guard.

## Why the screen refuses by default

Regulated data is not an edge case in any vertical, and nobody volunteers it in
an intake call. They are not hiding it; it is so ordinary to them that it does
not register as a disclosure. So the screen asks explicitly, names the
categories, and **refuses unless the answer is an affirmative no.** An
unanswered question is a refusal, not a pass.

In a nonprofit, beneficiary records routinely carry health information, minors,
eligibility determinations, immigration status, and housing or
domestic-violence service history -- a shelter's client list is a life-safety
document, not a privacy matter. In an owner-operated business the same shape
appears as personnel files, customer payment instruments and patient or client
records held under a contract nobody has reread. Different nouns, identical
exposure.

A first engagement runs on aggregates the organization already reports
somewhere. That is not a limitation imposed by caution -- it is sufficient for
the reporting workflow, which is what makes it an easy boundary to hold.

## Why the vertical is an explicit answer

Two questions have no vertical-neutral form, because the *right* answer differs
by how the organization is governed:

- **Who can adopt a policy.** A nonprofit board holds fiduciary authority and an
  executive signature is frequently not authorized at all. In an owner-operated
  business the owner *is* that authority, and demanding a board would be
  theatre. Generalising this question into one sentence either weakens it for
  the nonprofit or makes it nonsense for the LLC.
- **Which third-party agreements restrict data handling.** Grant and funder
  terms for one; customer contracts, DPAs and insurance for the other.

So the vertical is named, each profile states its own rule, and an unrecognised
vertical is **refused rather than guessed**. A profile ships disabled until a
named human has signed its authority rule -- see `docs/65-vertical-profiles.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

#: Categories that put a first engagement out of scope. Named explicitly
#: because "sensitive data" as a phrase reliably gets answered "no" by people
#: holding all of this.
REGULATED_CATEGORIES = {
    "health_or_medical": "health, medical, disability, or behavioural-health information",
    "minors": "records about anyone under 18",
    "eligibility_determinations": "benefit, program, or financial-eligibility decisions about individuals",
    "immigration_status": "citizenship, immigration, or visa status",
    "housing_or_dv_services": "housing, shelter, or domestic-violence service records",
    "criminal_justice": "arrest, conviction, probation, or reentry records",
    "employment_records": "individual personnel, disciplinary, or compensation records",
    "financial_accounts": "bank details, payment instruments, or donor payment records",
}

@dataclass(frozen=True)
class VerticalProfile:
    """How one kind of organization is governed, for the two questions that differ.

    ``enabled=False`` means the profile is **drafted but not signed**: the
    wording exists so it can be reviewed, and the screen refuses it so it
    cannot be used before that review happens. Enabling one is a human
    decision recorded in ``docs/65-vertical-profiles.md``, not a config tweak.
    """

    label: str
    enabled: bool
    #: Who holds the authority to adopt an AI use policy here.
    authority_statement: str
    #: What "aggregates only" means for this kind of organization.
    aggregate_statement: str
    #: Which third-party agreements can restrict data handling.
    third_party_terms: str
    #: Who signed the authority rule, or what is still needed.
    sign_off: str


#: Keyed by the value of the ``vertical`` answer. Add a profile here *and*
#: record its sign-off before setting ``enabled=True``.
VERTICAL_PROFILES: Dict[str, VerticalProfile] = {
    "nonprofit": VerticalProfile(
        label="Nonprofit or NGO with a governing board",
        enabled=True,
        authority_statement=(
            "The governing board has adopted an AI use policy (an executive "
            "signature alone is not sufficient and at most nonprofits is not "
            "authorized)."
        ),
        aggregate_statement=(
            "The pilot will use only aggregate figures the organization already "
            "publishes or already reports to a funder."
        ),
        third_party_terms="Grant and funder agreements",
        sign_off="Signed by Zach Alkharusy, 2026-09-29, as the original design basis.",
    ),
    "owner_operated": VerticalProfile(
        label="Owner-operated business (sole proprietor, LLC, partnership)",
        enabled=True,
        authority_statement=(
            "The owner or managing member who can bind the business has adopted an "
            "AI use policy in writing. They may also be the named stop authority."
        ),
        aggregate_statement=(
            "The pilot will use only aggregate figures the business already reports "
            "to a lender, insurer, franchisor or tax preparer."
        ),
        third_party_terms="Customer contracts, data-processing addenda, and insurance terms",
        sign_off=(
            "Signed by Zach Alkharusy, 2026-10-03. Decision: a single owner holding "
            "both policy authority and stop authority IS acceptable here, because "
            "they carry the whole liability and there is nobody above them -- "
            "requiring a second signatory would produce a spouse or a direct report "
            "rubber-stamping it, and a fake control reads as coverage while "
            "protecting nothing. Compensating control: because an invested owner "
            "cannot be impartial at the worst moment, this profile requires the "
            "halt conditions to be WRITTEN DOWN IN ADVANCE and objective, so the "
            "stop does not depend on anyone's judgment in the moment."
        ),
    ),
}

#: Questions that must be answered true for the engagement to proceed.
#:
#: The **keys** are the contract -- the setup form is checked against them by
#: gate 21. Two of the statements are placeholders replaced at screen time by
#: the vertical's own wording, because their correct form is governance-specific
#: (see the module docstring).
REQUIRED_ASSURANCES = {
    "vertical": "The kind of organization is named, and its governing-authority rule is one this kit has signed off.",
    "aggregates_only": "The pilot will use only aggregate figures the organization already reports somewhere.",
    "sponsor_named": "A named accountable sponsor exists.",
    "stop_authority_named": "A named person can stop the engagement at any time.",
    "governing_authority_adopted_policy": "The body with authority to adopt policy has adopted an AI use policy.",
    "data_agreement_signed": "A confidentiality and data-handling agreement is signed.",
}

#: Assurances whose wording the vertical profile overrides.
_PROFILE_STATEMENTS = {
    "aggregates_only": "aggregate_statement",
    "governing_authority_adopted_policy": "authority_statement",
}


def resolve_vertical(answers: Mapping[str, Any]) -> tuple[Optional[VerticalProfile], Optional[str]]:
    """Return the profile for ``answers['vertical']``, or a refusal reason.

    Three ways this refuses, all deliberately: unanswered, unrecognised, and
    recognised-but-unsigned. The third is the one worth having -- it is how a
    half-finished profile stays unusable instead of quietly becoming the default
    for a kind of business nobody designed the rule for.
    """
    raw = answers.get("vertical")
    if not isinstance(raw, str) or not raw.strip():
        return None, None  # unanswered; reported by the normal unanswered path
    key = raw.strip()
    profile = VERTICAL_PROFILES.get(key)
    if profile is None:
        known = ", ".join(sorted(k for k, p in VERTICAL_PROFILES.items() if p.enabled))
        return None, (
            f"vertical {key!r} is not a profile this kit has. Signed and usable: "
            f"{known or '(none)'}. Adding one is a human decision -- see "
            f"docs/65-vertical-profiles.md. Do not configure against the closest match."
        )
    if not profile.enabled:
        return None, (
            f"vertical {key!r} ({profile.label}) is drafted but NOT signed off. "
            f"{profile.sign_off}"
        )
    return profile, None

PRECONDITIONS = {
    "workflow_card": "One workflow, named and observed, with ten real instances recorded.",
    "source_register": "Every source named, with an owner role AND a current holder, and a data class.",
    "metric_dictionary": "Every number defined once, with a single named source of truth.",
    "frozen_baseline": "A signed before-picture that will never be recomputed.",
    "human_only_list": "The written list of decisions that stay human.",
    "named_operator": "A named accountable human, recorded as a role plus the current holder.",
    # Added when owner_operated was signed off (2026-10-03). A named stop
    # authority assumes that person can be impartial when the thing they
    # commissioned starts going wrong. In an owner-operated business the stop
    # authority IS the champion, so that assumption does not hold -- the fix is
    # to decide the halt conditions while nobody is under pressure, in writing
    # and objectively, rather than relying on judgment at the worst moment.
    #
    # Required in every vertical, not just that one. It is a tightening (one
    # more artifact must exist), it weakens nothing already signed, and a
    # nonprofit board benefits from the same pre-commitment.
    "halt_conditions": "Written, objective conditions that stop the engagement — checkable facts, not 'if it goes wrong'.",
}


@dataclass
class ScreenResult:
    passed: bool
    refusals: List[str] = field(default_factory=list)
    missing_preconditions: List[str] = field(default_factory=list)
    unanswered: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def report(self) -> str:
        if self.passed:
            return "PRE-ACCESS SCREEN: pass — aggregates only, preconditions met."
        lines = ["PRE-ACCESS SCREEN: REFUSED", ""]
        if self.refusals:
            lines.append("Out of scope for a first engagement:")
            lines += [f"  - {r}" for r in self.refusals]
            lines.append("")
            lines.append("  This is not a permanent no. It means the pilot runs on")
            lines.append("  aggregates first, and any work touching these records is")
            lines.append("  scoped separately with its own review and its own agreement.")
            lines.append("")
        if self.unanswered:
            lines.append("Unanswered — an unanswered question is a refusal, not a pass:")
            lines += [f"  - {q}" for q in self.unanswered]
            lines.append("")
        if self.missing_preconditions:
            lines.append("Discovery is not finished. Missing:")
            lines += [f"  - {p}" for p in self.missing_preconditions]
            lines.append("")
            lines.append("  The answer here is not 'configure it anyway'. Until these")
            lines.append("  exist there is nothing specific enough to configure, and a")
            lines.append("  kit configured against guesses produces confident wrong")
            lines.append("  answers rather than obvious failures.")
        return "\n".join(lines)


def run_screen(answers: Mapping[str, Any]) -> ScreenResult:
    """Evaluate the pre-access screen against an answer set.

    ``answers`` maps question keys to booleans. A key that is absent is
    **not** treated as false-and-fine; it is reported as unanswered and the
    screen refuses. Silence is the most common way a disclosure fails to
    happen.
    """
    result = ScreenResult(passed=True)

    def answered(key: str) -> bool:
        """True only for an explicit boolean.

        ``None`` counts as unanswered, not as "no". The blank template ships
        every question as null, so treating null as false would let a
        half-filled form sail through the regulated-data check while the
        operator believed they had skipped those questions. That is the
        dangerous direction, so it is the one that is closed.
        """
        return isinstance(answers.get(key), bool)

    for key, description in REGULATED_CATEGORIES.items():
        if not answered(key):
            result.unanswered.append(f"Does the pilot data include {description}?")
            result.passed = False
        elif answers[key]:
            result.refusals.append(f"pilot data includes {description}")
            result.passed = False

    # The vertical is resolved first: it supplies the wording for two of the
    # assurances below, and an unsigned vertical must refuse even when every
    # other answer is clean.
    profile, vertical_refusal = resolve_vertical(answers)
    if vertical_refusal:
        result.refusals.append(vertical_refusal)
        result.passed = False

    for key, statement in REQUIRED_ASSURANCES.items():
        if key == "vertical":
            # Answered with a profile key, not a boolean.
            if not isinstance(answers.get(key), str) or not answers[key].strip():
                result.unanswered.append(statement)
                result.passed = False
            continue
        if profile is not None and key in _PROFILE_STATEMENTS:
            statement = getattr(profile, _PROFILE_STATEMENTS[key])
        if not answered(key):
            result.unanswered.append(statement)
            result.passed = False
        elif not answers[key]:
            result.refusals.append(f"not satisfied: {statement}")
            result.passed = False

    provided = set(answers.get("preconditions") or [])
    for key, description in PRECONDITIONS.items():
        if key not in provided:
            result.missing_preconditions.append(f"{key} — {description}")
            result.passed = False

    if answers.get("third_party_terms_reviewed") is not True:
        terms = profile.third_party_terms if profile else "Third-party agreements"
        result.notes.append(
            f"{terms} can restrict data handling and subprocessor use. This is "
            "agreement-specific and jurisdiction-specific — read the actual terms "
            "or route to counsel. Do not state a compliance position from a "
            "framework summary."
        )
    return result
