# Tile shelf connectors: design spec

**Date:** 2026-10-11
**Status:** revision 3, implemented: two styles (r2 `cube` and r3 `deco`) on one shared core
**Project folder:** `projects/tile-shelf-connectors/`

## Revision history

- **r1, approach B:** shared side tile, thin T/L profile connectors.
  - Replaced at the user's request with a heavy-duty cube hub like the reference photos.
  - Review also found a flaw in r1: its lower jaws were joined to the rest only through the 3 mm front plate.
- **r2:** universal cube hub, double side walls, filler plug, grooved faces.
- **r3:** Art Deco styling. The user asked for "an art piece which also works as a functional print". The r2 functional core is unchanged (see the "Revision 3" section below). At the user's request, the r2 grooved cube is kept alongside it as the `cube` style.

## Goal

Printed connectors that turn leftover ceramic tiles into a low, single-row cube shelf, held together by friction only (no glue, screws or tools), so the tiles can be reused later. The connectors should be heavy-duty and cube-shaped, like the reference design.

### What the user specified

- Layout: one row of cubes side by side; no stacking, no back panels.
- Load: light decor, under 10 kg per cube. The user still wants a heavy-duty connector.
- Tiles: mixed sizes, factory square edges. Thickness must be configurable.
- Each cube has its own side tiles (double walls).
- One universal hub, plus filler plugs for unused slots.
- The hub stands proud of the top surface, so the top tile is clamped on both faces.
- Grooved 3×3 block look.
- Printer and material: Bambu A1, 0.4 mm nozzle, PLA.

### Assumptions

- Tiles are 6–12 mm thick and flat, within ±0.3 mm of nominal within one batch.
- Within one cube, the top and bottom tiles are the same length, and all side tiles are the same height.

## Architecture

### Coordinate frame

- X runs along the row.
- Y is depth: 0 is the front face of the tiles, +Y is towards the back.
- Z is up: 0 is the top edge of the side tiles, for a hub in the top position.

### Layout

- Every cube is identical: a bottom tile, a top tile, and two side tiles of its own.
- Hubs sit at every junction, front and back, top and bottom. Each hub joins the corners of two neighbouring cubes, or one cube at the ends of the row.

| Part | Count for N cubes |
|------|-------------------|
| `hub` | 4(N+1) |
| `plug` | 8: one in the unused channel of each end hub |
| tiles | N top, N bottom, 2N side |

### Orientation and handedness

- The hub is mirror-symmetric in X.
- One hub file covers every position through 180° rotations: about Z for front ↔ back, about Y or X for top ↔ bottom.
- The plug is a plain L-prism with both ends chamfered, so it fits either channel.

### Load path

1. Each top tile rests on the full top edge of its own side tiles, ceramic bearing on ceramic over the full tile thickness.
2. Each side tile stands on the full edge of its bottom tile.
3. Bottom tiles rest on the hubs' 5 mm foot (the cap, when the hub is flipped). The foot is the only part touching the floor.
4. The plastic locates the tiles and resists racking. It carries gravity load only at the feet, in compression.

## Hub geometry

### Cross-section (XZ, constant along Y), hub size `HUB`

Seen from the front:

```
 ┌──────────── cap ────────────┐
 │ top tile L │col│ top tile R │
 ├───────┐ side │ │ side ┌─────┤
 │ block │ tile │ │ tile │block│
 │       │  L   │ │  R   │     │
 └───────┘      └─┘      └─────┘
```

- **Two L-shaped channels**, one per cube. Each is a top-tile slot (`TS` = `T_SHELF` + `CLEAR` high, running from the column face `X1` out through the side face) joined to a side-tile slot (`TW` = `T_SIDE` + `CLEAR` wide, running from Z=0 out through the bottom face).
- **Centre column:** `COLUMN` wide, full height, carrying the cap. It separates the two cubes' side tiles and top tiles.
- **Cap:** `CAP` thick, over both top-tile slots.
- **Corner blocks:** solid, filling the inside corner of each L, `HUB/2 − X2` wide.
  - Each block is wedged between its top tile's underside and its side tile's inner face.
  - Racking squeezes the block between the two tiles rather than bending it.
  - Each block is tied to the rest of the hub by the solid `FRONT` face.
- **Extrusion:** the profile is extruded `HUB − FRONT` along +Y, closed by a solid front face `FRONT` thick, giving a `HUB`³ cube.
- **Plug:** fills one channel at nominal tile thickness, so the crush ribs grip it like a tile. Its outer faces are flush with the hub.

### Grip

- **Thickness band:** each slot accepts tiles within ±`THICK_TOL` (0.3 mm) of nominal without reprinting.
- **Clearance:** `CLEAR` = `THICK_TOL` + the linear "snug" fit (0.1) = 0.4 mm. A tile at +0.3 mm still slides in.
- **Crush ribs:**
  - Half-round ribs (R 2 mm) run along Y: two on the cap underside per top slot, and two on the corner-block face per side slot.
  - Each reaches `CLEAR + CRUSH` = 0.7 mm into the slot. Interference is 0 at −0.3 mm, 0.3 at nominal and 0.6 at +0.3 mm.
  - The ribs push the tiles against the solid faces: block top for top tiles, column face for side tiles.
- **Lead-in:** slot mouths get a 1 mm 45° chamfer, on the back face and on the side and bottom openings. Ribs stop 3 mm inside the back mouth and ramp in over 2 mm.
- **Outside the band:** change `T_SHELF`/`T_SIDE` and reprint.
- **Measuring without calipers:** a printed `thickness_gauge` comb (5.0–12.0 mm in 0.5 mm steps) finds the tile thickness.

### Look

- `ROUND` 2 mm radius on the cube's long edges, and a 1 mm chamfer on the front face edges.
- 1 × 0.6 mm grooves on the front and top faces, exactly where the tile surfaces run (X = ±`X1`, Z = 0 and Z = `TS`). The tile lines appear to continue through the hub, giving the reference's block pattern.

### Parameters (defaults)

| Name | Default | Meaning |
|------|---------|---------|
| `T_SHELF`, `T_SIDE` | 8.0 | nominal tile thicknesses |
| `THICK_TOL` | 0.30 | thickness variation handled without reprinting |
| `CLEAR` | 0.40 | slot clearance (total) |
| `CRUSH` | 0.30 | crush rib interference at nominal thickness |
| `HUB` | 48.0 | cube size |
| `COLUMN` | 8.0 | centre column width |
| `CAP` | 5.04 | cap/foot thickness (12 lines) |
| `FRONT` | 5.0 | solid front face (25 layers) |

These give:
- clamp length on each top tile: `HUB/2 − X1` = 20 mm;
- clamp length on each side tile: 34.6 mm;
- corner blocks 11.6 mm wide;
- slot depth 43 mm.

The model asserts that the blocks are at least 8 mm wide and the side clamp is over 25 mm.

## Printing

- **Orientation:** the hub prints front face down. All channels stand vertical, so there are no supports and no overhangs, and the visible front face is the smooth bed side.
- **Plug:** prints back face down.
- **Settings:** PLA, 0.20 mm layers, 4 walls, 20% gyroid infill.
- **Mass:**
  - hub: 70.9 cm³ solid (88 g). Its walls are mostly thicker than 4 perimeters' worth, so expect about 45–55 g at these settings;
  - plug: about 15 g;
  - 3-cube shelf: about 0.9 kg, nearly a full spool. Bambu Studio gives the exact figure.

## Engineering checks (hand calcs)

Assumed tiles: 300×300×8 mm, about 1.7 kg each. A 3-cube row with 10 kg per cube weighs about 50 kg in total.

| Check | Result | Status |
|-------|--------|--------|
| Ceramic bearing, top tile on its side tile edge | 50 N over 8 × 300 mm ≈ 0.02 MPa | negligible |
| Foot compression, per bottom hub (8 hubs) | about 60 N over ≈ 2000 mm² ≈ 0.03 MPa | negligible |
| Tile bending, 300 mm span, 100 N, 8 mm thick | ≈ 2 MPa vs ≥ 35 MPa ceramic | about 17× margin |

**Racking** (no back panels), for a 50 N sideways bump at the top:
- about 1 N·m per top joint, so about 40 N at the cap tip;
- cap as a 20 mm cantilever, 5.04 mm thick, 43 mm deep: stress about 4.4 MPa, deflection about 0.07 mm;
- the corner block is in compression;
- that is roughly 7× stiffer and 3× less stressed than r1.

## Assembly

1. Lay the bottom tiles in a row, glaze up. Slide hubs (cap side down, as feet) onto the front and back corners. Put a plug in the empty channel of each end hub.
2. Drop each cube's two side tiles straight down into the side slots.
3. Lay the top tiles glaze-down, slide on the top hubs (and plugs) front and back, turn the joined top over, and lower it onto the side tiles.
4. Lift the shelf from the bottom. The top lifts off by design.

## Deliverables

- `projects/tile-shelf-connectors/model.py`: parametric `hub`, `plug`, `fit_test` (a 10 mm slice of half a hub) and `thickness_gauge`, plus a digital assembly of the row (preview only).
- `projects/tile-shelf-connectors/test_fit.py`: geometric tests.
- `projects/tile-shelf-connectors/README.md`: workflow, counts, print settings, assembly, print log.

## Verification

1. `check()` on every part: valid, single solid, on the bed, fits the A1.
2. Slot test, for both channels, at nominal and ±0.3 mm thickness: zero body overlap, and crush-rib overlap equal to `CRUSH` + delta. The plug gives zero body overlap and `CRUSH` rib bite.
3. Assembly test of the 3-cube row:
   - every overlap is a rib sliver;
   - no hub-to-hub contact;
   - plugs never touch tiles;
   - middle hubs grip 4 tiles, end hubs 2 tiles and a plug.
4. Visual check in the viewer.
5. Physical: `fit_test` on the user's real tiles before printing the full set, with the result logged in the README.

## Out of scope

Stacking, back panels, coffee table variant, flush top surface. The universal hub could later grow extra channels on the top face for stacking.

## Revision 3: Art Deco styling

**Brief:** turn the hub into an art piece without weakening it, and add matching accent pieces. The user picked the Art Deco direction with accents (hubs, plugs, cornice trims and medallions). They left the colours to me: matte black body with silk gold relief.

### Code split

| File | Contents |
|------|----------|
| `core.py` | Tile channels, crush ribs, plug body, thickness gauge. Unchanged r2 geometry; it takes any outline. |
| `cube.py` | The r2 grooved cube style. |
| `deco.py` | Art Deco style: silhouette, relief, plug, trim and medallion. |
| `model.py` | Builds either style or both (`output/cube/`, `output/deco/`), plus assembly and export. |

Each style module exposes the same interface: `silhouette()`, `hub()`, `plug()`, `CROWN`, `HAS_TRIMS` and `HUB_FACE_UP`. `test_fit.py` runs every check for every style.

### Hub ("skyscraper corner")

- **Crown:** two 1.6 mm tiers on the cap, inset 4 mm and 10 mm. Flipped at the bottom, they become a stepped plinth. The bottom tiles now sit 3.2 mm higher.
- **Corbels:**
  - The corner blocks' outer faces step in by 2 mm at Z = −9, −18 and −27, like stepped stone brackets.
  - The block faces that grip the tiles, and the crush ribs, are untouched.
  - The narrowest block is 5.6 mm, at the bottom, and it is loaded in compression only.
  - The body is 4 cm³ lighter than r2 (66.9 cm³).
- **Corners and edges:** convex silhouette corners and the front-face edges get a 0.6 mm chamfer.
- **Relief:** 1.2 mm raised on the front face, as a separate body for a second filament. It holds a little short of the silhouette edge (`RELIEF_MARGIN` 1.5 mm) and contains:
  - a 3.2 mm spire up the column, through the crown;
  - two 0.9 mm speed lines across the tile band (Z = 0.3 and 0.7 × `TS`);
  - a nine-ray sunburst fan with a half ring, radiating down from where the tiles meet. It becomes a sunrise on the bottom hubs.
- **Print orientation flips to front face up**, so the relief prints as top surfaces. The colour changes are confined to the last 6 layers of each plate (6 filament swaps on an AMS lite). Channels stay vertical, so no supports are needed. The slot lead-ins at the back mouth now sit on the bed as 45° overhangs, which print fine.

### Plug

The same as r2, plus two speed-line grooves on its outer end face, so the hub's front lines carry on around the corner at the ends of the row.

### Cornice trim and medallion

- **Shape:** a C-section clip on the front edge of a top or bottom tile, between two hubs:
  - face 4 mm thick, sitting 1 mm behind the hub face;
  - lips 7 mm deep and 2 mm thick, with 0.8 mm lead-ins;
  - two crush ribs along X on the upper lip;
  - the same ±0.3 mm tolerance as the hubs.
- **Relief:** three gold speed lines.
- **Length:** each span is cut into two trims and a central medallion with 0.5 mm gaps. That is 111 mm per trim for 300 mm tiles (`trim_half_length(pitch)`), because a full span (260 mm) is longer than the A1 bed.
- **Medallion:** 36 mm wide, the same clip plus a stepped keystone (widths 36, 28 and 20 mm, hanging 28 mm below the tile edge, solid back to the lip depth so it prints without supports), with a sunburst relief. On bottom tiles it is rotated 180° about Y, so it points up.
- **Function:** hides and protects the raw tile edges, and adds a stiffening clip to every tile edge.
- **Printing:** face up. The 8.4 mm channel bridges cleanly.

### Counts for N cubes, with trims on top and bottom

- 4(N+1) hubs and 8 plugs;
- 4N trims and 2N medallions.

For 3 cubes that is 16 hubs, 8 plugs, 12 trims and 6 medallions: about 1.1 kg of PLA, mostly black, with about 30 g of gold.

### Verification (r3)

`test_fit.py` covers:
- hub channels, plug, trim and medallion, at nominal and ±0.3 mm thickness;
- the full assembly: no body clashes, each trim and medallion grips exactly one tile, and the relief never touches a tile.

All of it passes.
