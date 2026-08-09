# Multi-symbol Build evidence report

Use the batch report when a design depends on several installed Lua claims.

```powershell
python scripts/report_pz_api.py `
  --symbol OnClientCommand `
  --symbol OnServerCommand `
  --symbol ISPanel `
  --json
```

The command resolves one Build 42 installation, preserves input symbol order, and evaluates every symbol under the same build ID and branch. Matches inside each symbol use the ranking defined in `api-query.md` before the per-symbol limit is applied.

Exit codes:

- `0`: every requested symbol has at least one exact source match
- `1`: the report is valid but one or more symbols are explicitly `found: false`
- `2`: discovery, identifier, limit, Lua-root, or linked-path validation failed

## Agent workflow

1. List every event, function, and class the planned mod depends on.
2. Request them in one report with repeated `--symbol`.
3. Keep the shared build and branch provenance with the plan.
4. For each found symbol, inspect the strongest returned locations and surrounding source.
5. Remove, replace, or investigate every missing symbol before writing code.

The report does not turn references into signatures and does not prove an API is valid in every client/server context. Apply the evidence rules in `source-of-truth.md` and the single-symbol interpretation rules in `api-query.md`.
