#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "PUBLIC-MANIFEST.json"
ALLOWED_TOP = {
    ".github", ".gitignore", "CONTRIBUTING.md", "LICENSE", "PUBLIC-MANIFEST.json",
    "README.md", "SECURITY.md", "contracts", "docs", "evals", "fixtures", "mcp",
    "plugins", "scripts", "src", "templates", "toolbox", "tools",
}
FORBIDDEN_PARTS = {"internal", "traces", "engagements", "operator-playbooks", ".env", "__pycache__"}
PRIVATE_MARKERS = re.compile(r"(?:/home/|/Users/|Primary Pi|Obsidian vault|tailscale\.net)", re.I)
MARKER_EXEMPT = {
    "scripts/screen-import.py",          # detects private paths in imported tools
    "scripts/verify-public-export.py",   # defines the patterns enforced here
}


def inventory() -> dict[str, str]:
    result = {}
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if (".git" in relative.parts or "__pycache__" in relative.parts
                or path.suffix == ".pyc" or path == MANIFEST or not path.is_file()):
            continue
        if relative.parts[0] not in ALLOWED_TOP:
            raise SystemExit(f"unexpected top-level path: {relative}")
        if any(part.lower() in FORBIDDEN_PARTS for part in relative.parts):
            raise SystemExit(f"forbidden public path: {relative}")
        data = path.read_bytes()
        if b"\x00" not in data:
            text = data.decode("utf-8", "replace")
            if relative.as_posix() not in MARKER_EXEMPT and PRIVATE_MARKERS.search(text):
                raise SystemExit(f"private-path marker in {relative}")
        result[relative.as_posix()] = hashlib.sha256(data).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="owner-only: refresh reviewed manifest")
    args = parser.parse_args()
    current = {"schemaVersion": 1, "files": inventory()}
    if args.write:
        MANIFEST.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {len(current['files'])} reviewed files")
        return 0
    expected = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if current != expected:
        missing = sorted(set(expected.get("files", {})) - set(current["files"]))
        added = sorted(set(current["files"]) - set(expected.get("files", {})))
        changed = sorted(k for k in set(current["files"]).intersection(expected.get("files", {})) if current["files"][k] != expected["files"][k])
        raise SystemExit(f"public export drift: added={added} missing={missing} changed={changed}")
    print(f"public export verified: {len(current['files'])} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

