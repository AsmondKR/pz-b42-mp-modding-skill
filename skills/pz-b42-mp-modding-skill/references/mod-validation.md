# Build 42 multiplayer mod preflight

Run the read-only validator on the generated mod root before dedicated-server QA.

```powershell
python scripts/validate_mod.py `
  --mod-root "C:\approved-workspace\generated\ExampleMod" `
  --json
```

Exit codes:

- `0`: no structural issue found
- `1`: validation completed and reported one or more issues
- `2`: the requested root is missing, not a directory, or is itself a link/reparse point

## Checked boundaries

- `workshop.txt` exists at the package root.
- `workshop.txt` includes version, Workshop ID, title, description, visibility, and tags.
- Workshop tags include both `Build 42` and `Multiplayer`.
- `Contents/mods` contains exactly one mod directory.
- the Build 42 directory is `Contents/mods/<id>/42`.
- `mod.info` includes name, ID, author, and description; its `id` matches the directory name.
- client, server, and shared Lua each contain at least one `.lua` file.
- client Lua registers `Events.OnServerCommand.Add`.
- server Lua registers `Events.OnClientCommand.Add`.
- no scanned package path is a symlink, junction, or reparse point.

## Deliberate limits

This is a package and command-boundary preflight, not a proof of multiplayer authority. A passing result does not prove that:

- command arguments are validated correctly;
- permissions are checked at the mutation point;
- persistence and reconnect behavior are correct;
- client-visible state came from the server;
- the mod works on a dedicated server.

After preflight passes, review `multiplayer-authority.md` and run the feature with a dedicated server and real clients.
