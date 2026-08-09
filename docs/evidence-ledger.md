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
| 2026-08-09 | Installed Lua API query | Live `OnClientCommand` query classified local, assigned, and method functions plus event registration; malformed and absent symbols returned typed errors | PASS |
| 2026-08-09 | Isolated Agent Skill package | `npx skills add` installed exactly 18 runtime files with no CI, tests, repository docs, or root README; the installed helper completed live `OnServerCommand`, malformed-input, and help QA | PASS |
| 2026-08-09 | Guarded scaffold writes | Every generated destination exercised the shared policy guard; live plan/apply created five files, reapply returned `destination_exists`, and generated server Lua retained untrusted-client guidance | PASS |
| 2026-08-09 | Manifest-driven API query | Explicit-manifest and zero-path discovery returned the current build and branch with live `ISPanel`/`OnClientCommand` evidence; conflicting location arguments exited 2 | PASS |
| 2026-08-09 | Multiplayer mod preflight | A generated mod passed with no issues; an incomplete fixture returned server Lua and command-boundary findings with exit 1; a missing root returned typed exit 2 | PASS |
| 2026-08-09 | Cross-platform quality matrix | Ubuntu and Windows both passed format, lint, type check, 25 tests, and nested Agent Skill validation | PASS |
| 2026-08-09 | Multi-symbol evidence report | A live three-symbol report completed under one build/branch; a partial report retained found evidence and marked the missing claim with exit 1; invalid input exited 2 | PASS |

## Residual boundary

The mutation guard blocks accidental outside-root writes, stale plans, overwrites, static symlink/junction/reparse escapes, and known protected PZ paths. Python path checks cannot eliminate a hostile concurrent ancestor-swap race on Windows. Hard adversarial isolation requires an ACL-protected workspace, VM, or container.
