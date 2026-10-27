"""Enumerated decision reasons.

Every gateway decision carries exactly one of these. They are the vocabulary an
operator reads when asking "why was this allowed or denied?", so each one names
a specific condition rather than a category. A generic reason code is a defect:
if two different failures produce the same code, the log cannot distinguish
them and the operator cannot act on either.

Codes are stable strings, not integers. They appear verbatim in the decision
log and in eval assertions, so renaming one is a breaking change.
"""

from __future__ import annotations

from enum import Enum


class Reason(str, Enum):
    """Why a request was allowed or denied."""

    # -- allow ------------------------------------------------------------
    ALLOWED = "allowed"

    # -- check 1: identity -------------------------------------------------
    IDENTITY_UNKNOWN_ACTOR = "identity.unknown_actor"
    IDENTITY_REGISTRATION_EXPIRED = "identity.registration_expired"

    # -- check 2: purpose --------------------------------------------------
    PURPOSE_MISSING = "purpose.missing"
    PURPOSE_NOT_PERMITTED = "purpose.not_permitted"

    # -- check 3: resource scope ------------------------------------------
    RESOURCE_NOT_IN_SCOPE = "resource.not_in_scope"

    # -- check 4: data class ----------------------------------------------
    DATA_CLASS_UNKNOWN = "data_class.unknown"
    DATA_CLASS_EXCEEDS_GRANT = "data_class.exceeds_grant"
    DESTINATION_NOT_PERMITTED = "data_class.destination_not_permitted"

    # -- check 5: operation / tier ----------------------------------------
    OPERATION_NOT_IN_TIER = "operation.not_in_tier"
    TIER_EXCEEDS_GRANT = "operation.tier_exceeds_grant"

    # -- check 6: approval -------------------------------------------------
    APPROVAL_MISSING = "approval.missing"
    APPROVAL_EXPIRED = "approval.expired"
    APPROVAL_ALREADY_USED = "approval.already_used"
    APPROVAL_BINDING_MISMATCH = "approval.binding_mismatch"

    # -- containment (enforced outside the six checks) ---------------------
    EGRESS_HOST_NOT_ALLOWLISTED = "containment.egress_host_not_allowlisted"
    COST_BUDGET_EXCEEDED = "containment.cost_budget_exceeded"

    # -- structural failures -----------------------------------------------
    # These exist so that a malformed input can never fall through to allow.
    POLICY_MISSING = "structural.policy_missing"
    REQUEST_MALFORMED = "structural.request_malformed"


#: Every reason other than ALLOWED denies. Stated explicitly rather than
#: inferred, so that adding a reason without classifying it fails loudly at
#: import time instead of silently defaulting to allow.
DENY_REASONS = frozenset(r for r in Reason if r is not Reason.ALLOWED)


def is_denial(reason: Reason) -> bool:
    """True if this reason denies the request.

    Deliberately not ``reason != Reason.ALLOWED``: this routes through the
    explicit set above so that a future reason which is neither cannot quietly
    read as an allow.
    """
    if reason is Reason.ALLOWED:
        return False
    if reason in DENY_REASONS:
        return True
    raise ValueError(f"unclassified reason: {reason!r}")
