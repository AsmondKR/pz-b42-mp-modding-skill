# Installed Lua symbol evidence

The query helper can discover the conventional Steam manifest itself or resolve one explicit manifest. Pass `--install-root` only when the installation is outside those Steam locations.

```powershell
python scripts/query_pz_api.py `
  --manifest "C:\path\to\steamapps\appmanifest_108600.acf" `
  --symbol OnClientCommand `
  --json
```

The helper is read-only. It verifies the manifest through the discovery module, scans `media/lua/**/*.lua`, ignores line comments, matches exact Lua identifiers, and returns deterministic evidence sorted by relative path and line number. JSON output includes the resolved build ID and branch when discovery was used.

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
- Use at most one of `--manifest` and `--install-root`; omitting both triggers conventional Steam discovery.
- Use `--limit` to bound common references; the default is 100.
- Invalid identifiers, missing Lua roots, and linked/reparse query paths return typed JSON errors without creating files.
- A linked installation root, Lua root, directory entry, or Lua file stops the query with `lua_path_linked`; no partial evidence is returned.
- Results are source locations, not generated API documentation.
