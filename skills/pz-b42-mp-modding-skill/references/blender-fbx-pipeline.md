# Blender FBX pipeline

Blender is the authoritative source for every 3D asset. An FBX is a derived build
artifact; never repair the FBX by hand.

This workflow uses Blender 5.1 or newer for inspected scene state, explicit-object FBX
export, and round-trip QA. An AI-generated or downloaded mesh is untrusted input and
receives no shortcut through the gates.

## Evidence status

The community modeling guide documents Blender-to-PZ FBX use and applied transforms:
https://theindiestone.com/forums/topic/37647-the-one-stop-shop-for-3d-modeling-from-blender-to-zomboid/

The current Blender operator contract is documented at:
https://docs.blender.org/api/current/bpy.ops.export_scene.html

These sources do not prove one universal Build 42 contract. Do not invent:

- asset-class triangle, material, texture, bone, or animation limits;
- exact units, axes, origin, pivot, attachment transforms, or rotation order;
- required FBX version and exporter flags for every loader path;
- UV names or counts, tangent policy, normal-map convention, or material channels;
- skeleton names, hierarchy, bind pose, influence limit, or animation settings;
- vehicle part, wearable mask, collision, LOD, or package rules.

Classify each constraint as:

- `verified`: observed in the current installed build and linked to evidence;
- `project_policy`: a declared production budget chosen by the mod team;
- `unknown`: unresolved; block promotion when the profile needs it.

One vanilla sample proves that one configuration exists. It does not prove a maximum or
universal rule.

For installed public Build `24574865`, begin with
`build-24574865-fbx-reference.md`. Its five measurements are file-specific observations.
Any Build ID, FBX hash, script hash, Blender version, or probe-version change invalidates
that reference.

## Supported workflow profiles

- `static_model`: non-rigged prop or world model;
- `held_model`: held, world, or stowed object with evidence-backed attachments;
- `rigged_model`: clothing or character-bound mesh with an exact verified skeleton;
- `vehicle_model`: multipart vehicle asset with an exact verified reference.

Static and held models may proceed with project policies. Rigged and vehicle promotion
must stop when the matching Build 42 skeleton, hierarchy, part names, or transforms are
unknown.

## Intake

1. Place source candidates under an authorized workspace, never in the game install or
   Workshop subscription.
2. Record origin, license, author, and SHA-256 before editing.
3. Disable automatic Python execution before opening an untrusted `.blend`.
4. Import untrusted geometry into an empty inspection scene.
5. Inspect hidden objects, collections, drivers, text blocks, node groups, custom
   properties, and external paths.
6. Rebuild or clean the accepted candidate in a new project file.
7. Keep references outside the explicit export-object list.

No downloaded or generated source is production-ready by origin.

## Reference lock

Before choosing scene scale or orientation:

1. Run `scripts/plan_pz_fbx_reference.py` for an exact same-role vanilla FBX.
2. Review and execute the emitted Blender command without editing it.
3. Record build, branch, relative FBX path, file hash, encoding, FBX axes and units,
   measurement space, mesh-local geometry dimensions, imported bounds, and matching
   model-script transform.
4. Import binary references into a clean Blender comparison scene and exclude them from
   export.
5. Keep mesh-local geometry dimensions, raw/imported bounds, FBX unit metadata, Blender
   object scale, model-script
   `scale`, attachment transforms, and `undoCoreScale` separate.

Never multiply those values into runtime metres without an in-game measurement. Never
copy one profile's front axis into another profile: current shipped observations already
contain both `Front -X / Coord +Z` and `Front +Z / Coord +X`.

### Held tool and weapon size

PZ weapon editing geometry can be visually tiny in Blender. That is not, by itself, a
broken import and it is not evidence that Blender's FBX `Global Scale` should change.

- In public Build `24574865`, shipped `weapons/1handed/Machete.x` has a raw mesh envelope
  of approximately `0.009428 x 0.334505 x 0.056614`; its model declaration has no
  `scale`, so the script default is `1`.
- Shipped `weapons/Floor_FBX/ButterflyKnife_Closed.fbx` has a raw geometry envelope of
  approximately `10.087231 x 3.268965 x 0.566537`, while its model declaration applies
  `scale = 0.01`. The script-scaled source-coordinate envelope is therefore approximately
  `0.100872 x 0.032690 x 0.005665`.
- The common `0.01` weapon workflow is a one-time geometry/conversion correction or a
  model-script transform. It is not a universal FBX unit-metadata rule. Converted legacy
  `.x` references are frequently 100 times too large until that correction is applied.

For a held/tool/weapon asset, match one named vanilla reference's raw geometry together
with that same reference's model-script transform. If the pair proves a 100:1 conversion
is required, choose exactly one correction layer:

- preserve the larger geometry and use model-script `scale = 0.01`; or
- duplicate the authored mesh into an export collection, bake `0.01`, apply transforms so
  the export object is back at `(1, 1, 1)`, and use model-script scale `1`.

Keep the checked-in FBX exporter at `Global Scale = 1.0`; do not combine baked `0.01`,
exporter `0.01`, and model-script `scale = 0.01`. Round-trip validation must preserve the
chosen export geometry.

## Manifest

Use one JSON manifest per Blender asset:

```json
{
  "asset_id": "ExampleAxe",
  "export_objects": ["ExampleAxe"],
  "output_fbx": "build/ExampleAxe.fbx",
  "profile": "static_model",
  "schema_version": 1,
  "source_blend": "source.blend",
  "texture_files": ["textures/albedo.png"],
  "topology_policy": "closed_solid",
  "triangle_budget": 2400
}
```

Paths are workspace-relative. The shared policy must authorize the output immediately
before Blender creates it. Inputs and destinations containing links or reparse points
are rejected. Existing FBX files are never overwritten.

`triangle_budget` is a project policy unless the manifest's evidence record proves
otherwise.

Rigged manifests also declare `expected_armature` and `max_vertex_influences`, both
derived from evidence or explicitly labeled project policy.

## Human Blender work

Humans own:

- modeling and retopology;
- seam placement and unwrap strategy;
- normals and shading decisions;
- material authoring and texture baking;
- rig placement and weight painting;
- animation and deformation polish;
- visual approval.

Automation may inspect, report, export an explicit set, and compare a round trip. It
must not silently decimate, remesh, fill holes, unwrap, merge objects, delete materials,
replace textures, recalculate all normals, auto-rig, or waive a failed check.

## Objective scene gate

Before export, the installed validator checks the declared objects:

- all export object names exist and are unique;
- at least one non-empty mesh is present;
- triangle total does not exceed the declared project budget;
- object scale is `(1, 1, 1)` and rotation is zero;
- dimensions are finite and non-zero;
- every textured mesh has a UV map and material assignment;
- required texture files exist and Blender reports no missing images;
- no unapplied modifiers remain;
- closed-solid profiles have no non-manifold boundary;
- rigged profiles have the declared armature and one armature modifier per mesh;
- rigged vertices respect the declared influence count and normalized weights.

These checks reject objective defects. They do not approve silhouette, edge flow,
material quality, deformation, or game fit.

## Export

The launcher:

1. loads the workspace policy and manifest;
2. refuses linked paths and existing destinations;
3. starts Blender in background mode with factory settings and auto-execution disabled;
4. loads only the declared `.blend`;
5. validates only the declared export objects;
6. selects the explicit export set;
7. exports with a checked-in preset;
8. clears the scene and reimports the produced FBX;
9. compares object and mesh semantics;
10. emits versioned JSON.

The checked-in preset is a reviewable project baseline, not a universal B42 promise.
Observed source-file axes do not by themselves prove the game's required exporter flags.
Any same-role evidence requiring different flags needs a separately named preset,
round-trip tests, and matching-build in-game QA.

## Round-trip gate

Compare source and reimported FBX:

- exported mesh and armature count;
- object names;
- triangle distribution;
- material-slot and UV-layer counts;
- world-space bounds within declared tolerance;
- rig names and hierarchy when applicable.

FBX bytes need not be identical. Semantic drift is a failure. Fix the source scene or
export preset, then create a new FBX; never patch the exported file.

## Manual visual gates

### Geometry

- silhouette reads at the target PZ camera distance;
- proportions and comparison scale match the approved brief and exact vanilla reference;
- bevels, thickness, intersections, and topology are intentional;
- deformation topology supports required motion.

### Surface

- seams and stretching are acceptable at final texture resolution;
- alpha has no fringe;
- material separation and contrast survive neutral and PZ-like lighting;
- generated color references were converted into authored or baked runtime maps.

### Rig and animation

- extreme poses preserve volume and avoid clipping or twisting;
- contacts, arcs, timing, loops, and root behavior are correct;
- every required gameplay pose is reviewed.

### Export comparison

Use fixed source and reimport views: orthographic silhouettes, three-quarter view,
wireframe, face orientation, UV checker, neutral material, and final texture preview.

## Build 42 runtime gate

Blender success is not game success.

- Wire the asset through evidence-backed Build 42 scripts and package paths.
- Launch the exact target build and inspect loader output.
- Instantiate every declared usage context.
- Compare scale and orientation with a verified vanilla neighbor.
- Test single-player, hosted multiplayer, and a joining client with a cold cache when
  the mod ships to multiplayer.
- Review held/stowed states, wearables, vehicle parts, or animations required by the
  selected profile.

Release only the exact hashes that passed Blender round trip, package validation, and
runtime review.
