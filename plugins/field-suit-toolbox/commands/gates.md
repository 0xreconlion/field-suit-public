---
description: Run the offline gate suite and report the result verbatim
---
```
python3 evals/run.py
```

Report the actual output, not a summary of it. State the pass count and the
suite name.

If any gate fails, quote its failure line. Do not characterise a failing
suite as "mostly passing" — the gates are binary and a partial pass is a
fail.

The offline suite runs with no network and no API key. It is **not** evidence
of a live pass. If a live result is wanted, that is `--live`, reported
separately.
