"""Core data types shared by the gateway, the adapters, and the eval suite.

Everything here is frozen. A request that could be mutated between the approval
check and the adapter call would make hash-binding meaningless, which is the
one property the whole gateway exists to provide.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Mapping, Optional, Sequence, Tuple

# Data classifications, ordered least to most sensitive. The ordering is the
# comparison used by check 4, so it is defined once here rather than inline.
DATA_CLASSES: Tuple[str, ...] = ("public", "internal", "confidential", "restricted")


def data_class_rank(name: str) -> Optional[int]:
    """Rank of a data class, or None if it is not a recognised class.

    Returns None rather than raising or defaulting, because an unrecognised
    class must deny (DATA_CLASS_UNKNOWN) and not be silently coerced to the
    most permissive value. Fail closed.
    """
    try:
        return DATA_CLASSES.index(name)
    except ValueError:
        return None


def canonical_json(payload: Any) -> str:
    """Deterministic JSON encoding used for every hash we bind to.

    Sorted keys, no insignificant whitespace, no NaN. Two structurally equal
    payloads must produce byte-identical output on any machine and any Python
    build, or approvals minted on one host will not verify on another.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_of(payload: Any) -> str:
    """Hex sha256 over the canonical encoding of ``payload``."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ToolCallRequest:
    """One attempt by an actor to use one tool against one resource.

    This is the unit the gateway decides on. It carries the *declared* intent;
    nothing here is trusted until the checks have run.
    """

    actor: str
    purpose: str
    workflow: str
    tool: str
    operation: str
    resource: str
    data_class: str
    tier: int
    destination: Optional[str] = None
    approval_ref: Optional[str] = None
    #: Free-form action detail. Included in the binding hash, so anything that
    #: changes what would actually happen belongs here — a diff, a message
    #: body, a target record id.
    action: Mapping[str, Any] = field(default_factory=dict)

    def binding_payload(self) -> Dict[str, Any]:
        """The exact fields an approval is minted over.

        ``approval_ref`` is deliberately excluded: the approval cannot be part
        of what it attests to. Everything else that determines what happens is
        included, so approving one action and executing another produces a
        different hash and is refused.
        """
        return {
            "actor": self.actor,
            "purpose": self.purpose,
            "workflow": self.workflow,
            "tool": self.tool,
            "operation": self.operation,
            "resource": self.resource,
            "data_class": self.data_class,
            "tier": self.tier,
            "destination": self.destination,
            "action": dict(self.action),
        }

    def binding_hash(self) -> str:
        """sha256 over :meth:`binding_payload`. This is what approvals bind to."""
        return sha256_of(self.binding_payload())


@dataclass(frozen=True)
class Decision:
    """The gateway's answer, plus everything needed to audit it later."""

    allowed: bool
    reason: str
    #: Which of the six checks produced this, e.g. "4:data_class". None on a
    #: structural failure that happened before any check ran.
    check: Optional[str]
    policy_version: str
    request_hash: str
    #: Human-readable elaboration. Safe to log: never contains prompts,
    #: model output, or resource *contents* — only identifiers and classes.
    detail: str = ""


@dataclass(frozen=True)
class Grant:
    """One capability granted to one actor.

    A grant is narrow on purpose: an actor with three kinds of access holds
    three grants, so revoking one does not widen or narrow the others.
    """

    grant_id: str
    actor: str
    purposes: FrozenSet[str]
    operations: FrozenSet[str]
    resources: Sequence[str]  # glob patterns
    max_data_class: str
    destinations: FrozenSet[str]
    max_tier: int


@dataclass(frozen=True)
class Agent:
    """A registered actor. Unregistered actors are denied at check 1."""

    agent_id: str
    #: ISO-8601 date. A registration with no expiry is not permitted —
    #: an agent nobody has re-confirmed is a finding, not a default.
    expires: str


@dataclass(frozen=True)
class Policy:
    """The complete authorization state the gateway decides against."""

    policy_version: str
    agents: Mapping[str, Agent]
    grants: Sequence[Grant]
    #: Which destinations may receive which data class.
    destination_max_class: Mapping[str, str]
    #: Minimum tier at which an approval is required. Tier >= this must
    #: present a valid, hash-bound, unexpired, unused approval.
    approval_required_at_tier: int = 3

    def hash(self) -> str:
        """Stable hash of the policy, recorded on every decision.

        Lets an auditor answer "which rules were in force when this was
        allowed?" without needing the policy file to have been archived.
        """
        return sha256_of(
            {
                "policy_version": self.policy_version,
                "agents": {k: v.expires for k, v in sorted(self.agents.items())},
                "grants": [
                    {
                        "grant_id": g.grant_id,
                        "actor": g.actor,
                        "purposes": sorted(g.purposes),
                        "operations": sorted(g.operations),
                        "resources": list(g.resources),
                        "max_data_class": g.max_data_class,
                        "destinations": sorted(g.destinations),
                        "max_tier": g.max_tier,
                    }
                    for g in self.grants
                ],
                "destination_max_class": dict(sorted(self.destination_max_class.items())),
                "approval_required_at_tier": self.approval_required_at_tier,
            }
        )


@dataclass(frozen=True)
class Approval:
    """A human's authorization for one specific action.

    Bound to a hash, single-use, and expiring. All three properties are
    required: a long-lived approval is a standing permission wearing a
    different name, and an approval bound to a session rather than to content
    authorizes whatever that session later decides to do.
    """

    approval_id: str
    #: The ToolCallRequest.binding_hash() this approval attests to.
    binding_hash: str
    #: Who approved. A name, not a role.
    approver: str
    issued_at: str  # ISO-8601
    expires_at: str  # ISO-8601
