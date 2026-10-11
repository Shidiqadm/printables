# Tile shelf connectors

**Status:** test-print
**Created:** 2026-10-11
**Spec:** [design spec](../../docs/superpowers/specs/2026-10-11-tile-shelf-connectors-design.md)

## Purpose

Friction-fit corner connectors that turn leftover ceramic tiles into a low, single-row cube shelf. No glue, screws or tools, and the tiles can be taken back out undamaged. Neighbouring cubes share one side tile. The top tiles rest directly on the side tiles' edges, so the ceramic carries the weight and the plastic only locates and stiffens the joints.

## Files (in `output/`)

| File | What | Per shelf of N cubes |
|------|------|----------------------|
| `thickness_gauge.3mf` | comb to measure tile thickness (print once) | 1 |
| `fit_test.3mf` | short middle connector to try on your real tiles | 1 |
| `middle.3mf` | connector at the inner side tiles | 4 × (N − 1) |
| `end.3mf` | end connector | 4 |
| `end_mirrored.3mf` | mirror-image end connector | 4 |

For a 3-cube shelf: 8 × middle, 4 × end, 4 × end_mirrored. That's about 400 g of PLA, plus 3 top, 3 bottom and 4 side tiles.

## Workflow

1. **Measure tiles.** Print `thickness_gauge`. Find the narrowest slot each kind of tile slides into, then set `T_SHELF` (top and bottom tiles) and `T_SIDE` (side tiles) in `model.py` to that number minus 0.1.
2. **Regenerate.** Run `uv run projects/tile-shelf-connectors/model.py`, then `uv run projects/tile-shelf-connectors/test_fit.py` (it must print ALL PASSED).
3. **Fit test.** Print `fit_test` and push it onto a tile corner, using both slots. Each tile should go in with firm hand pressure and stay put when shaken, without needing a mallet.
   - Too tight: lower `CRUSH` by 0.1.
   - Too loose: raise it by 0.1.
4. **Print the set**, then assemble.

## Key parameters

| Name | Default | Notes |
|------|---------|-------|
| `T_SHELF`, `T_SIDE` | 8.0 | nominal tile thicknesses |
| `THICK_TOL` | 0.3 | tiles within ±0.3 of nominal fit without reprinting |
| `CRUSH` | 0.3 | crush-rib bite at nominal thickness (0 at −0.3, 0.6 at +0.3) |
| `ARM` | 28 | clamp reach along each tile (stiffness against sway) |
| `DEPTH` | 30 | reach back along the tile edges |
| `CAP` | 4.2 | cap over the top tiles / foot under the bottom tiles |

Tile sizes don't affect the printed parts. Any size works, but within one cube the top and bottom tiles must be the same length, and all side tiles the same height.

## Print settings (Bambu Studio)

- Material: PLA
- Orientation: as exported, front plate flat on the bed. No supports, no brim.
- Layer height: 0.20 mm. Walls: 4. Infill: 30% gyroid.
- About 1–1.5 h per middle connector. Plate several at once.

## Assembly

1. Lay the bottom tiles in a row, glaze up. Slide bottom connectors (cap side down = feet) onto the front and back corners:
   - `end` / `end_mirrored` at both ends of the row;
   - `middle` where two tiles meet.
2. Drop the side tiles straight down into the vertical slots.
3. Lay the top tiles glaze-down and slide the top connectors onto their front and back edges. Turn the joined top over and lower it onto the side tiles.
4. Lift the shelf from the bottom, never by the top.

Which end part goes where, looking at the shelf from the front:

| | Front-top | Front-bottom | Back-top | Back-bottom |
|---|---|---|---|---|
| Left end | end | end_mirrored | end_mirrored | end |
| Right end | end_mirrored | end | end | end_mirrored |

If a connector's open wing points out of the shelf instead of along the tile, it's the wrong end type.

## Print log

| Date | Version | Result | Change for next |
|------|---------|--------|-----------------|
