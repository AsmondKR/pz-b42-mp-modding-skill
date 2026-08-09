# Evidence ledger

Only observed evidence is recorded here.

| Date | Increment | Evidence | Result |
| --- | --- | --- | --- |
| 2026-08-09 | Initial agent-skill release | `agentskills validate .` | PASS |
| 2026-08-09 | Python behavior | `pytest`: 15 passed | PASS |
| 2026-08-09 | Code quality | `ruff format --check`, `ruff check`, `basedpyright`: clean | PASS |
| 2026-08-09 | Local B42 discovery | Current Steam build; command dispatchers and `ISPanel` found | PASS |
| 2026-08-09 | B42 MP scaffold | Planned and created a client/server/shared example fixture | PASS |
| 2026-08-09 | Refusal behavior | Existing mod root and malformed mod ID returned typed JSON errors with exit code 2 | PASS |
| 2026-08-09 | npm-based installation | `npx skills add` copied skill version `0.2.0` into an isolated Codex project | PASS |
| 2026-08-09 | Public-content privacy audit | No tracked queue scenario, local absolute path, or private fixture identifier remained | PASS |

## Residual boundary

The mutation guard blocks accidental outside-root writes, stale plans, overwrites, static symlink/junction/reparse escapes, and known protected PZ paths. Python path checks cannot eliminate a hostile concurrent ancestor-swap race on Windows. Hard adversarial isolation requires an ACL-protected workspace, VM, or container.
