"""Read-only adapter over a directory of Markdown sources.

This class has no write method, and that absence is the point. The gateway
decides whether a write is permitted; this adapter makes the question moot by
having nothing to call. Two independent reasons the same action fails, and the
second one survives a policy misconfiguration.

That property is asserted by gate 6, which inspects this class for any
mutating method by name. Adding ``save_source`` here would fail the suite even
if every policy in the repo still denied writes -- which is the intent: a
capability that exists is a capability that will eventually be granted by
accident.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(text: str) -> Dict[str, str]:
    """Parse the flat ``key: value`` frontmatter block.

    A deliberately minimal parser: these files carry a fixed, flat set of
    scalar keys, and pulling in a YAML library for that would add a runtime
    dependency to a kit whose zero-dependency property is a security claim.
    Nested structures are not supported and must not be introduced here --
    if a source needs them, that is a signal the source register is carrying
    data it should not.
    """
    match = _FRONTMATTER.match(text)
    if not match:
        return {}
    out: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip().strip("'\"")
    return out


class ReadOnlyViolation(RuntimeError):
    """Raised if anything attempts to mutate through this adapter."""


class MarkdownSourceAdapter:
    """Reads Markdown sources from one engagement directory.

    Every public method is a read. There is no write path, no append path, and
    no file handle in write mode anywhere in this module.
    """

    def __init__(self, root: str) -> None:
        self._root = Path(root).resolve()

    @property
    def root(self) -> Path:
        return self._root

    def _resolve(self, relative: str) -> Path:
        """Resolve a relative path, refusing anything outside the root.

        The gateway already rejects traversal in the request, but this adapter
        re-checks rather than trusting it. A guard that assumes an earlier
        guard ran is not a guard.
        """
        candidate = (self._root / relative).resolve()
        try:
            candidate.relative_to(self._root)
        except ValueError:
            raise ReadOnlyViolation(
                f"path {relative!r} resolves outside the engagement root"
            )
        return candidate

    def list_sources(self, subdir: str = "sources") -> List[str]:
        """Relative paths of every Markdown source under ``subdir``."""
        base = self._resolve(subdir)
        if not base.is_dir():
            return []
        return sorted(
            str(p.relative_to(self._root)) for p in base.glob("*.md")
        )

    def read_source(self, relative: str) -> Optional[Dict[str, Any]]:
        """Read one source. Returns None if it does not exist.

        None rather than raising, because "this source is absent" is a normal
        finding the workflow must halt on visibly (gate 2) -- not an
        exceptional condition. The caller distinguishes absent from
        unreadable; both are reported, neither is skipped.
        """
        path = self._resolve(relative)
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
        meta = _parse_frontmatter(text)
        return {
            "path": relative,
            "source_id": meta.get("source_id", Path(relative).stem),
            "meta": meta,
            "body": _FRONTMATTER.sub("", text, count=1),
        }

    def read_all(self, subdir: str = "sources") -> List[Dict[str, Any]]:
        out = []
        for rel in self.list_sources(subdir):
            doc = self.read_source(rel)
            if doc is not None:
                out.append(doc)
        return out
