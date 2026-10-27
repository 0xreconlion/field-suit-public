"""The gateway. One pure function, six checks, frozen.

``decide`` takes a request, a policy, a clock, and an approval store, and
returns a :class:`Decision`. It reads nothing, writes nothing, and calls
nothing -- which is what makes it exhaustively testable offline and what stops
it from growing into a product of its own.

The six checks run in a fixed order and the first denial wins, so the reason
an operator reads is the *earliest* thing wrong rather than an arbitrary one.
Deny-by-default throughout: a check that cannot evaluate denies.

FEATURE FROZEN at milestone M2. A seventh check is a v2 decision with a
written reason, not a Tuesday.
"""

from __future__ import annotations

from typing import FrozenSet, Mapping, Optional

from ..types import Approval, Decision, Policy, ToolCallRequest
from . import checks
from .reasons import Reason

#: The fixed order. Named here so the sequence is readable in one place and
#: so a reordering is a visible diff rather than a subtle behaviour change.
CHECK_ORDER = (
    "1:identity",
    "2:purpose",
    "3:resource",
    "4:data_class",
    "5:operation",
    "6:approval",
)

VALID_OPERATIONS = frozenset({"read", "analyse", "draft", "write", "send", "execute"})


def _deny(reason: Reason, check: Optional[str], policy_hash: str,
          request_hash: str, detail: str = "") -> Decision:
    return Decision(
        allowed=False,
        reason=reason.value,
        check=check,
        policy_version=policy_hash,
        request_hash=request_hash,
        detail=detail,
    )


def decide(
    request: ToolCallRequest,
    policy: Optional[Policy],
    now: str,
    approvals: Optional[Mapping[str, Approval]] = None,
    used_approval_ids: Optional[FrozenSet[str]] = None,
) -> Decision:
    """Allow or deny one tool call.

    Args:
        request: the declared intent. Nothing in it is trusted.
        policy: the rules in force. ``None`` denies -- a missing policy must
            never read as "no restrictions".
        now: ISO-8601 instant, injected rather than read from the system clock
            so expiry behaviour is deterministic in tests.
        approvals: approval store keyed by approval id.
        used_approval_ids: approvals already spent. Single-use is enforced
            here rather than by mutating the store, keeping this function
            pure.

    Returns:
        A :class:`Decision` carrying exactly one reason, the check that
        produced it, the policy hash in force, and the request's binding hash.
    """
    # Request hash is computed first so that even a structural rejection is
    # attributable to a specific request in the log.
    try:
        request_hash = request.binding_hash()
    except Exception:
        request_hash = "unhashable"

    if policy is None:
        return _deny(Reason.POLICY_MISSING, None, "none", request_hash,
                     "no policy supplied; refusing rather than defaulting open")

    policy_hash = policy.hash()

    parsed_now = checks.parse_instant(now)
    if parsed_now is None:
        return _deny(Reason.REQUEST_MALFORMED, None, policy_hash, request_hash,
                     f"unparseable clock value {now!r}")

    resource = checks.normalise_resource(request.resource)
    if resource is None:
        return _deny(
            Reason.REQUEST_MALFORMED, None, policy_hash, request_hash,
            f"resource {request.resource!r} is absolute or escapes the "
            f"engagement root; a grant glob must never be satisfiable by a "
            f"path that leaves the tree it names",
        )

    if request.operation not in VALID_OPERATIONS:
        return _deny(Reason.REQUEST_MALFORMED, None, policy_hash, request_hash,
                     f"unknown operation {request.operation!r}")

    if not isinstance(request.tier, int) or request.tier < 0:
        return _deny(Reason.REQUEST_MALFORMED, None, policy_hash, request_hash,
                     f"tier {request.tier!r} is not a non-negative integer")

    # -- check 1: identity -------------------------------------------------
    reason = checks.check_identity(request, policy, parsed_now)
    if reason:
        return _deny(reason, CHECK_ORDER[0], policy_hash, request_hash,
                     f"actor {request.actor!r}")

    candidates = [g for g in policy.grants if g.actor == request.actor]

    # -- check 2: purpose --------------------------------------------------
    candidates, reason = checks.narrow_by_purpose(request, candidates)
    if reason:
        return _deny(reason, CHECK_ORDER[1], policy_hash, request_hash,
                     f"purpose {request.purpose!r} not granted to {request.actor!r}")

    # -- check 3: resource scope ------------------------------------------
    candidates, reason = checks.narrow_by_resource(resource, candidates)
    if reason:
        return _deny(reason, CHECK_ORDER[2], policy_hash, request_hash,
                     f"resource {resource!r} matches no granted pattern")

    # -- check 4: data class and destination ------------------------------
    candidates, reason = checks.check_data_class(request, policy, candidates)
    if reason:
        return _deny(reason, CHECK_ORDER[3], policy_hash, request_hash,
                     f"class {request.data_class!r} -> destination "
                     f"{request.destination!r}")

    # -- check 5: operation and tier --------------------------------------
    candidates, reason = checks.check_operation_tier(request, candidates)
    if reason:
        return _deny(reason, CHECK_ORDER[4], policy_hash, request_hash,
                     f"operation {request.operation!r} at tier {request.tier}")

    # -- check 6: approval -------------------------------------------------
    reason = checks.check_approval(request, policy, approvals, parsed_now,
                                   used_approval_ids)
    if reason:
        return _deny(reason, CHECK_ORDER[5], policy_hash, request_hash,
                     f"approval_ref {request.approval_ref!r}")

    if not candidates:
        # Unreachable by construction: every narrowing step returns a reason
        # when it empties the set. Kept because "allowed with no grant behind
        # it" is the one outcome that must never be possible, and a crash is
        # a better failure than a silent allow.
        return _deny(Reason.REQUEST_MALFORMED, None, policy_hash, request_hash,
                     "internal: no grant survived narrowing yet no reason set")

    return Decision(
        allowed=True,
        reason=Reason.ALLOWED.value,
        check=None,
        policy_version=policy_hash,
        request_hash=request_hash,
        detail=f"granted by {candidates[0].grant_id}",
    )
