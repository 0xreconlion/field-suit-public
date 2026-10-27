#!/usr/bin/env bash
# Build a STANDALONE engagement package for one organization.
#
# The output does not depend on this repository. It vendors the runtime, the
# gate suite, and the self-test fixture, so the organization can run it, verify
# it, and keep using it after the engagement ends — with the kit deleted and
# the consultant gone.
#
# That is the whole point. An engagement that needs the consultant's repo on
# disk is an engagement that needs the consultant. Handing over a config file
# that references a repo they do not have is handing over a dependency and
# calling it a deliverable.
#
# It is also NEVER a fork of this repo. A fork puts their data in a descendant
# of the kit, which is the one failure that ends the practice. Separate repo,
# separate history, no submodule, no shared remote.
#
# Usage:
#   scripts/new-engagement.sh --answers answers.json --out ../engagement-acme
#   scripts/new-engagement.sh --answers answers.json --out ../eng-acme --no-git

set -euo pipefail
KIT="$(cd "$(dirname "$0")/.." && pwd)"

ANSWERS=""; OUT=""; DO_GIT=1
while [ $# -gt 0 ]; do
  case "$1" in
    --answers) ANSWERS="$2"; shift 2 ;;
    --out)     OUT="$2";     shift 2 ;;
    --no-git)  DO_GIT=0;     shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ -n "$ANSWERS" ] && [ -n "$OUT" ] || { echo "need --answers and --out" >&2; exit 2; }
[ -f "$ANSWERS" ] || { echo "no such answers file: $ANSWERS" >&2; exit 2; }

# ---------------------------------------------------------------------------
# GUARD FIRST. The pre-access screen runs before a single byte is written.
# A guard placed after the writes it protects is not a guard.
# ---------------------------------------------------------------------------
echo "▸ Pre-access screen"
if ! python3 "$KIT/scripts/configure.py" --answers "$ANSWERS" --dry-run >/tmp/.screen.$$ 2>&1; then
  cat /tmp/.screen.$$; rm -f /tmp/.screen.$$
  echo
  echo "✗ Screen refused. No package written." >&2
  exit 1
fi
sed -n '1,3p' /tmp/.screen.$$; rm -f /tmp/.screen.$$

[ -e "$OUT" ] && { echo "✗ $OUT already exists — refusing to overwrite" >&2; exit 1; }

ORG="$(python3 -c "import json;print(json.load(open('$ANSWERS')).get('organization','the organization'))")"
echo "▸ Building standalone package for: $ORG"

mkdir -p "$OUT"/{config,sources,reports,docs,engine,runs}

# ---------------------------------------------------------------------------
# Vendor the engine. Structure is preserved exactly so nothing needs path
# rewriting — engine/ is a miniature of the kit and resolves internally.
# ---------------------------------------------------------------------------
echo "▸ Vendoring runtime and gate suite"
mkdir -p "$OUT/engine/src" "$OUT/engine/evals" "$OUT/engine/fixtures"
cp -r "$KIT/src/field_suit"                   "$OUT/engine/src/"
# Gate cases, EXCLUDING operator-scoped ones. A case marked `"scope": "operator"`
# asserts something about the operator's own machine (the intake form, for
# instance) and references paths that are deliberately not vendored here, so it
# cannot be evaluated in the package and would report an ERR the client can
# never clear. Gate 25 in the kit asserts this filter stays correct.
mkdir -p "$OUT/engine/evals/cases"
for case in "$KIT"/evals/cases/*.json; do
  if python3 -c "import json,sys; sys.exit(0 if json.load(open(sys.argv[1])).get('scope')=='operator' else 1)" "$case"; then
    continue
  fi
  cp "$case" "$OUT/engine/evals/cases/"
done
cp    "$KIT/evals/run.py"                     "$OUT/engine/evals/"
cp -r "$KIT/fixtures/synthetic"               "$OUT/engine/fixtures/"
find "$OUT/engine" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

# The self-test fixture is deliberately included. It is what lets the
# organization prove, at any time and without the consultant, that the
# refusals still work. A handover with no way to re-verify is a handover on
# trust.

# ---------------------------------------------------------------------------
# Their configuration
# ---------------------------------------------------------------------------
echo "▸ Writing configuration"
python3 "$KIT/scripts/configure.py" --answers "$ANSWERS" --out "$OUT/config" >/dev/null
mv "$OUT/config/AGENTS.md" "$OUT/AGENTS.md"

cp "$KIT/templates/source-register.md"   "$OUT/docs/"
cp "$KIT/templates/workflow-card.md"     "$OUT/docs/"
cp "$KIT/templates/aar.md"               "$OUT/docs/"
cp "$KIT/docs/board-one-pager.md"        "$OUT/docs/"
cp "$KIT/docs/PRECONDITIONS.md"          "$OUT/docs/"
sed "s/{{ORG}}/$ORG/g" "$KIT/templates/START-HERE.md" > "$OUT/START-HERE.md"

# A starter metric dictionary carrying the rules, not our synthetic numbers.
python3 - "$OUT" <<'PY'
import json, sys, pathlib
out = pathlib.Path(sys.argv[1])
(out / "config" / "metric-dictionary.json").write_text(json.dumps({
  "_about": "Every number in your report, defined exactly once. Fill this in before the first run.",
  "_rules": [
    "source_of_truth is exactly ONE source id from your source register.",
    "extraction_labels are the EXACT bold-total labels as they appear in that file. No fuzzy matching: 'Total participants' must not be allowed to bind to 'Total unique participants served'.",
    "reconciliation_rule halt_on_conflict is the safe default. If two sources disagree the system stops and asks a person, which is usually the most valuable thing it tells you.",
    "A metric with no extraction_labels resolves to nothing and is reported missing. That is intentional."
  ],
  "period": "YYYY-MM",
  "freshness_window_days": 45,
  "owner_confirmation_window_days": 180,
  "metrics": [{
    "id": "example_metric",
    "label": "Total people served",
    "definition": "Write this precisely enough that two staff who disagree can read it and find out who is right.",
    "unit": "people",
    "source_of_truth": "your-source-id",
    "corroborating_sources": [],
    "extraction_labels": ["Total people served"],
    "reconciliation_rule": "halt_on_conflict"
  }]
}, indent=2) + "\n")
PY

# ---------------------------------------------------------------------------
# Two commands. That is the entire interface.
# ---------------------------------------------------------------------------
cat > "$OUT/verify.sh" <<'SH'
#!/usr/bin/env bash
# Prove the safety rules still work. Runs offline: no internet, no API key.
# Run this before you trust a report, after any change, and whenever you want
# reassurance. It takes seconds and it needs nobody's help.
set -euo pipefail
cd "$(dirname "$0")"
python3 engine/evals/run.py "$@"
SH

cat > "$OUT/run.sh" <<'SH'
#!/usr/bin/env bash
# Draft this period's report from the files in sources/.
# Stops and tells you why if anything is missing, stale, or contradictory.
set -euo pipefail
cd "$(dirname "$0")"
PYTHONPATH="engine/src" python3 - "$@" <<'PY'
import json, sys, pathlib
from field_suit.skills.draft_impact_report import run

here = pathlib.Path(".").resolve()
result = run({}, str(here))

print(f"\nOutcome: {result.outcome}")
if result.halt_reason:
    print(f"STOPPED: {result.halt_reason}")
    if result.missing_sources:
        print("  missing source(s): " + ", ".join(result.missing_sources))
    if result.conflict_metric:
        print(f"  '{result.conflict_metric}' disagrees across sources: "
              f"{result.conflict_values}")
    if result.uncited_claims:
        print(f"  figure(s) that trace to no source: "
              f"{[c['value'] for c in result.uncited_claims]}")
    print("\nNo report was written. That is deliberate — a report that quietly\n"
          "dropped a number looks finished, which is worse than none.")
    sys.exit(1)

for f in result.flags:
    print(f"  NOTE  {f['type']}: {f['source_id']} — {f.get('detail','')}")
out = pathlib.Path("reports") / "latest.md"
out.parent.mkdir(exist_ok=True)
out.write_text(result.report)
print(f"\nWritten to {out}")
PY
SH

cat > "$OUT/bootstrap.sh" <<'SH'
#!/usr/bin/env bash
# Check this machine can run the package. Installs nothing.
set -euo pipefail
cd "$(dirname "$0")"
for c in python3.13 python3.12 python3.11 python3.10 python3.9 python3; do
  if command -v "$c" >/dev/null 2>&1; then
    v=$("$c" -c 'import sys;print("%d%02d"%sys.version_info[:2])' 2>/dev/null || echo 0)
    if [ "$v" -ge 309 ]; then
      echo "Python found: $("$c" --version 2>&1)"
      echo "Dependencies to install: none."
      echo
      echo "Next: ./verify.sh    (prove the safety rules work)"
      exit 0
    fi
  fi
done
echo "Needs Python 3.9 or newer. None found." >&2; exit 1
SH
chmod +x "$OUT"/{verify.sh,run.sh,bootstrap.sh}

cat > "$OUT/.gitignore" <<'GI'
runs/
reports/latest.md
__pycache__/
*.pyc
GI

# ---------------------------------------------------------------------------
# Separate repo. Never a fork, never a submodule, never the kit's remote.
# ---------------------------------------------------------------------------
if [ "$DO_GIT" -eq 1 ]; then
  echo "▸ Initialising a separate repository"
  git -C "$OUT" init -q
  git -C "$OUT" symbolic-ref HEAD refs/heads/main
  KIT_REMOTE="$(git -C "$KIT" remote get-url origin 2>/dev/null || echo '')"
  if [ -n "$KIT_REMOTE" ]; then
    mkdir -p "$OUT/.git/hooks"
    cat > "$OUT/.git/hooks/pre-push" <<HOOK
#!/usr/bin/env bash
# This engagement must never be pushed to the kit's remote. A fork or a shared
# remote puts one client's data in a descendant of the reusable kit, which is
# the single failure that ends the practice.
while read -r _ _ _ url; do :; done
remote_url="\$2"
if [ "\$remote_url" = "$KIT_REMOTE" ]; then
  echo "REFUSED: this engagement must not be pushed to the kit's remote." >&2
  echo "  kit remote: $KIT_REMOTE" >&2
  echo "  Use a separate private repository for this client." >&2
  exit 1
fi
exit 0
HOOK
    chmod +x "$OUT/.git/hooks/pre-push"
    echo "  pre-push guard installed (blocks pushing to the kit's remote)"
  fi
fi

echo
echo "▸ Self-test on the finished package (standalone, nothing from the kit)"
( cd "$OUT" && ./verify.sh --no-colour 2>&1 | tail -2 )

cat <<EOF

────────────────────────────────────────────────────────────────
  Standalone package: $OUT

  It does not reference this kit. Copy it anywhere, hand it over,
  delete the kit — it still runs and still refuses the same things.

  Next:
    cd $OUT
    cat START-HERE.md
────────────────────────────────────────────────────────────────
EOF
