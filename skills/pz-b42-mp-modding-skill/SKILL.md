---
name: pz-b42-mp-modding-skill
description: Build, debug, validate, and package scalable, trust-aware Project Zomboid Build 42 multiplayer mods and high-quality image assets, Blender models, and FBX exports. Use for B42 client/server/shared Lua, networking, persistence, UI, dedicated servers, Workshop packaging, art direction, Codex image prompts, Blender-authored assets, or FBX validation. Read-only by default; never modify game installs, Workshop subscriptions, saves, active server configuration, credentials, or third-party mods.
license: MIT
compatibility: Works as an Agent Skill on supported coding agents. Optional bundled helpers use Python 3.11+. Blender asset inspection and FBX export require Blender 5.1+. Live multiplayer QA requires a local Project Zomboid Build 42 client or dedicated server.
metadata:
  author: pz-b42-mp-modding-skill contributors
  version: 0.17.0
---

# Project Zomboid Build 42 Multiplayer Modding

Build against verified Build 42 evidence, not model memory.
Machine-readable discovery, query, report, and validation documents declare `schema_version: 1`.

## Mandatory workflow

1. Inspect the local Steam manifest and vanilla Lua to record the installed build plus evidence roots. Use `scripts/discover_pz.py` when Python 3.11+ is available.
2. Query installed vanilla Lua with `scripts/query_pz_api.py --symbol <name>` before naming one event, class, or function. For multiple claims, run `scripts/report_pz_api.py` with repeated `--symbol` arguments and resolve every missing result. Record the returned build, branch, relative file, line, kind, and signature.
3. Classify every mod-owned state as client-local, server-committed, or hybrid before editing, including its update frequency and affected players.
4. Choose the least-centralized model that preserves integrity. Server-commit permission, progression, economy, and shared persistent invariants; keep presentation, private ephemeral state, and deterministic derived data off the wire.
5. Treat integrity-sensitive client commands as untrusted requests. Revalidate identity, permission, ownership, relevant range and world state, and replay safety at the server commit boundary without reproducing harmless client simulation.
6. Use only serialization-safe primitive values and tables across command boundaries.
7. Scaffold new work in an approved workspace; never retrofit a B41 layout by assumption.
8. Run `scripts/validate_mod.py` against the new mod root, resolve every structural issue, then exercise integrity and load behavior on a dedicated server at a representative player count and command rate.

## Asset production workflow

For images, models, textures, or FBX work:

1. Discover the installed Build 42 build, then probe an exact same-role vanilla FBX with `scripts/plan_pz_fbx_reference.py`. For Build `24574865`, read `references/build-24574865-fbx-reference.md`; for any other build, regenerate observations instead of inheriting its values.
2. Define one visual world and one approved asset brief with `references/asset-art-direction.md`.
3. Produce copy/paste prompts with `references/codex-image-prompts.md`; the user generates images manually in the Codex app.
4. Treat every generated image or mesh as an untrusted candidate. Record provenance and keep concept, orthographic, icon, and texture-reference roles distinct.
5. Keep Blender authoritative for geometry, topology, UVs, materials, rigging, and FBX output. Never ship a prompt-generated mesh directly.
6. Create one workspace-bound asset manifest, then run `scripts/validate_asset_manifest.py --policy <policy> --manifest <asset.json>`.
7. Generate a hashed command with `scripts/plan_blender_asset.py validate --policy <policy> --manifest <asset.json>`. Review and execute that exact command; resolve every `PZ_ASSET_RESULT` issue.
8. After human geometry and surface approval, generate and execute the `export` plan. The Blender script refuses weak scenes, creates no overwrite, reimports the FBX, and reports semantic drift.
9. Wire the exact output hash through evidence-backed Build 42 paths, then perform in-game visual QA for every declared single-player and multiplayer context.

## Progressive references

Read only the references required by the task:

| Task | Reference |
| --- | --- |
| Decide whether an API claim is usable | `references/source-of-truth.md` |
| Query installed Lua symbol evidence | `references/api-query.md` |
| Collect several API claims together | `references/evidence-report.md` |
| Preflight a multiplayer mod package | `references/mod-validation.md` |
| Split client/server/shared code | `references/multiplayer-authority.md` |
| Define a coherent mod asset set | `references/asset-art-direction.md` |
| Write Codex app image prompts | `references/codex-image-prompts.md` |
| Establish FBX size and direction evidence | `references/build-24574865-fbx-reference.md` |
| Validate and export Blender FBX assets | `references/blender-fbx-pipeline.md` |
| Perform any write | `references/safety-boundaries.md` |

## Mutation safety

- Discovery is read-only.
- Never write to the game installation, subscribed Workshop content, saves, logs, credentials, or active server directories.
- Never overwrite or delete an existing file through bundled scripts.
- Route every generated scaffold file through the shared destination policy guard.
- Never follow a symlink, junction, or reparse point outside the approved workspace.
- Refuse linked or reparse-point Lua sources during evidence queries.
- Authorize every Blender output through the same workspace policy immediately before export.
- Never overwrite an FBX or silently repair, decimate, merge, unwrap, rig, or replace an authored asset.
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

This skill covers Build 42 multiplayer Lua mods, networking, UI, persistence, permissions, reconnect handling, dedicated-server QA, Workshop packaging, image-prompt handoff, Blender-authored models, texture references, and FBX quality gates. It does not cover Java core mods, maps, automatic image generation, automatic production-quality 3D generation, animation authoring, or B41 compatibility.

## Stop conditions

Stop and report the missing evidence instead of guessing when:

- the installed build cannot be identified;
- a requested event or method is absent from installed Lua and version-matched API sources;
- client/server execution context is ambiguous;
- authority classification, synchronization frequency, or expected server cost is undefined;
- dedicated-server QA cannot be run for a behavioral MP change;
- a required asset-specific Build 42 constraint is unknown;
- the installed Build ID or reference hash differs from the selected FBX observation;
- a human has not approved the art, geometry, surface, or in-game visual gate;
- Blender validation or FBX round-trip comparison reports an issue;
- a destination is outside the approved workspace or already exists.
