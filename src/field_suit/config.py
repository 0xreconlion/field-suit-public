"""Loading and validating engagement configuration.

JSON rather than YAML throughout. YAML would need PyYAML, and zero runtime
dependencies is a deliberate security property here: it removes the kit's own
supply-chain surface and means it runs on a locked-down machine that cannot
pip-install anything. Operators rarely hand-edit these files anyway --
``scripts/configure.py`` generates them.

Keys beginning with an underscore are documentation for whoever opens the file
and are ignored by every loader below.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping

from .types import Agent, Grant, Policy, data_class_rank


class ConfigError(ValueError):
    """Configuration that cannot be loaded.

    Raised rather than returning a default, because every default available
    here would be more permissive than the file the operator meant to write.
    """


def _strip_docs(obj: Any) -> Any:
    """Recursively drop underscore-prefixed documentation keys."""
    if isinstance(obj, dict):
        return {k: _strip_docs(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_strip_docs(v) for v in obj]
    return obj


def load_json(path: Path) -> Dict[str, Any]:
    """Read a JSON config file, with documentation keys removed."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"config file not found: {path}")
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path} is not valid JSON: {exc}")
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a JSON object at the top level")
    return _strip_docs(raw)


def _require(d: Mapping[str, Any], key: str, where: str) -> Any:
    if key not in d:
        raise ConfigError(f"{where}: missing required key {key!r}")
    return d[key]


def load_policy(path: Path) -> Policy:
    """Build a :class:`Policy` from a policy JSON file.

    Validates eagerly. A policy that half-loads is worse than one that refuses:
    the gateway would then decide against rules the operator never wrote.
    """
    raw = load_json(path)
    where = str(path)

    agents: Dict[str, Agent] = {}
    for agent_id, spec in _require(raw, "agents", where).items():
        expires = _require(spec, "expires", f"{where}: agent {agent_id!r}")
        agents[agent_id] = Agent(agent_id=agent_id, expires=expires)

    dest_max = _require(raw, "destination_max_class", where)
    for dest, cls in dest_max.items():
        if data_class_rank(cls) is None:
            raise ConfigError(
                f"{where}: destination {dest!r} declares unknown data class {cls!r}"
            )

    grants = []
    for spec in _require(raw, "grants", where):
        gid = _require(spec, "grant_id", where)
        g_where = f"{where}: grant {gid!r}"
        max_class = _require(spec, "max_data_class", g_where)
        if data_class_rank(max_class) is None:
            raise ConfigError(f"{g_where}: unknown max_data_class {max_class!r}")
        actor = _require(spec, "actor", g_where)
        if actor not in agents:
            raise ConfigError(
                f"{g_where}: grants capability to unregistered actor {actor!r}"
            )
        for dest in spec.get("destinations", []):
            if dest not in dest_max:
                raise ConfigError(
                    f"{g_where}: names destination {dest!r} with no declared max class"
                )
        grants.append(
            Grant(
                grant_id=gid,
                actor=actor,
                purposes=frozenset(_require(spec, "purposes", g_where)),
                operations=frozenset(_require(spec, "operations", g_where)),
                resources=list(_require(spec, "resources", g_where)),
                max_data_class=max_class,
                destinations=frozenset(spec.get("destinations", [])),
                max_tier=int(_require(spec, "max_tier", g_where)),
            )
        )

    return Policy(
        policy_version=_require(raw, "policy_version", where),
        agents=agents,
        grants=grants,
        destination_max_class=dest_max,
        approval_required_at_tier=int(raw.get("approval_required_at_tier", 3)),
    )
