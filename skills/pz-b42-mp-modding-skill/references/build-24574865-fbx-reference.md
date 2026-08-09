# Installed FBX reference: Build 24574865

Observed evidence from the installed public Build 42 branch. This file records measurements, not universal export settings.

## Provenance

- Build: `24574865`
- Branch: `public`
- Vanilla population: 2,032 FBX files under `media/`
- Sample count: 5
- Coverage: 0.246 percent
- Binary probe: Blender `5.1.0`
- ASCII probe: bundled geometry-array parser
- Observation schema: `1`

No vanilla model, texture, or decoded geometry is included. Paths are game-relative and each observation carries the shipped file hash.

## Script evidence

| Role | Model declaration | Script fact |
| --- | --- | --- |
| Held open razor | `media/scripts/generated/models_items.txt:6658` | `mesh = StraightRazor_Open`, `scale = 0.005` |
| Ground angle flashlight | `media/scripts/generated/models_items.txt:232` | `mesh = WorldItems/FlashLight_AngleHead_Ground`, `scale = 0.4` |
| Ground hoodie | `media/scripts/generated/models_clothes.txt:3` | `mesh = WorldItems/Clothing/Bob_Hoodie_Ground`, `scale = 0.33` |
| Iso laundry object | `media/scripts/generated/models_isoobject.txt:3` | exact mesh, `undoCoreScale = true`, no declared `scale` |
| Normal vehicle | `media/scripts/generated/vehicles/vehicle_car_normal_model.txt:3` | exact mesh, `invertX = false`, `scale = 0.008` |

Script hashes for this build:

| Relative script | SHA-256 |
| --- | --- |
| `media/scripts/generated/models_items.txt` | `d07882a16fb85ca66eca3510da1c210d29ea20c2c4415f66dc2dcee20ab4d37d` |
| `media/scripts/generated/models_clothes.txt` | `ba30d759e053ea92198534461e48fad43bbbf431be37d726a1f2afde689d499e` |
| `media/scripts/generated/models_isoobject.txt` | `ca87ec2b7154ead64d9ebde8880a341f433df66681e6426f0087097c8bc77b1e` |
| `media/scripts/generated/vehicles/vehicle_car_normal_model.txt` | `dec42a8009c3b0f45805fa2da58da983e23fc8a9bae81a7ee8c69a835fd3bee5` |

## Observed FBX records

Dimensions for binary files are Blender-imported axis-aligned bounds. Dimensions for the ASCII vehicle are raw FBX geometry-array bounds. These measurement spaces are not interchangeable.

| Role | Relative FBX and SHA-256 | Encoding | Axes: up/front/coord | Unit/original | Observed dimensions | Triangles | Script transform |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Held open razor | `media/models_X/StraightRazor_Open.fbx`<br>`c9743d187054a367669f0cb1374d1e7e44471d6a2d43dda10ae7b0e653aaa7e1` | binary 7400 | `+Y / -X / +Z` | `1.0 / 1.0` | Blender: `0.406274 x 0.098086 x 0.026210`; object scale `0.0254` | 348 | `scale 0.005` |
| Ground angle flashlight | `media/models_X/WorldItems/FlashLight_AngleHead_Ground.fbx`<br>`b6b24926c781a38871f15029af700fbcffd6afabf9f42111190f029bedecc781` | binary 7400 | `+Y / +Z / +X` | `91.44 / 2.54` | Blender: `0.377238 x 0.150154 x 0.098333`; object scale `0.0254` | 142 | `scale 0.4` |
| Ground hoodie | `media/models_X/WorldItems/Clothing/Bob_Hoodie_Ground.fbx`<br>`cbf46749b461c2527163530488f4e2875a25e86c8bf5a49b397b8a94a3561561` | binary 7400 | `+Y / +Z / +X` | `91.44 / 2.54` | Blender: `1.491739 x 1.143836 x 0.048236`; object scale `0.0254` | 360 | `scale 0.33` |
| Iso laundry | `media/models_X/IsoObject/appliances_laundry_P1_00.fbx`<br>`a445f75cbeaa97ab9ed350f938799e3c3f3b60f3fc6d9c0b1ca21bddda2a82b5` | binary 7400 | `+Y / +Z / +X` | `100.0 / 100.00000066` | Blender: `0.809270 x 0.785760 x 0.895091`; object scale `1.0` | 2,136 | `undoCoreScale true` |
| Normal vehicle | `media/models_X/vehicles/Vehicles_CarNormal.fbx`<br>`d57880ba2da8dcd44419726336dcb027ee083d20654ea448cfae4f2ab9908cec` | ASCII | `+Y / +Z / +X` | `2.54 / 2.54` | Raw FBX: `132.798515 x 327.078949 x 81.891129`; 532 vertices | 823 | `invertX false`, `scale 0.008` |

## Direction reference rules

1. Never state one PZ FBX front or coordinate axis. The held sample contradicts the four other observations in this build.
2. `Up=+Y` is an observed five-of-five value, not a loader requirement.
3. Select the exact same runtime role first: held, ground/world, clothing ground, iso object, or vehicle.
4. Prefer an exact shipped file and its same-build model declaration. Bind both hashes in the asset brief.
5. Match orientation in a clean Blender comparison scene after import. Do not rotate authored source merely to imitate metadata labels.
6. Vehicle FBX is ASCII in this sample and Blender 5.1 refuses to import it. Do not derive a Blender vehicle export preset from this record.

## Size reference rules

1. Keep raw/imported bounds, FBX unit metadata, model-script `scale`, and `undoCoreScale` as separate observations.
2. Never multiply them into "runtime metres." No measured game-loader contract proves that result.
3. Match silhouette and proportions against the exact same-role vanilla observation.
4. Confirm final scale in the matching Build 42 game next to a known vanilla object.
5. A project may choose triangle or texture budgets, but must label them `project_policy`, not PZ limits.

## Reproduce the probe

Generate a reviewed command:

```bash
python scripts/plan_pz_fbx_reference.py \
  --sample held_open_razor=media/models_X/StraightRazor_Open.fbx \
  --sample world_angle_flashlight=media/models_X/WorldItems/FlashLight_AngleHead_Ground.fbx \
  --sample clothing_ground_hoodie=media/models_X/WorldItems/Clothing/Bob_Hoodie_Ground.fbx \
  --sample iso_laundry=media/models_X/IsoObject/appliances_laundry_P1_00.fbx \
  --sample vehicle_normal=media/models_X/vehicles/Vehicles_CarNormal.fbx
```

Review and execute the exact command array. Output declares:

- `claims_excluded.runtime_metres = true`
- `claims_excluded.loader_behavior = true`
- `claims_excluded.universal_axis_convention = true`
- `population_claimed = false`

Re-run after any Build ID, FBX hash, script hash, Blender version, or probe version change. Until then this reference is a Build `24574865` observation only.
