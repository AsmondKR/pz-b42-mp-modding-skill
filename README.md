# PZ Build 42 Multiplayer Modding Skill

An Agent Skills-compatible package that helps AI coding agents build Project Zomboid Build 42 multiplayer mods without relying on stale Build 41 knowledge.

## What it gives an agent

- local Steam build and vanilla Lua discovery;
- an evidence hierarchy that prevents invented API calls;
- client/server/shared authority rules;
- create-only B42 multiplayer mod scaffolding;
- dry-run plans tied to an approved workspace policy;
- references for networking, persistence, UI, reconnects, and permissions;
- a 32-active/40-connected priority-admission queue capstone;
- deterministic unit tests and real CLI QA.

The generated Lua is intentionally minimal. It establishes the correct B42 boundaries and leaves feature-specific state changes behind explicit server validation.

## Quick start

Clone the repository and expose its directory through your coding agent's Agent Skills directory.

Validate the installed game:

```powershell
python scripts/discover_pz.py --json
```

Create a dedicated workspace and `.pz-skill-policy.json`:

```json
{
  "version": 1,
  "workspace_root": "C:\\absolute\\path\\to\\workspace",
  "allowed_output_roots": ["generated"],
  "forbidden_roots": []
}
```

The `generated` directory must already exist. Produce and review a scaffold plan:

```powershell
python scripts/scaffold_mod.py plan `
  --policy C:\absolute\path\to\workspace\.pz-skill-policy.json `
  --mod-id AdmissionQueue `
  --name "Admission Queue" `
  --author "Your Name" `
  --output-root generated
```

Save the reviewed JSON and apply it:

```powershell
python scripts/scaffold_mod.py apply `
  --policy C:\absolute\path\to\workspace\.pz-skill-policy.json `
  --plan C:\absolute\path\to\reviewed-plan.json
```

## Repository guide

- `SKILL.md`: agent workflow and trigger contract
- `references/source-of-truth.md`: evidence policy and verified local surfaces
- `references/multiplayer-authority.md`: server-authoritative command design
- `references/priority-queue-capstone.md`: queue requirements and adversarial QA
- `references/safety-boundaries.md`: write authorization limits
- `scripts/discover_pz.py`: read-only installation discovery
- `scripts/scaffold_mod.py`: plan/apply B42 MP scaffold

## Safety boundary

Bundled tools never modify Project Zomboid installations, subscribed Workshop content, saves, credentials, active server configuration, or third-party mods. Existing output roots are allowed, but a mod root must not already exist.

A skill cannot sandbox an arbitrary process. The path guard prevents cooperative mistakes and static link escapes; hard protection against a hostile concurrent process requires an ACL-protected workspace, VM, or container with read-only source mounts.

## Current verified baseline

The first release was exercised against the Steam `public` branch, build ID `24574865`, with local vanilla evidence for:

- `Events.OnClientCommand` on the server;
- `Events.OnServerCommand` on the client;
- `ISPanel` client UI inheritance.

Agents must rediscover the user's installed build rather than assuming this baseline is current.

## License

MIT. Project Zomboid and its assets are owned by The Indie Stone. This repository does not redistribute game code or assets.
