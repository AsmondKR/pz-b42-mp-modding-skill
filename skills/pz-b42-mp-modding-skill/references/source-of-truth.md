# Build 42 source-of-truth policy

JSON discovery successes and failures declare top-level `schema_version: 1`.

Project Zomboid modding documentation is incomplete and often mixes Build 41 with Build 42. Every volatile API claim needs provenance.

## Evidence ladder

1. **Installed game files** matching the user's exact Steam build.
2. **Current official Indie Stone material** applicable to that build.
3. **Version-matched generated API docs or type stubs**, such as Umbrella.
4. **Maintained community implementations** tested on the same build.
5. General model knowledge is useful for search terms, never as final proof.

## Verified surface examples

The repository baseline verified the following relative files and symbols against a local Build 42 installation. Agents must rediscover the active branch and build ID on the current user's machine and must not publish absolute local paths.

| Surface | Local evidence |
| --- | --- |
| Client request received by server | `media/lua/server/ClientCommands.lua`: `ClientCommands.OnClientCommand`; registered with `Events.OnClientCommand.Add` |
| Server message received by client | `media/lua/client/ServerCommands.lua`: `ServerCommands.OnServerCommand`; registered with `Events.OnServerCommand.Add` |
| Client UI base | `media/lua/client/ISUI/ISPanel.lua`: `ISPanel = ISUIElement:derive("ISPanel")` |
| Server permission revalidation example | `media/lua/server/ClientCommands.lua`: debug commands call `player:getRole():hasCapability(...)` before state changes |

The vanilla dispatchers route by `module` and `command`. Their existence proves the event boundary; it does not make every vanilla handler a safe example.

## Unverified until discovered

Do not assert any of these from memory:

- a Lua hook before character/world spawn;
- a native login queue API;
- a stable player-connect/disconnect callback with a particular signature;
- automatic synchronization of arbitrary mod data;
- B41 recipe, item, or timed-action signatures.

An unversioned B41 mod layout must be migrated to `Contents/mods/<id>/42` before Build 42 validation. Moving files is only a packaging change; it does not validate B41 Lua APIs.

Search installed source and record the exact relative file, line, symbol, and build. Use the read-only query workflow in `api-query.md` when the bundled helper is available. If no evidence is found, describe the limitation and design a tested fallback rather than inventing an API.

## External references

- Agent Skills specification: https://agentskills.io/specification
- Vanilla Lua mirror: https://github.com/Project-Zomboid-Community-Modding/ProjectZomboid-Vanilla-Lua
- Umbrella type stubs: https://github.com/PZ-Umbrella/Umbrella
- Archived official B42 MP guides: https://github.com/PZ-Wiki-Modding/Archive.Project-Zomboid-Modding/tree/main/TIS%20guides/B42%20unstable%20MP
