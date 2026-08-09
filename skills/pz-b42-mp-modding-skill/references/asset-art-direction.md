# Asset art direction

Use this reference to define the visual world for Project Zomboid mod assets before
requesting images or opening Blender. It adapts the decision discipline of
[Impeccable](https://github.com/pbakaus/impeccable) to game assets; it does not copy
frontend rules into the game.

This workflow creates briefs, comparison evidence, and handoffs. It does not generate
images, approve art, or prove that an asset loads in Build 42.

## Evidence boundary

- Inspect installed Build 42 assets before stating a required size, path, naming rule,
  material behavior, skeleton, transform, or budget.
- Label a team-selected limit as `project_policy`, not as a game requirement.
- Label a required unresolved game fact as `unknown` and stop that promotion path.
- Never infer a universal rule from one vanilla asset.
- Record only observations and hashes; do not redistribute vanilla assets.

## One visual world

Create one durable art-direction record for the mod. It must define:

1. place, era, owner, and use history;
2. material and weathering language;
3. silhouette and value priorities at the target game view;
4. palette references from inspected vanilla neighbors;
5. deliberate differences from those references;
6. forbidden motifs and common generator artifacts;
7. comparison contexts: inventory, world, worn, held, UI, or vehicle;
8. the human who owns final visual approval.

Do not use adjectives such as "cinematic" or "premium" without observable visual
choices. Name real objects, materials, construction, damage, and viewing conditions.

## Asset brief

Keep one brief per asset. Values marked `unknown` remain blockers when they are needed
for the selected profile.

```yaml
schema_version: 1
asset_id: example_roadside_toolbox
asset_class: model
profile: static_model
world_context: rural Kentucky roadside repair equipment
real_referent: powder-coated steel toolbox with a repaired latch
usage_contexts: [world, inventory_icon]
dimensions_m: unknown
vanilla_comparisons: []
silhouette:
  recognition_cues: [raised handle, rectangular body, offset latch]
  forbidden: [hero framing, decorative spikes]
materials:
  - role: body
    description: worn powder-coated steel
image_outputs: [concept_sheet, orthographic_turnaround, item_icon]
project_policy:
  triangle_budget: 2400
provenance_ref: art/provenance.yaml#example_roadside_toolbox
review:
  brief: pending
  comp: pending
  finish: pending
```

## Comp-led decisions

Resolve large decisions before detail:

1. Produce at least three meaningfully different silhouettes.
2. Compare them at the final viewing size and declared usage context.
3. Establish value grouping before color and surface detail.
4. Place candidates beside inspected vanilla references at the same scale.
5. Have a named human select, revise, or reject the direction.
6. Preserve rejected directions and their reasons to prevent accidental recycling.

Generated images are candidates. A technically valid result does not become approved
because it is polished.

## Separate machine checks from art judgment

### Objective checks

An agent may pass or fail these when it has inspected the artifact:

- expected file exists inside the authorized workspace;
- dimensions, channels, and declared format match the brief;
- required source and provenance records exist;
- model transforms and project budgets satisfy the manifest;
- required comparison views were produced;
- export and runtime evidence refer to the same artifact hash.

### Human gates

An agent may prepare evidence but cannot approve:

- silhouette reads at the real game scale;
- material and wear communicate the intended object;
- the asset belongs to the mod's visual world;
- icon, world model, and UI representations describe the same object;
- detail survives the target camera and lighting;
- the finished set feels internally consistent.

Record `awaiting_art_review` rather than turning taste into a machine pass.

## Quality gates

### Brief gate

- purpose, usage contexts, profile, and real referent are explicit;
- rights and provenance are known;
- required Build 42 facts are verified or visibly blocked;
- project-selected budgets are labeled as policy;
- final reviewer is named.

### Comp gate

- silhouette, value, and scale comparisons exist;
- variants differ structurally, not only by color;
- the selected direction has a recorded reason;
- no detailed production begins before approval.

### Finish gate

- inspect at native UI size and actual game camera distance;
- compare beside the declared vanilla references;
- inspect on bright, dark, and busy backgrounds when applicable;
- check alpha edges, texture seams, shading, and generated artifacts;
- review the complete asset set, not only the best individual asset;
- record one remaining weakness even when accepted.

## Asset-specific direction

### Item icons and UI art

- Judge recognition at the actual rendered size.
- Keep internal margins consistent across the set.
- Request transparent backgrounds only when the runtime role needs them.
- Keep player-facing text in game localization where possible.

### Concept and orthographic images

- Concept sheets explain construction, materials, scale, and moving parts.
- Orthographic sheets use matched front, side, back, and top views without perspective.
- State real dimensions and axis intent only when verified.
- Concept art never becomes a runtime texture by default.

### Texture references

- Treat generated texture images as color and material references.
- Do not call a painted image a physically correct albedo, normal, roughness,
  metallic, or ambient-occlusion map.
- Author or bake runtime maps in a controlled material workflow.
- Review tiling, edge padding, alpha, and mip-scale readability manually.

### Blender-bound assets

- Blender is authoritative for geometry, UVs, materials, rigging, and FBX export.
- AI meshes and downloaded files are untrusted source candidates.
- No generated mesh bypasses retopology, surface review, scene validation, export
  round-trip, and in-game review.

## Provenance

Record per source and output:

- asset ID and workspace-relative path;
- author or generating tool and model;
- origin URL and right-to-use evidence;
- cryptographic hash;
- exact image prompt when generated;
- human edits after generation;
- reviewer and verdict for each gate.

An asset without complete provenance does not ship.

## Handoff

For image work, pass the approved brief to `codex-image-prompts.md`. Save the exact
copy/paste prompt with the resulting image and provenance.

For 3D work, pass the approved brief, orthographic references, project budget, and
verified target facts to `blender-fbx-pipeline.md`. All writes remain governed by
`safety-boundaries.md`.

## Limits

Art direction cannot prove engine compatibility. Promotion still requires Blender
validation, FBX round-trip evidence, package wiring checks, and real Build 42 runtime
QA on the exact released bytes.
