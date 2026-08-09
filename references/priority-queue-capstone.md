# Priority admission queue capstone

This scenario evaluates whether an agent can combine Build 42 discovery, UI, networking, authority, reconnect handling, and monetization-neutral access control without inventing APIs.

## Required behavior

- Server connection capacity: 40.
- Active-world capacity: 32.
- Connections 33–40 remain queued and cannot become active until admitted.
- Two FIFO lanes: priority supporters first, then standard users.
- Priority affects access order only; it grants no items, stats, spawn advantage, or persistent gameplay benefit.
- When an active player disconnects, the server admits the next eligible queued player.
- Administrators use a separately authorized bypass.
- Queue position survives a short reconnect grace period keyed by a server-observed stable identity.
- A client that hides or modifies the overlay still cannot admit itself.

## Authoritative state machine

```text
CONNECTED -> QUEUED -> ADMITTED -> DISCONNECTED
                |          |
                +----------+-- server decision only
```

The server owns:

- active and queued membership;
- lane and FIFO sequence;
- admission tokens/generation;
- disconnect promotion;
- reconnect grace;
- administrator exceptions.

The client owns only presentation and requests for the latest server-confirmed queue snapshot.

## Discovery gate

The desired UX intercepts the flow after “press any key” but before ordinary play. Do not name an interception hook until it is found in the installed Build 42 source.

If no supported pre-spawn Lua hook exists, the implementation must:

1. document the limitation;
2. identify the earliest verified client UI/world event;
3. use a server-enforced limbo or admission state so bypassing the overlay cannot grant play access;
4. test that fallback with two real clients and a dedicated server.

## Required adversarial tests

- 32 active users plus standard and priority arrivals;
- simultaneous disconnect and two promotion candidates;
- priority user reconnect during grace;
- forged client command claiming supporter/admin state;
- hidden or destroyed overlay;
- duplicate command and stale queue generation;
- server restart with queued clients;
- capacity lowered while active count exceeds the new limit;
- malformed or missing queue payload.

Passing UI tests alone is insufficient. Admission must be proven from the server's observable state.
