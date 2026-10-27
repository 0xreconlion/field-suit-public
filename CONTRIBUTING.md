# Contributing

Keep the runtime dependency-free and the test corpus synthetic. New capabilities need a known-pass and known-fail case, and changes must preserve deny-by-default behavior.

```console
python3 evals/run.py
python3 scripts/verify-public-export.py
```

