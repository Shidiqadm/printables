# Tile shelf connectors

**Status:** test-print
**Created:** 2026-10-11
**Spec:** [design spec (r2, cube hub)](../../docs/superpowers/specs/2026-10-11-tile-shelf-connectors-design.md)

## Purpose

Heavy-duty cube hubs that turn leftover ceramic tiles into a low, single-row cube shelf. They're friction-fit: no glue, screws or tools, and the tiles come back out undamaged.

- Every cube is identical: a top tile, a bottom tile and two side tiles of its own.
- One universal hub sits at every corner.
- At the two ends of the row, a plug fills the unused half of the hub.
- Each top tile rests on the full edge of its side tiles, so the ceramic carries the weight. The hubs locate the tiles and lock the joints against sway.

## Files (in `output/`)

| File | What | For N cubes | For 3 cubes |
|------|------|-------------|-------------|
| `thickness_gauge.3mf` | comb to measure tile thickness (print once) | 1 | 1 |
| `fit_test.3mf` | 10 mm slice of half a hub, to try on real tiles | 1 | 1 |
| `hub.3mf` | universal cube hub (48 mm) | 4 × (N + 1) | 16 |
| `plug.3mf` | fills the empty channel of each end hub | 8 | 8 |
| tiles | | N top, N bottom, 2N side | 3 + 3 + 6 |

A 3-cube shelf takes about 0.9 kg of PLA. Bambu Studio shows the exact weight.

## Workflow

1. **Measure tiles.** Print `thickness_gauge`. Find the narrowest slot each kind of tile slides into, then set `T_SHELF` (top and bottom tiles) and `T_SIDE` (side tiles) in `model.py` to that number minus 0.1.
2. **Regenerate and test.** Run `uv run projects/tile-shelf-connectors/model.py`, then `uv run projects/tile-shelf-connectors/test_fit.py` (it must print ALL PASSED).
3. **Fit test.** Print `fit_test` and push it onto a tile corner, using both the top slot and the side slot. Each tile should need firm hand pressure and stay put when shaken, without needing a mallet.
   - Too tight: lower `CRUSH` by 0.1.
   - Too loose: raise it by 0.1.
4. **Print the set**, then assemble.

## Key parameters

| Name | Default | Notes |
|------|---------|-------|
| `T_SHELF`, `T_SIDE` | 8.0 | nominal tile thicknesses |
| `THICK_TOL` | 0.3 | tiles within ±0.3 of nominal fit without reprinting |
| `CRUSH` | 0.3 | crush-rib bite at nominal thickness |
| `HUB` | 48 | cube size; smaller saves plastic but shortens the clamp |
| `COLUMN` | 8 | gap between neighbouring cubes' side tiles |
| `CAP` | 5.04 | how far the hub stands above the top tiles (and the foot height) |

Tile sizes don't affect the printed parts. Within one cube the top and bottom tiles must be the same length, and both side tiles the same height.

## Print settings (Bambu Studio)

- Material: PLA
- Orientation: as exported. Hub with the grooved front face on the bed; plug standing on its end. No supports, no brim.
- Layer height: 0.20 mm. Walls: 4. Infill: 20% gyroid.
- About 2 h per hub. Four fit on one plate.

## Assembly

1. **Bottom:** lay the bottom tiles in a row, glaze up. Slide hubs onto the front and back corners from the front and back, cap side down (it becomes the foot). Push a plug into the empty channel of each end hub.
2. **Sides:** drop each cube's two side tiles straight down into the side slots.
3. **Top:** lay the top tiles glaze-down and slide on the top hubs (and plugs) front and back. Turn the joined top over and lower it onto the side tiles.
4. Lift the shelf from the bottom, never by the top.

## Print log

| Date | Version | Result | Change for next |
|------|---------|--------|-----------------|
