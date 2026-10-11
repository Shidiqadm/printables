# Tile shelf connectors: cube and Art Deco styles

**Status:** test-print
**Created:** 2026-10-11
**Spec:** [design spec (r3)](../../docs/superpowers/specs/2026-10-11-tile-shelf-connectors-design.md)

## Purpose

Heavy-duty cube hubs that turn leftover ceramic tiles into a low, single-row cube shelf. They're friction-fit: no glue, screws or tools, and the tiles come back out undamaged. Each top tile rests on the full edge of its side tiles, so the ceramic carries the weight; the plastic locates the tiles and locks the joints against sway.

There are two styles. Both share the same tile channels and grip (`core.py`), so they fit the same tiles identically, and you can even mix them in one shelf.

| Style | Look | Pieces | Colours |
|-------|------|--------|---------|
| **cube** (`cube.py`) | Grooved 44 mm-wide block with a 3×3 pattern, like the reference photos. Slimmed for fast printing: 20 mm front to back, side tiles clamped 24 mm. | hub, plug | one colour, e.g. terracotta |
| **deco** (`deco.py`) | 48 mm "skyscraper corner": stepped crown/plinth, stepped corbels, gold spire, speed lines and sunburst | hub, plug, cornice trim, keystone medallion | matte black + silk gold |

## Files (in `output/`)

| File | What | For N cubes | For 3 cubes |
|------|------|-------------|-------------|
| `thickness_gauge.3mf` | comb to measure tile thickness (print once, shared) | 1 | 1 |
| `<style>/fit_test.3mf` | 10 mm slice of half a hub, to try on real tiles | 1 | 1 |
| `<style>/hub.3mf` | universal hub (deco: body + gold relief) | 4 × (N + 1) | 16 |
| `<style>/plug.3mf` | fills the empty channel of each end hub | 8 | 8 |
| `cube/mid_hub.3mf` | middle hub joining two stacked rows (44 × 56 × 20 mm) | 2 × (N + 1) per extra row | 8 |
| `cube/mid_plug.3mf` | T-shaped plug for the end middle hubs | 4 per extra row | 4 |
| `deco/trim.3mf` | cornice clip for a tile's front edge, body + gold lines | 4 × N | 12 |
| `deco/medallion.3mf` | mid-span keystone clip with sunburst, body + gold relief | 2 × N | 6 |
| tiles, 1 row | | N top, N bottom, 2N side | 3 + 3 + 6 |
| tiles, R rows | | N × (R + 1) shelf, 2N × R side | 2 rows: 9 shelf + 12 side |

PLA for a 3-cube shelf:
- **cube:** 3 cubes × 2 rows comes to 439 g and 10 h 55 min, as sliced by Bambu Studio, test plate included.
- **deco:** about 1.1 kg with trims, roughly 30 g of it gold. The trims and medallions are optional.

## Workflow

1. **Measure tiles.** Print `thickness_gauge`. Find the narrowest slot each kind of tile slides into, then set `T_SHELF` (top and bottom tiles) and `T_SIDE` (side tiles) in `core.py` to that number minus 0.1. Set `TILE_W` in `model.py` to your top tile length; this sizes the trims.
2. **Regenerate and test.** Run `uv run projects/tile-shelf-connectors/model.py` (both styles; add `cube` or `deco` to build one), then `uv run projects/tile-shelf-connectors/test_fit.py` (it must print ALL PASSED).
3. **Fit test.** Print `fit_test` and push it onto a tile corner, using both slots. Each tile should need firm hand pressure and stay put when shaken, without needing a mallet.
   - Too tight: lower `CRUSH` in `core.py` by 0.1.
   - Too loose: raise it by 0.1.
4. **Print the set**, then assemble.

### Fastest route for the cube style: ready-sliced plates

`uv run projects/tile-shelf-connectors/print_plan.py` slices ready-to-print Bambu projects into `output/cube/print/`. Open them in Bambu Studio, or send them straight to the A1.

| File | Contents | Time | PLA | Print |
|------|----------|------|-----|-------|
| `1_test_plate.gcode.3mf` | thickness gauge + fit test | 27 min | 16 g | once, first |
| `2_hub_plate.gcode.3mf` | 8 hubs + 4 plugs | 3 h 07 min | 124 g | 2 times |
| `3_mid_plate.gcode.3mf` | 8 middle hubs + 4 mid plugs (only for stacking) | 4 h 14 min | 176 g | once per extra row |

A 3-cube × 2-row shelf comes to 10 h 55 min and 439 g of PLA. Set `CUBES` and `ROWS` in `model.py`; `print_plan.py` works out the repeats.

The slices assume Bambu PLA Basic. With another PLA, pick that filament in Bambu Studio and re-slice. The time barely changes.

Re-run `model.py cube` and `print_plan.py` after changing tile thickness or `CRUSH`. The test plate and hub plate must use the same settings, because the grip depends on them.

## Print settings (Bambu Studio)

**cube** (as embedded in the sliced plates)

| Setting | Value | Why |
|---------|-------|-----|
| Printer | Bambu Lab A1, 0.4 mm nozzle | |
| Process preset | 0.28mm Extra Draft @BBL A1 | 19% faster than 0.20 Standard. Slot widths are set by XY moves, not layer height, so the fit is unaffected. |
| Wall loops | 3 | Sturdy cap and clamp faces. Costs 6 min per hub over 2 walls. |
| Sparse infill | 15% grid | Fastest pattern. Plenty, since the blocks only take compression. |
| Supports / brim | none / none | Nothing overhangs, and a 44 mm footprint sticks fine on textured PEI. |
| Orientation | hub: grooved face down; plug: lying on its side | Smooth bed finish on the visible face. The plug is 18 mm tall instead of a 39 mm column, so it stays steady on the moving bed. |
| Elephant-foot compensation | 0.075 (preset) | The model also has 1 mm chamfers on the bed edges. |

**How these were chosen:** by slicing variants headless in Bambu Studio (`uv run slice <file> --process ... --set key=value`).
- Time tracks grams, because the hub is limited by how fast PLA melts. Raising speed settings changed nothing.
- Plating more hubs together barely helps: about 0.5 min of overhead per plate.
- The real levers were layer height (0.20 to 0.28: −19%), the 48 to 44 mm cube (−20%) and wall count.

| Variant | Per hub |
|---------|---------|
| 48 mm, 0.20 Standard, 2 walls (Bambu defaults) | 58 min, 32 g |
| 48 mm, 0.28, 3 walls | 55 min, 39 g |
| 44 mm, 0.28, 3 walls | 44 min, 31 g |
| 44 mm, 0.28, 2 walls | 38 min, 26 g |
| **44 mm face, 20 mm thick, 24 mm clamp, 0.28, 3 walls (chosen)** | **22 min, 14 g** |

**Slimming:** after the first test print showed that a 10 mm-deep grip already holds, the hub was made 20 mm thick front to back (print height) instead of 44, and the side-tile clamp was cut from 30.6 to 24 mm. The middle hub drops from 69.5 to 56 mm tall.
- Hubs for a 3×2 shelf: 20.1 h / 864 g → 9.7 h / 381 g.
- The tile slots, grip and tile-on-tile load path are unchanged. Sway stiffness drops to about 30% of the full cube, which is still fine for light decor (cap stress about 11 MPa under a 50 N bump, against PLA's roughly 50 MPa).
- Set it with `DIMS = Hub(44, thick=..., clamp=...)` in `cube.py`.

**deco** (not yet optimised like the cube style)
- PLA, 0.20 mm layers, 4 walls, 20% gyroid infill, no supports, no brim.
- Hub, trim and medallion print decorated face up.
- **Two colours:** each of these files contains two parts, body and relief. When Bambu Studio asks whether to load them as a single object with multiple parts, answer **Yes**. Then set the body to matte black PLA and the relief to silk gold PLA. The colour change only happens in the last ~6 layers, so filament waste is tiny.
- **Top surface:** turn on **ironing** (top surfaces only) for a glassy finish on the faces.

## Key parameters

| File | Name | Default | Notes |
|------|------|---------|-------|
| core.py | `T_SHELF`, `T_SIDE` | 8.0 | nominal tile thicknesses |
| core.py | `THICK_TOL` | 0.3 | tiles within ±0.3 of nominal fit without reprinting |
| core.py | `CRUSH` | 0.3 | crush-rib bite at nominal thickness |
| cube.py | `DIMS = Hub(44, thick=20, clamp=24)` | | face size, print height, side clamp |
| deco.py | `DIMS = Hub(48)` | | full 48 mm cube |
| cube.py | `ROUND`, `GROOVE_W` | 2, 1.0 | edge radius and groove width |
| deco.py | `CROWN_INSETS`, `CORBEL_LEVELS` | | crown tiers and corbel setbacks |
| deco.py | `RAY_ANGLES`, `RELIEF` | 9 rays, 1.2 mm | sunburst and relief height |
| model.py | `TILE_W`, `CUBES` | 300, 3 | sets the trim length and the preview |

## Assembly

1. **Bottom:** lay the bottom tiles in a row, glaze up. Slide hubs onto the front and back corners, cap side down (on deco hubs the crown becomes the plinth). Push a plug into the empty channel of each end hub.
2. **Sides:** drop each cube's two side tiles straight down into the side slots.
3. **Top:** lay the top tiles glaze-down and slide on the top hubs (and plugs). Turn the joined top over and lower it onto the side tiles.
4. **Stacking a second row (cube style):** instead of top hubs on the first row, lay its top tiles and slide on **middle hubs**, with mid plugs at the ends. Each middle hub takes the first row's side tiles from below, the shared shelf tile in the middle, and the second row's side tiles from above. Drop in the second row's side tiles, then finish with normal top hubs.
   - The first row's top tile is the second row's floor, so the weight still goes tile on tile all the way down.
   - Keep heavy items on the lower row. If children or pets could climb it, strap it to the wall.
5. **Trims (deco only):** clip trims onto the front edge of every top and bottom tile, with the medallion in the middle. On bottom tiles, the keystone points up.
6. Lift the shelf from the bottom, never by the top.

## Print log

| Date | Version | Result | Change for next |
|------|---------|--------|-----------------|
