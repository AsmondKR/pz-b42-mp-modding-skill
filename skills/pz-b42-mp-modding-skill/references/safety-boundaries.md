# Safety boundaries

## Default state

All discovery is read-only. A write is allowed only when every condition below holds:

1. The user approved a dedicated workspace.
2. `.pz-skill-policy.json` names that canonical workspace.
3. The destination resolves inside an allowed output root.
4. The destination is outside every forbidden root.
5. No destination component escapes through a symlink, junction, or reparse point.
6. The destination does not already exist.
7. The apply operation matches an unchanged, previously reviewed dry-run manifest.

The scaffolder re-authorizes each generated file after creating its parent directories and immediately before exclusive file creation. A valid plan does not bypass the shared path, forbidden-root, Windows-name, symlink, junction, or reparse checks.

## Unconditional forbidden targets

- Project Zomboid installation directories
- Steam Workshop subscription directories
- `Zomboid/Saves`
- active server configuration and save directories
- credential, token, cookie, and SSH key locations
- third-party mod source trees not copied into the approved workspace

## External effects

Workshop publishing, GitHub pushes, server restarts, deployment, payment-provider updates, and any other external write require separate explicit approval. They are not performed by bundled mutation scripts.

## Enforcement limit

These rules bind compatible agents and are technically enforced by bundled scripts. They cannot prevent an unrelated tool or hostile process from writing elsewhere. Use a read-only source mount plus a separate writable output mount for hard isolation.
