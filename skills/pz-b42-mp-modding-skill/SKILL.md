---
name: pz-b42-mp-modding-skill
description: Build, debug, validate, and package server-authoritative Project Zomboid Build 42 multiplayer mods. Use for B42 client/server/shared Lua, networking, persistence, UI overlays, dedicated servers, Workshop packaging, reconnect handling, permissions, or migrating multiplayer mods from B41. Read-only by default; never modify game installs, Workshop subscriptions, saves, active server configuration, credentials, or third-party mods.
license: MIT
compatibility: Works as an instruction-only Agent Skill on supported coding agents. Optional bundled helpers use Python 3.11+. Live multiplayer QA requires a local Project Zomboid Build 42 client or dedicated server.
metadata:
  author: pz-b42-mp-modding-skill contributors
  version: 0.11.0
---

# Project Zomboid Build 42 Multiplayer Modding

Build against verified Build 42 evidence, not model memory.

## Mandatory workflow

1. Inspect the local Steam manifest and vanilla Lua to record the installed build plus evidence roots. Use `scripts/discover_pz.py` when Python 3.11+ is available.
2. Query installed vanilla Lua with `scripts/query_pz_api.py --symbol <name>` before naming one event, class, or function. For multiple claims, run `scripts/report_pz_api.py` with repeated `--symbol` arguments and resolve every missing result. Record the returned build, branch, relative file, line, kind, and signature.
3. Declare client, server, and shared responsibilities before editing.
4. Keep permissions, persistence, rewards, and state changes server-authoritative.
5. Treat client commands as untrusted requests. Revalidate identity, permission, range, ownership, and current state on the server.
6. Use only serialization-safe primitive values and tables across command boundaries.
7. Scaffold new work in an approved workspace; never retrofit a B41 layout by assumption.
8. Run `scripts/validate_mod.py` against the new mod root, resolve every structural issue, then exercise the feature on a dedicated server.

## Progressive references

Read only the references required by the task:

| Task | Reference |
| --- | --- |
| Decide whether an API claim is usable | `references/source-of-truth.md` |
| Query installed Lua symbol evidence | `references/api-query.md` |
| Collect several API claims together | `references/evidence-report.md` |
| Preflight a multiplayer mod package | `references/mod-validation.md` |
| Split client/server/shared code | `references/multiplayer-authority.md` |
| Perform any write | `references/safety-boundaries.md` |

## Mutation safety

- Discovery is read-only.
- Never write to the game installation, subscribed Workshop content, saves, logs, credentials, or active server directories.
- Never overwrite or delete an existing file through bundled scripts.
- Route every generated scaffold file through the shared destination policy guard.
- Never follow a symlink, junction, or reparse point outside the approved workspace.
- Never publish, deploy, restart a server, or call an external write API without separate explicit user approval.
- When existing code must change, produce a reviewable patch and wait for approval before applying it.

Read `references/safety-boundaries.md` before any write.

## Evidence order

1. Installed Build 42 game files and vanilla Lua.
2. Current official Indie Stone material.
3. Version-matched generated API documentation or type stubs.
4. Maintained community implementations.
5. Model memory is never sufficient on its own.

## Scope

This skill covers Build 42 multiplayer Lua mods, networking, UI, persistence, permissions, reconnect handling, dedicated-server QA, and Workshop packaging. It does not cover Java core mods, maps, models, textures, animations, or B41 compatibility.

## Stop conditions

Stop and report the missing evidence instead of guessing when:

- the installed build cannot be identified;
- a requested event or method is absent from installed Lua and version-matched API sources;
- client/server execution context is ambiguous;
- dedicated-server QA cannot be run for a behavioral MP change;
- a destination is outside the approved workspace or already exists.
