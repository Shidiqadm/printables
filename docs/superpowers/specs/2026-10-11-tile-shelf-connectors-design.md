# Tile shelf connectors: design spec

**Date:** 2026-10-11
**Status:** approved, implemented
**Project folder:** `projects/tile-shelf-connectors/`

## Goal

Printed connectors that turn leftover ceramic tiles into a low, single-row cube shelf (like a TV/book unit), held together by friction only, with no glue, screws or tools, so the tiles can be reused later.

### What the user specified

- Layout: one row of cubes side by side; no stacking, no back panels.
- Load: light decor, under 10 kg per cube.
- Tiles: mixed sizes, factory square edges. Thickness unknown, so the design must be configurable.
- Printer and material: Bambu A1, 0.4 mm nozzle, PLA (see `CLAUDE.md`).

### Assumptions (not stated by the user)

- Tiles are 6–12 mm thick and flat within normal factory tolerance (about ±0.3 mm within one batch).
- The top surface may have a 4 mm raised cap at each connector (as in the reference photos).
- Shelf depth equals the tile dimension used for side tiles; cube width equals the top tile length plus the rib.

## Architecture

### Coordinate frame

X runs along the row, Y is depth (0 = front face of the tiles, +Y towards the back), Z is up (0 = top edge of the side tile for a top connector).

### Shared-wall layout

Neighbouring cubes share one vertical side tile. A connector sits at each of the 4 corners of every side tile (front/back × top/bottom).

| Part | Position | Count for N cubes |
|------|----------|-------------------|
| `middle` | corners of the N−1 inner side tiles | 4(N−1) |
| `end` | front-left-top, front-right-bottom, back-right-top, back-left-bottom | 4 |
| `end_mirrored` | the other four end corners | 4 |

Parts reach other positions by 180° rotations about X, Y or Z:
- `middle` is mirror-symmetric in X, so one file covers all of its positions.
- `end` has no mirror symmetry. Rotations carry it to only 4 of the 8 end corners; the other 4 take `end_mirrored`, which is the same part mirrored in X.

That makes three printed files: `middle`, `end` and `end_mirrored`. A 3-cube row needs 8 + 4 + 4.

### Load path

1. Top tiles rest directly on the side tile's top edge: ceramic bearing on ceramic. The `middle` connector gives each top tile `(T_SIDE − RIB)/2` of bearing (3 mm for 8 mm tiles). On the `end` connector the end top tile bears on the full `T_SIDE`.
2. Side tiles stand on the bottom tiles' edges, again ceramic on ceramic.
3. Bottom tiles rest on the bottom connectors' 4.2 mm foot plate (the "cap" when flipped), which is the only thing touching the floor.
4. The plastic locates the tiles and resists racking. It carries no gravity load except at the feet, where it is in pure compression.

## Connector geometry

### Profile (XZ cross-section, constant along Y)

The middle connector, seen from the front:

```
   ┌──────────────── cap ───────────────────────┐
   │ top tile L          │rib│        top tile R │
   └──────jaw───────┐  side tile  ┌───────jaw────┘
                    │             │
                    └ jaw     jaw ┘
```

- **Shelf slot:** height `T_SHELF + CLEAR`, running from the rib out to the wing end (open at the wing end and the back).
- **Side slot:** width `T_SIDE + CLEAR`, running from Z=0 down to `−ARM` (open at the bottom and the back).
- **Rib:** `RIB` wide, between the two shelf slots, directly above the side tile.
- **Cap:** `CAP` thick above the shelf slots.
- **Under-jaws:** `PLATE` thick below the shelf slots, outboard of the side tile.
- **Side jaws:** `PLATE` thick either side of the side slot.
- **Wing reach:** each shelf slot extends `ARM` beyond the side tile face.
- **Extrusion:** the profile is extruded `DEPTH` along +Y.
- **Front plate:** `FRONT` thick at Y<0, covering the profile outline and hiding the tile edges.
- **End variant:** the same as middle, except:
  - the outer wing is removed;
  - an outer wall `PLATE` thick closes both slots on the outside;
  - there is no rib, so the end top tile sits over the full side tile.

### Grip

- **Thickness band:** each slot accepts tiles within ±`THICK_TOL` (0.3 mm) of nominal without reprinting.
- **Clearance:** slots are nominal tile thickness + `CLEAR`, where `CLEAR` = `THICK_TOL` + the linear "snug" fit (0.1) = 0.4 mm. A tile at +0.3 mm still slides in with 0.1 mm to spare.
- **Crush ribs:**
  - Half-round ribs (R 2 mm) run along Y, on one face of each slot: the cap underside for shelf slots, and the +X jaw for side slots.
  - Each rib reaches `CLEAR + CRUSH` = 0.7 mm into the slot. Interference is 0 at −0.3 mm, 0.3 at nominal and 0.6 at +0.3 mm. Part of that is taken up by the jaws flexing.
  - Ribs run parallel to the slide-in direction, so they shave rather than catch. Their round profile also acts as a ramp for side tiles dropped in vertically.
- **Rib count:** two ribs per slot face, near the far ends of the clamp length, so the grip resists rotation (racking), not just sliding.
- **Lead-in:** slot mouths at the back and at the wing ends get a 1.0 mm 45° chamfer. Crush ribs stop 3 mm inside the back mouth and ramp in over 2 mm.
- **Outside the band:** change `T_SHELF`/`T_SIDE` and reprint. No spring tabs, because PLA creep would relax them.
- **Measuring without calipers:** a printed `thickness_gauge` comb (5.0–12.0 mm in 0.5 mm steps) finds the tile thickness.

### Parameters (defaults)

| Name | Default | Meaning |
|------|---------|---------|
| `T_SHELF` | 8.0 | top/bottom tile thickness |
| `T_SIDE` | 8.0 | side tile thickness |
| `THICK_TOL` | 0.30 | tile thickness variation handled without reprinting |
| `CLEAR` | `THICK_TOL` + `fit("snug","linear")` = 0.40 | slot clearance (total) |
| `CRUSH` | 0.30 | crush rib interference at nominal thickness |
| `RIB` | 2.0 | gap/rib between top tiles |
| `PLATE` | 3.36 | jaw/wall thickness (8 lines) |
| `CAP` | 4.2 | cap/foot thickness (10 lines); sized for racking stiffness |
| `ARM` | 28.0 | clamp reach along each tile beyond the side tile |
| `DEPTH` | 30.0 | how far the connector reaches back along the tile edges |
| `FRONT` | 3.0 | front plate thickness (15 layers) |
| `EDGE` | 1.0 | outer chamfer on visible edges; 0.4 on bed-side edges |

## Printing

- **Orientation:** front plate on the bed. All slots stand vertical, so there are no supports and no overhangs. The visible face is the smooth bed side.
- **Strength:** slot walls are loaded in bending within their layers, not across them, so tile insertion and racking loads never peel layers apart.
- **Settings:** PLA, 0.20 mm layers, 4 walls, 30% gyroid infill. Plates of 3.36 mm or less print fully solid anyway.
- **Mass:** estimated 25–30 g per connector. To be confirmed by `check()`.

## Engineering checks (hand calcs)

Assumed tiles: 300×300×8 mm, about 1.7 kg each. A 3-cube row with 10 kg per cube weighs about 47 kg in total.

| Check | Result | Status |
|-------|--------|--------|
| Ceramic bearing, top tile on side tile edge | 50 N over 3 mm × 300 mm ≈ 0.06 MPa | negligible |
| Foot compression, per bottom connector (8 connectors, 460 N total) | 58 N over ≈ 2000 mm² ≈ 0.03 MPa | negligible |
| Tile bending, 300 mm span, 100 N distributed, 8 mm thick | ≈ 2 MPa vs ≥ 35 MPa ceramic flexural strength | about 17× margin |

**Racking** (the critical case, since there is no back panel):
- Load case: a 50 N sideways bump at the top of the row.
- This puts about 1 N·m on each of the 8 front/back top joints.
- Over a 25 mm clamp couple, that gives about 40 N of contact force at the wing tip.
- Treating the 4.2 mm cap as a 28 mm cantilever: stress about 13 MPa, deflection about 0.5 mm. PLA yields at about 50 MPa, so this is fine for a transient bump.
- The real stiffness is higher, because the cap is also tied to the front plate along its whole edge.
- Sustained sideways load is not expected.

## Assembly

1. Lay the bottom tiles in a row (glaze up). Slide the bottom connectors on from the front and back.
2. Drop the side tiles straight down into the side slots.
3. Lay the top tiles glaze-down, slide on the top connectors from the front and back, and lower the joined top onto the side tiles.
4. To move the shelf, lift from the bottom. The top lifts off by design.

## Deliverables

- `projects/tile-shelf-connectors/model.py`: parametric generator for the `middle`, `end` and `end_mirrored` parts and a `fit_test` piece, plus a digital assembly of a 3-cube row (assembly is preview only, not exported).
- `projects/tile-shelf-connectors/README.md`: parameters, print settings, counts per row length, assembly steps, print log.
- Exports: `middle.3mf`, `end.3mf`, `end_mirrored.3mf`, `fit_test.3mf`, `thickness_gauge.3mf` (plus STEP and STL).

## Verification

1. `check()` on every part: valid, single solid, on the bed, fits the A1 volume.
2. Interference test against a digital tile slab at nominal, −0.3 mm and +0.3 mm thickness:
   - zero overlap with the slot walls;
   - crush rib overlap within 0.0–0.6 mm.
3. Assembly test of a 3-cube row: tiles do not overlap connectors, except at crush ribs.
4. Visual check in the viewer, including from the bed side.
5. Physical: print `fit_test` (one short middle-connector section) on the user's real tiles before printing the full set. Log the result in the README.

## Out of scope

Stacking, back panels, coffee table variant, flush top surface, decorative face patterns. Each can be added later as a parameter or variant.
