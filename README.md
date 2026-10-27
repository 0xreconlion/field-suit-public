# Field Suit

[![CI](https://github.com/0xreconlion/field-suit/actions/workflows/ci.yml/badge.svg)](https://github.com/0xreconlion/field-suit/actions/workflows/ci.yml)

**Maturity:** v0.1.0 reference implementation — not a validated client platform.

Field Suit is a reference implementation for content-bound approvals and network containment in an AI-assisted impact-report workflow. It is runnable, offline, and built around one idea: capability should not imply authority.

```console
./scripts/bootstrap.sh
python3 evals/run.py
```

The offline suite contains 33 synthetic gate cases. No credentials or network connection are required.

## What you can inspect

- `src/field_suit/gateway/`: fixed-order, deny-by-default checks.
- `src/field_suit/approvals/`: approval issuance bound to exact action content.
- `src/field_suit/containment/`: destination allowlists and run cost ceilings.
- `src/field_suit/adapters/`: read-only source adapters; no write method exists.
- `src/field_suit/skills/`: a synthetic impact-report workflow.
- `src/field_suit/configure/` and `tools/engagement-setup.html`: configuration screen and validation.
- `fixtures/synthetic/`: the only included organization data.
- `plugins/field-suit-toolbox/`: public posture and workflow helpers.
- `evals/`: deterministic offline acceptance cases.

The key controls are independently testable. Approval of one content hash does not authorize later content. Instructions embedded inside source material are treated as findings. A destination not present in the containment allowlist stays unreachable even if a model is persuaded to ask for it.

## Limitations

This is a reference implementation, not a validated client platform. It does not establish regulatory compliance, verify that a source figure is true, or replace legal and security review. The included workflow and organization are synthetic. Any real deployment needs its own threat model, source ownership, data classification, approvals, and operational support.

## Public-export boundary

This repository is generated from an explicit public allowlist. It intentionally excludes operator playbooks, internal material, engagement data, traces, private paths, and knowledge-vault references. `python3 scripts/verify-public-export.py` fails on unexpected top-level paths, forbidden path classes, private-path markers, or a changed file inventory.

Licensed under MIT. See [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

