"""Network egress control.

This is the half of the prompt-injection defence that still works after the
model has been successfully persuaded. You will not reliably stop a model from
being talked into something; you can make the destination unreachable.

Default-deny against a named allowlist. An empty allowlist blocks everything,
which is the correct behaviour for a misconfigured engagement: a run that can
reach nothing fails loudly and immediately, where a run that can reach
everything fails silently and later.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..types import Decision, sha256_of
from ..gateway.reasons import Reason

#: The only egress policy this module implements. Any other value denies --
#: an unrecognised policy name must not read as permission.
SUPPORTED_POLICY = "default-deny"


def _normalise_host(host: str) -> str:
    """Lowercase, strip a trailing dot, drop any port or userinfo.

    Hostname comparison is case-insensitive and ``example.test.`` is the same
    host as ``example.test``. Normalising both sides stops a trivially
    different spelling from bypassing the allowlist.
    """
    if not isinstance(host, str):
        return ""
    h = host.strip().lower()
    if "@" in h:
        h = h.rsplit("@", 1)[1]
    if h.startswith("["):  # bracketed IPv6
        h = h[1:h.index("]")] if "]" in h else h[1:]
    elif h.count(":") == 1:
        h = h.split(":", 1)[0]
    return h.rstrip(".")


def _allowed_by(host: str, pattern: str) -> bool:
    """Exact match, or an explicit ``*.`` subdomain wildcard.

    A bare ``*`` is not supported and a pattern is never treated as a
    substring: ``api.anthropic.com`` must not be satisfied by
    ``api.anthropic.com.attacker.test``, which a naive ``endswith`` would
    happily accept.
    """
    p = _normalise_host(pattern)
    if p.startswith("*."):
        suffix = p[1:]  # ".example.test"
        return host.endswith(suffix) and host != suffix.lstrip(".")
    return host == p


def check_egress(host: str, containment: Mapping[str, Any]) -> Decision:
    """Allow or deny an outbound connection to ``host``.

    Args:
        host: destination hostname. A port may be present and is ignored.
        containment: the loaded ``containment.json`` for this engagement.

    Returns:
        A :class:`Decision`. Denials carry
        ``containment.egress_host_not_allowlisted``.
    """
    egress = (containment or {}).get("egress") or {}
    policy_name = egress.get("policy")
    allowlist = egress.get("allowlist") or []
    ctx_hash = sha256_of({"policy": policy_name, "allowlist": sorted(allowlist)})
    attempt_hash = sha256_of({"host": host})

    normalised = _normalise_host(host)

    if policy_name != SUPPORTED_POLICY:
        return Decision(
            allowed=False,
            reason=Reason.EGRESS_HOST_NOT_ALLOWLISTED.value,
            check="containment:egress",
            policy_version=ctx_hash,
            request_hash=attempt_hash,
            detail=(
                f"egress policy is {policy_name!r}; only {SUPPORTED_POLICY!r} is "
                f"implemented, and an unrecognised policy denies rather than "
                f"defaulting open"
            ),
        )

    if not normalised:
        return Decision(
            allowed=False,
            reason=Reason.EGRESS_HOST_NOT_ALLOWLISTED.value,
            check="containment:egress",
            policy_version=ctx_hash,
            request_hash=attempt_hash,
            detail=f"uninterpretable host {host!r}",
        )

    if any(_allowed_by(normalised, p) for p in allowlist):
        return Decision(
            allowed=True,
            reason=Reason.ALLOWED.value,
            check=None,
            policy_version=ctx_hash,
            request_hash=attempt_hash,
            detail=f"{normalised} is on the egress allowlist",
        )

    return Decision(
        allowed=False,
        reason=Reason.EGRESS_HOST_NOT_ALLOWLISTED.value,
        check="containment:egress",
        policy_version=ctx_hash,
        request_hash=attempt_hash,
        detail=(
            f"{normalised} is not on the allowlist "
            f"({len(allowlist)} host(s) permitted)"
        ),
    )
