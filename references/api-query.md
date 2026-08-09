# Installed Lua symbol evidence

Use the query helper only after discovery has identified the current Project Zomboid installation root.

```powershell
python scripts/query_pz_api.py `
  --install-root "C:\path\to\ProjectZomboid" `
  --symbol OnClientCommand `
  --json
```

The helper is read-only. It scans `media/lua/**/*.lua`, ignores line comments, matches exact Lua identifiers, and returns deterministic evidence sorted by relative path and line number.

## Evidence kinds

- `function`: a matching `function Owner.symbol(...)` or `function Owner:symbol(...)` definition
- `event_registration`: an exact `Events.Symbol.Add(handler)` registration
- `class_derivation`: a matching `Child = Parent:derive("Child")` declaration
- `reference`: an exact identifier occurrence that is not one of the stronger forms above

Treat a registration as proof that the event name is used by the installed build, not proof that every handler signature or execution context is safe. Read the surrounding source before implementing behavior.

## Required recording

For each API claim, retain:

1. the discovered build ID and branch;
2. the relative Lua path;
3. the one-based line number;
4. the evidence kind and normalized signature;
5. any remaining ambiguity about arguments or client/server context.

If the helper returns `symbol_not_found`, stop and report missing evidence. Do not silently substitute a Build 41 event or a remembered signature.

## Boundaries

- Query a single exact symbol at a time.
- Use `--limit` to bound common references; the default is 100.
- Invalid identifiers and missing Lua roots return typed JSON errors without creating files.
- Results are source locations, not generated API documentation.
