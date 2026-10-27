"""Per-run cost ceiling.

A nonprofit cannot absorb a surprise API bill, and "it got expensive" is how a
pilot dies quietly without anyone filing it as a failure. So cost is a gate
like any other: projected spend is checked *before* the work runs, and a run
over its ceiling halts and reports rather than completing and billing.

The check is on projected cost, not actual. Discovering you exceeded the
ceiling after the tokens are spent is an invoice, not a control.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..types import Decision, sha256_of
from ..gateway.reasons import Reason

#: Usage keys. ``input_tokens`` is *uncached* input; cached input is counted
#: separately because it bills at a different rate. Conflating them is the
#: easy mistake and it under-projects cost, which is the dangerous direction.
USAGE_KEYS = ("input_tokens", "output_tokens", "cached_input_tokens")


def project_usd(usage: Mapping[str, Any], pricing: Mapping[str, float]) -> float:
    """Projected cost in USD for a usage profile.

    Cached input bills at a reduced rate; batch halves both directions. Any
    rate missing from ``pricing`` is treated as the full input rate rather
    than as zero -- a missing rate must never make something look free.
    """
    def rate(key: str, fallback_key: str = "input") -> float:
        value = pricing.get(key)
        if value is None:
            value = pricing.get(fallback_key, 0.0)
        return float(value)

    uncached = float(usage.get("input_tokens", 0) or 0)
    cached = float(usage.get("cached_input_tokens", 0) or 0)
    output = float(usage.get("output_tokens", 0) or 0)

    total = (
        uncached * rate("input")
        + cached * rate("cached_input")
        + output * rate("output")
    ) / 1_000_000.0

    if usage.get("batch"):
        total *= float(pricing.get("batch_multiplier", 1.0))
    return total


def total_tokens(usage: Mapping[str, Any]) -> int:
    return int(sum(float(usage.get(k, 0) or 0) for k in USAGE_KEYS))


def check_budget(usage: Mapping[str, Any], budget: Mapping[str, Any]) -> Decision:
    """Allow or deny a run against its declared ceiling.

    Both a dollar ceiling and a token ceiling are checked, and either one
    tripping denies. They catch different failures: a dollar ceiling catches
    an expensive model, a token ceiling catches a retry loop or an unfiltered
    source dump that is cheap per token and enormous in total.
    """
    pricing = budget.get("pricing_usd_per_mtok") or {}
    ceiling_usd = budget.get("ceiling_usd")
    ceiling_tokens = budget.get("ceiling_tokens")

    ctx_hash = sha256_of({"ceiling_usd": ceiling_usd, "ceiling_tokens": ceiling_tokens})
    usage_hash = sha256_of({k: usage.get(k) for k in sorted(usage)})

    if ceiling_usd is None and ceiling_tokens is None:
        return Decision(
            allowed=False,
            reason=Reason.COST_BUDGET_EXCEEDED.value,
            check="containment:cost",
            policy_version=ctx_hash,
            request_hash=usage_hash,
            detail=(
                "no ceiling declared; a budget file with no ceiling is an "
                "unbounded budget and denies rather than permitting an "
                "uncapped run"
            ),
        )

    projected = project_usd(usage, pricing)
    tokens = total_tokens(usage)
    breaches = []
    if ceiling_usd is not None and projected > float(ceiling_usd):
        breaches.append(f"${projected:.4f} projected > ${float(ceiling_usd):.4f} ceiling")
    if ceiling_tokens is not None and tokens > int(ceiling_tokens):
        breaches.append(f"{tokens:,} tokens > {int(ceiling_tokens):,} ceiling")

    if breaches:
        return Decision(
            allowed=False,
            reason=Reason.COST_BUDGET_EXCEEDED.value,
            check="containment:cost",
            policy_version=ctx_hash,
            request_hash=usage_hash,
            detail="; ".join(breaches),
        )

    return Decision(
        allowed=True,
        reason=Reason.ALLOWED.value,
        check=None,
        policy_version=ctx_hash,
        request_hash=usage_hash,
        detail=f"${projected:.4f} projected, {tokens:,} tokens, within ceiling",
    )
