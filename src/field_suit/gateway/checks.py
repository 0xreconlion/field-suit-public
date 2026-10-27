"""The six checks, plus the primitives they need.

Each check either passes or returns exactly one :class:`Reason`. None of them
can return "don't know": a check that cannot evaluate its input denies, which
is the only safe reading of an ambiguous authorization question.

The checks narrow a candidate set of grants in a fixed order. Narrowing (as
opposed to evaluating each grant independently and OR-ing the results) is what
lets the gateway report the *earliest* thing wrong rather than an arbitrary
one, so an operator reading a denial sees the most actionable cause.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Optional, Sequence, Tuple

from ..types import Grant, Policy, ToolCallRequest, data_class_rank
from .reasons import Reason

# --------------------------------------------------------------------------
# primitives
# --------------------------------------------------------------------------

_SEG = r"[^/]*"


def _glob_to_regex(pattern: str) -> "re.Pattern[str]":
    """Compile a resource glob.

    Semantics, chosen to be boring and explicit rather than inherited from
    whatever ``fnmatch`` happens to do:

    * ``**`` matches any number of path segments, including separators
    * ``*``  matches within a single segment only
    * ``?``  matches one character, not a separator

    ``fnmatch`` is deliberately not used: there, ``*`` crosses ``/``, so a
    pattern meant to grant one directory silently grants the whole tree
    beneath it.
    """
    out: List[str] = ["^"]
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "*":
            if pattern[i:i + 2] == "**":
                out.append(".*")
                i += 2
                # Swallow a following slash so "sources/**" also matches
                # "sources" itself rather than only things under it.
                if pattern[i:i + 1] == "/":
                    i += 1
                continue
            out.append(_SEG)
            i += 1
            continue
        if ch == "?":
            out.append("[^/]")
            i += 1
            continue
        out.append(re.escape(ch))
        i += 1
    out.append("$")
    return re.compile("".join(out))


def normalise_resource(resource: str) -> Optional[str]:
    """Return a safe relative resource path, or None if it is not one.

    Rejects absolute paths and any ``..`` segment. Without this, a pattern
    like ``sources/**`` would match ``sources/../../etc/shadow`` -- the glob
    is satisfied and the grant is honoured while the read escapes the
    engagement entirely. Returning None routes to REQUEST_MALFORMED.
    """
    if not resource or not isinstance(resource, str):
        return None
    if resource.startswith("/") or resource.startswith("\\"):
        return None
    if re.match(r"^[A-Za-z]:", resource):  # windows drive letter
        return None
    parts = [p for p in resource.replace("\\", "/").split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        return None
    return "/".join(parts)


def matches_any(resource: str, patterns: Sequence[str]) -> bool:
    return any(_glob_to_regex(p).match(resource) for p in patterns)


def parse_instant(value: str) -> Optional[datetime]:
    """Parse an ISO-8601 date or datetime into an aware UTC datetime.

    Handles a trailing ``Z``, which ``datetime.fromisoformat`` does not accept
    before Python 3.11 -- and this kit targets 3.9 so it runs on a locked-down
    client machine without an interpreter upgrade.

    A bare date is treated as end-of-day UTC: an agent registration that
    "expires 2027-03-31" is valid throughout that day rather than expiring at
    midnight, which is what a human writing that date means.
    """
    if not isinstance(value, str) or not value:
        return None
    text = value.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            dt = datetime.strptime(text, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
            return dt
        if text.endswith("Z") or text.endswith("z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


# --------------------------------------------------------------------------
# check 1 -- identity
# --------------------------------------------------------------------------

def check_identity(request: ToolCallRequest, policy: Policy, now: datetime) -> Optional[Reason]:
    agent = policy.agents.get(request.actor)
    if agent is None:
        return Reason.IDENTITY_UNKNOWN_ACTOR
    expires = parse_instant(agent.expires)
    if expires is None:
        # A registration whose expiry cannot be read is not a valid
        # registration. Denying here is what stops a typo from producing a
        # permanent agent.
        return Reason.IDENTITY_REGISTRATION_EXPIRED
    if now > expires:
        return Reason.IDENTITY_REGISTRATION_EXPIRED
    return None


# --------------------------------------------------------------------------
# check 2 -- purpose
# --------------------------------------------------------------------------

def narrow_by_purpose(
    request: ToolCallRequest, candidates: Sequence[Grant]
) -> Tuple[List[Grant], Optional[Reason]]:
    if not request.purpose:
        return [], Reason.PURPOSE_MISSING
    kept = [g for g in candidates if request.purpose in g.purposes]
    return (kept, None) if kept else ([], Reason.PURPOSE_NOT_PERMITTED)


# --------------------------------------------------------------------------
# check 3 -- resource scope
# --------------------------------------------------------------------------

def narrow_by_resource(
    resource: str, candidates: Sequence[Grant]
) -> Tuple[List[Grant], Optional[Reason]]:
    kept = [g for g in candidates if matches_any(resource, g.resources)]
    return (kept, None) if kept else ([], Reason.RESOURCE_NOT_IN_SCOPE)


# --------------------------------------------------------------------------
# check 4 -- data class and destination
# --------------------------------------------------------------------------

def check_data_class(
    request: ToolCallRequest, policy: Policy, candidates: Sequence[Grant]
) -> Tuple[List[Grant], Optional[Reason]]:
    rank = data_class_rank(request.data_class)
    if rank is None:
        return [], Reason.DATA_CLASS_UNKNOWN

    kept = [
        g for g in candidates
        if (data_class_rank(g.max_data_class) or -1) >= rank
    ]
    if not kept:
        return [], Reason.DATA_CLASS_EXCEEDS_GRANT

    if request.destination is not None:
        allowed_class = policy.destination_max_class.get(request.destination)
        if allowed_class is None:
            # An undeclared destination is not a permissive one.
            return [], Reason.DESTINATION_NOT_PERMITTED
        dest_rank = data_class_rank(allowed_class)
        if dest_rank is None or rank > dest_rank:
            return [], Reason.DESTINATION_NOT_PERMITTED
        kept = [g for g in kept if request.destination in g.destinations]
        if not kept:
            return [], Reason.DESTINATION_NOT_PERMITTED

    return kept, None


# --------------------------------------------------------------------------
# check 5 -- operation and tier
# --------------------------------------------------------------------------

def check_operation_tier(
    request: ToolCallRequest, candidates: Sequence[Grant]
) -> Tuple[List[Grant], Optional[Reason]]:
    kept = [g for g in candidates if request.operation in g.operations]
    if not kept:
        return [], Reason.OPERATION_NOT_IN_TIER
    kept = [g for g in kept if request.tier <= g.max_tier]
    if not kept:
        return [], Reason.TIER_EXCEEDS_GRANT
    return kept, None


# --------------------------------------------------------------------------
# check 6 -- approval
# --------------------------------------------------------------------------

def check_approval(request, policy, approvals, now, used_ids) -> Optional[Reason]:
    """Verify a hash-bound, unexpired, single-use approval.

    The binding is the point. An approval minted over a session, a user, or a
    time window authorizes whatever that session later decides to do. An
    approval minted over ``sha256(canonical(action))`` authorizes one action
    and refuses every variation of it, which is what makes "approve one diff,
    execute a different diff" impossible rather than merely discouraged.
    """
    if request.tier < policy.approval_required_at_tier:
        return None

    if not request.approval_ref:
        return Reason.APPROVAL_MISSING
    approval = (approvals or {}).get(request.approval_ref)
    if approval is None:
        return Reason.APPROVAL_MISSING

    # Binding is checked before expiry on purpose. A mismatched approval is
    # the more serious finding, and reporting "expired" for an approval that
    # was never for this action would send the operator to re-issue it --
    # exactly the wrong response.
    if approval.binding_hash != request.binding_hash():
        return Reason.APPROVAL_BINDING_MISMATCH

    if request.approval_ref in (used_ids or frozenset()):
        return Reason.APPROVAL_ALREADY_USED

    expires = parse_instant(approval.expires_at)
    if expires is None or now > expires:
        return Reason.APPROVAL_EXPIRED

    issued = parse_instant(approval.issued_at)
    if issued is None or now < issued:
        # An approval from the future is malformed, not merely early.
        return Reason.APPROVAL_EXPIRED

    return None
