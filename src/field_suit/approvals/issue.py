"""Minting approvals.

The verification side lives in ``gateway.checks.check_approval``. This is the
other half: turning a human's decision about one specific action into a token
the gateway will accept.

The whole design rests on one property. An approval is minted over
``sha256(canonical(action))`` — the exact content, target, and effect. It is
not scoped to a session, a role, or a time window alone. An approval scoped to
a session authorizes whatever that session later decides to do; an approval
bound to content authorizes one action and refuses every variation of it.

That is what makes *approve one diff, execute a different diff* impossible
rather than merely discouraged.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from ..gateway.checks import parse_instant
from ..types import Approval, ToolCallRequest

#: Default validity. Deliberately short. An approval that outlives the
#: reviewer's memory of what they approved is a standing permission wearing a
#: different name.
DEFAULT_TTL_MINUTES = 30

#: Hard ceiling. A caller asking for longer is asking for a standing
#: permission and should be made to say so explicitly, in policy, rather than
#: obtaining one by passing a large number here.
MAX_TTL_MINUTES = 240


class ApprovalError(ValueError):
    """An approval could not be minted as requested."""


def mint(
    request: ToolCallRequest,
    approver: str,
    now: str,
    ttl_minutes: int = DEFAULT_TTL_MINUTES,
    approval_id: Optional[str] = None,
) -> Approval:
    """Mint an approval bound to exactly this request.

    Args:
        request: the action being approved. Its binding hash is computed here
            rather than accepted from the caller — a caller-supplied hash
            would let the approving step and the executing step disagree
            about what was approved, which is the failure this prevents.
        approver: a person's name. Not a role, not a system, not "operator".
            Accountability that cannot be traced to a human is not
            accountability.
        now: ISO-8601 instant, injected rather than read from the clock so
            behaviour is deterministic in tests.
        ttl_minutes: validity window, capped at :data:`MAX_TTL_MINUTES`.

    Raises:
        ApprovalError: on an unnamed approver, an unparseable clock, or a TTL
            outside the permitted range. Each of these denies rather than
            falling back to a default, because every available default here
            is more permissive than the caller's intent.
    """
    if not approver or not approver.strip():
        raise ApprovalError(
            "an approval requires a named human approver; a role or a blank "
            "is not accountability"
        )
    issued = parse_instant(now)
    if issued is None:
        raise ApprovalError(f"unparseable clock value {now!r}")
    if ttl_minutes <= 0:
        raise ApprovalError(f"ttl_minutes must be positive, got {ttl_minutes!r}")
    if ttl_minutes > MAX_TTL_MINUTES:
        raise ApprovalError(
            f"ttl_minutes {ttl_minutes} exceeds the {MAX_TTL_MINUTES} minute "
            f"ceiling. A longer-lived permission is a policy change, made "
            f"deliberately and visibly, not a parameter passed here"
        )

    expires = issued + timedelta(minutes=ttl_minutes)
    return Approval(
        approval_id=approval_id or f"apv-{uuid.uuid4().hex[:10]}",
        binding_hash=request.binding_hash(),
        approver=approver.strip(),
        issued_at=issued.astimezone(timezone.utc).isoformat(timespec="seconds"),
        expires_at=expires.astimezone(timezone.utc).isoformat(timespec="seconds"),
    )


def describe_for_approver(request: ToolCallRequest) -> str:
    """What to show a human before they approve.

    They must see the exact content, target, and effect — not a summary and
    not a category. An approver shown "update the report" has approved
    whatever the system does next; an approver shown the resource, operation,
    destination, data class and action payload has approved one thing.
    """
    lines = [
        "You are approving ONE action. This approval will not authorize any",
        "other action, including a later version of this one.",
        "",
        f"  actor        {request.actor}",
        f"  purpose      {request.purpose}",
        f"  operation    {request.operation}   (tier {request.tier})",
        f"  resource     {request.resource}",
        f"  data class   {request.data_class}",
        f"  destination  {request.destination or '(none — stays local)'}",
    ]
    if request.action:
        lines.append("  action:")
        for key in sorted(request.action):
            lines.append(f"    {key} = {request.action[key]!r}")
    lines += [
        "",
        f"  binding      {request.binding_hash()[:16]}…",
        "",
        "If anything above changes, this approval stops matching and the",
        "action is refused. That is intended.",
    ]
    return "\n".join(lines)
