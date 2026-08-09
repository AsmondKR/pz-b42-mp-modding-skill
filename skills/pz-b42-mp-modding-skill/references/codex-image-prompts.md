# Codex image prompts

Use this reference to turn an approved PZ asset brief into prompts the user can paste
into the Codex app. The skill does not call an image API, generate a file, or spend API
credit.

Prompt structure follows the specificity and preservation principles in the official
[OpenAI ImageGen skill](https://github.com/openai/skills/tree/main/skills/.system/imagegen),
adapted here for game-asset handoff.

## Required intake

Read `asset-art-direction.md` first. Do not write a production prompt until these are
known:

- asset ID and use case;
- approved visual direction and real referent;
- target view and final display context;
- required aspect ratio or transparent canvas;
- materials, construction, condition, and recognition cues;
- reference image roles;
- literal text, if any;
- elements that must not change;
- prohibited motifs and artifacts;
- next handoff: UI, texture authoring, or Blender.

Ask only for missing facts that would materially change the output. Never invent a
Build 42 size, camera convention, skeleton, or runtime texture rule.

## Stable prompt order

Keep this order so prompts remain reviewable:

1. use case;
2. canvas and composition;
3. subject and construction;
4. materials and condition;
5. view, scale, and lighting;
6. visual-world lock;
7. reference-image roles;
8. literal text;
9. preservation and exclusion constraints;
10. output intent.

Specific user requirements are invariants. Add detail only when it clarifies an
existing requirement; do not add story elements or decorative objects.

## Copy/paste output

Return one block per requested image. Do not bury the final prompt in explanation.

```text
Asset ID: <stable asset ID>
Use case: <concept sheet | orthographic turnaround | item icon | UI art | decal |
  seamless texture reference | edit>
Canvas: <aspect ratio, background, alpha intent, and safe margins>
Primary request: <subject, construction, state, and action>
Composition: <viewpoint, framing, orientation, scale cue, and negative space>
Materials and detail: <observable material, wear, fasteners, labels, and edges>
Visual-world lock: <the same approved style statement for the complete asset set>
Reference images: <Image N: role and what must be taken from it>
Literal text: <exact quoted text, placement, type character, or "none">
Constraints: <preserve, exclude, do not add, and output intent>
```

After the block, provide:

- `Review at:` the native UI size or intended modeling use;
- `Blender handoff:` what the image proves and what it does not prove;
- one optional edit prompt that changes only the weakest declared axis.

## Style lock

Write one concise visual-world lock for the asset set and keep it unchanged across
related prompts. It should describe:

- realism or stylization level;
- palette source and value range;
- material rendering language;
- edge and wear treatment;
- lighting neutrality;
- relationship to inspected vanilla references.

If the lock changes, treat the result as a new direction and regenerate the comparison
set. Do not mix visually incompatible locks in one shipped set.

## Reference-image roles

Label every input image by number and one role:

- `identity`: preserve the exact object or character identity;
- `structure`: preserve proportions, construction, or layout;
- `style`: borrow rendering language only;
- `material`: borrow surface response or wear;
- `context`: establish scale or game placement.

Use only references that materially help. State what must be ignored as well as what
must be copied. A reference is not permission to reproduce protected logos, text, or
unlicensed artwork.

## Prompt recipes

### Concept sheet

- Request several structurally distinct silhouettes on one neutral sheet.
- Add material, dimension, and moving-part callouts.
- Keep perspective consistent enough to compare candidates.
- State that the sheet is a design artifact, not a runtime texture.

### Orthographic turnaround

- Request front, back, left, right, and top views.
- Require matched scale, alignment, neutral lighting, and no perspective.
- Use a plain high-contrast background and no cast shadow crossing the silhouette.
- Require construction consistency across every view.
- State real dimensions only when the brief supplies them.

AI-generated turnarounds can contain contradictory geometry. Blender modeling must
resolve those contradictions; never trace every view blindly.

### Item icon

- Frame for recognition at the verified native size.
- Use one dominant silhouette and controlled internal detail.
- Request transparent background only when required.
- Reserve consistent padding across the set.
- Exclude dramatic perspective, cinematic light, borders, and decorative particles
  unless the approved art direction explicitly requires them.

### UI art

- Name the exact surface and interaction state.
- Reserve negative space for runtime text and controls.
- Keep player-facing strings out of generated pixels when localization should render
  them.
- Request state variants together only when their geometry and alignment must match.

### Decal

- Specify the physical substrate, print process, age, edge damage, and alpha intent.
- Request a straight-on isolated result with no scene lighting baked around it.
- Quote required lettering exactly and request verbatim rendering.
- Plan to redraw critical text and logos manually if generation is inconsistent.

### Seamless texture reference

- Request orthographic surface coverage with no focal object or directional shadow.
- Describe material scale, variation frequency, wear distribution, and forbidden
  repeated landmarks.
- Request seamless edges as a visual goal, then verify tiling manually.
- Label the result `color reference`, not `production PBR`.

An image model does not calculate physically correct albedo, roughness, metallic,
normal, height, or ambient-occlusion maps. Author or bake those maps in a controlled
material workflow and inspect them in Blender.

## Exact text

- Default to `Literal text: none`.
- When text is required, quote it exactly and specify placement, line breaks, case,
  color, and type character.
- Say `render this text verbatim; add no other letters or marks`.
- Keep translated runtime strings outside generated images whenever possible.
- Inspect every character manually before accepting the image.

## Editing

For an accepted base image, edit one axis at a time:

```text
Use case: targeted edit
Input images: Image 1: accepted base
Primary request: change only <one region or property> to <specific outcome>
Preserve: composition, silhouette, proportions, palette, materials, lighting, all
  unmentioned details, and exact canvas dimensions
Constraints: add no new objects or text
```

Repeat critical preservation constraints in every edit. Do not rely on conversation
memory to protect approved details.

## Review and handoff

Before giving the prompt to the user:

- all brief invariants appear explicitly;
- reference images have roles;
- exact text is quoted or prohibited;
- exclusions are concrete rather than generic quality words;
- final viewing size or modeling purpose is named;
- no unverified PZ fact was added;
- texture output is labeled as a reference;
- no API call or file write is implied.

Save the exact prompt and generated-image hash in provenance. The approved image then
enters `blender-fbx-pipeline.md` as an immutable reference, never as proof that the
resulting geometry or material is game-ready.
