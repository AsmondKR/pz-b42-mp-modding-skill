# Multiplayer authority patterns

## Execution boundaries

### Client

- render UI and overlays;
- collect local input;
- request actions from the server;
- display server-confirmed state.

The client must not grant admission, rewards, permissions, inventory, persistent state, or donor priority.

### Server

- authenticate the player object delivered by the command event;
- validate permissions and current world state;
- own queue, session, persistence, and admission state;
- apply mutations and send minimal confirmed results to clients.

### Shared

Use shared code only for constants, command names, serialization shapes, and pure helpers that are safe in both runtimes. Do not put authority-bearing state in shared globals.

## Verified command shape

Installed Build 42 vanilla Lua registers:

```lua
Events.OnClientCommand.Add(ClientCommands.OnClientCommand)
Events.OnServerCommand.Add(ServerCommands.OnServerCommand)
```

A mod should namespace commands with a unique module string and dispatch explicitly:

```lua
local MODULE = "MyMod"

local function onClientCommand(module, command, player, args)
    if module ~= MODULE then return end
    if command == "requestAction" then
        -- Revalidate player, permission, ownership, range, and current state here.
    end
end

Events.OnClientCommand.Add(onClientCommand)
```

Client-supplied username, access level, donor status, item ownership, coordinates, counts, and timestamps are assertions—not proof.

## Command payload contract

Keep network payloads to:

- strings;
- booleans;
- finite numbers;
- arrays/tables composed of the same primitives.

Send stable identifiers rather than Java/Lua object references. Resolve objects on the authoritative side and reject missing, stale, mismatched, or out-of-range identifiers.

## Persistence

Before selecting `modData`, files, database state, or server globals:

1. identify the owner of the state;
2. identify its required lifetime;
3. verify the save/load and synchronization API on the installed build;
4. define migration and corruption behavior;
5. test reconnect and server restart on a dedicated server.

Do not claim arbitrary `modData` synchronizes automatically without exact evidence.

## Review checklist

- Can a modified client grant itself the outcome?
- Does the server use the event-provided player instead of a claimed username?
- Are permissions checked at the mutation point?
- Can the command be replayed or reordered?
- Are identifiers stale-safe?
- Is every response derived from server state?
- Does reconnect reconstruct state without trusting the client?
