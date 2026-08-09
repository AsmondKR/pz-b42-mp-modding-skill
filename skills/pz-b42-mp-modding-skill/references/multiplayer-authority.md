# Multiplayer authority and load patterns

Server authority is a trust-boundary tool, not a default location for all logic. Choose the least-centralized design that prevents profitable forgery and cross-player disagreement.

## Authority decision

Classify each state before implementation:

| State class | Examples | Model | Network behavior |
| --- | --- | --- | --- |
| Local presentation | UI drafts, overlays, filters, input, animation cues | Client-local | No network traffic |
| Deterministic derived data | Labels or summaries computed from already-known state | Compute at each consumer | Do not replicate a second copy |
| Private ephemeral state | Selections, previews, local caches with no durable outcome | Client-local | No network traffic |
| Reversible latency-sensitive action | A preview or prediction whose result can be replaced cleanly | Hybrid | Client predicts; server reconciles only the meaningful outcome |
| Permission, progression, economy, or admission | Access, rewards, inventory grants, XP, currency, unlocks | Server-committed | Validate once at mutation; send a targeted result |
| Shared persistent world state | Mod-owned state that survives or affects multiple players | Server-committed | Persist first; send relevant deltas to affected players |
| Shared ephemeral signal | Non-authoritative presence or cosmetic cues | Bounded relay when needed | Stamp sender identity from the event-provided player; sanitize, rate-limit, coalesce, and target |

Rule of thumb: server-commit what a modified client could profit from forging or what multiple players must agree on. Keep everything else off the server and off the wire.

Hybrid does not mean shared authority over the committed result. Prediction is presentation-only, the server verdict replaces it, and irreversible grants are never predicted as final.

## Execution boundaries

### Client

- render UI, overlays, previews, and other presentation;
- collect input and maintain harmless private ephemeral state;
- derive display-only data from state it already has;
- predict reversible feedback when latency would otherwise be visible;
- request only integrity-sensitive mutations from the server.

The client must not commit admission, rewards, permissions, inventory grants, progression, shared persistent state, or other profitable outcomes.

### Server

- authenticate the player object delivered by the command event;
- validate only the invariants required for the requested commit;
- commit security-sensitive or shared persistent mutations;
- reconcile reversible predictions when required;
- send minimal deltas only to affected clients.

Do not move local presentation or full client simulation to the server merely because a feature is multiplayer.

### Shared

Use shared code only for constants, command names, serialization shapes, and pure helpers that are safe in both runtimes. Do not put authority-bearing state in shared globals.

## Server workload budget

- Prefer event-driven work over frequent timers or global scans.
- Never scan every player or broad world state on every frame for a mod-owned feature.
- If periodic work is unavoidable, use a bounded cadence and process an incremental slice.
- Reuse vanilla synchronization and authority only when installed-build evidence shows it enforces the invariant. Record that evidence like any API claim; do not duplicate verified protection in mod Lua.
- Validate at the meaningful mutation or cash-out boundary instead of mirroring every intermediate client step.
- Filter recipients by ownership, relevance, range, or affected state before sending.
- Coalesce rapid changes and send identifiers or deltas instead of repeated full snapshots.
- Bound per-player request rate, pending work, payload size, and server-originated update frequency.
- Return an explicit rejection for a throttled integrity-sensitive request; do not create silent ghost state.
- Bound and stagger join, reconnect, and initial synchronization so a reconnect wave cannot trigger simultaneous full-state work.
- Load-test with a representative player count and action rate. Observe server responsiveness, command volume, payload size, and queue growth.

Server cost should track meaningful shared mutations, not client frame rate multiplied by player count.

## Verified command shape

Installed Build 42 vanilla Lua registers:

```lua
Events.OnClientCommand.Add(ClientCommands.OnClientCommand)
Events.OnServerCommand.Add(ServerCommands.OnServerCommand)
```

When a server commit is required, namespace commands with a unique module string and dispatch explicitly:

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

Client-supplied username, access level, donor status, item ownership, coordinates, counts, and timestamps are always assertions—not proof. Committed outcomes require full invariant validation. Relays still require sender attribution from the event-provided player, payload sanitization, relevance filtering, and rate controls.

## Command payload contract

Keep network payloads to:

- strings;
- booleans;
- finite numbers;
- arrays/tables composed of the same primitives.

Send stable identifiers rather than Java/Lua object references. Resolve objects at the commit boundary and reject missing, stale, mismatched, or out-of-range identifiers. Do not send data that the receiving side can derive safely from state it already has.

## Persistence

Before selecting `modData`, files, database state, or server globals:

1. identify the owner of the state;
2. identify its required lifetime;
3. verify the save/load and synchronization API on the installed build;
4. define migration and corruption behavior;
5. test reconnect and server restart on a dedicated server.

Do not claim arbitrary `modData` synchronizes automatically without exact evidence.

## Review checklist

- Could this state remain client-local or be derived without synchronization?
- Can a modified client grant itself the outcome?
- Which exact invariant requires a server commit?
- Does the server use the event-provided player instead of a claimed username?
- Are permissions checked at the mutation point?
- Can the command be replayed or reordered?
- Are identifiers stale-safe?
- Is prediction reversible and clearly replaced by the server verdict?
- Does server work run per meaningful event rather than per player per frame?
- Are recipients filtered and rapid changes coalesced?
- Are request rate, pending work, payload size, and update cadence bounded?
- Does the design avoid duplicating vanilla synchronization?
- Is the claimed vanilla enforcement verified against the installed build?
- Are join, reconnect, and initial-sync bursts bounded and staggered?
- Does reconnect reconstruct state without trusting the client?
- Has load behavior been exercised at a representative player count?
