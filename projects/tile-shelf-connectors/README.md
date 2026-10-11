# Tile shelf: Art Deco edition

**Status:** test-print
**Created:** 2026-10-11
**Spec:** [design spec (r3)](../../docs/superpowers/specs/2026-10-11-tile-shelf-connectors-design.md)

## Purpose

Sculptural, heavy-duty cube hubs that turn leftover ceramic tiles into a low, single-row cube shelf. They're friction-fit: no glue, screws or tools, and the tiles come back out undamaged.

- **Hubs:** a "skyscraper corner" in matte black with silk gold relief. Each has a stepped crown (a plinth when used at the bottom), stepped corbels, a spire, speed lines and a sunburst fan.
- **Cornice trims:** clip onto each tile's front edge, with a sunburst keystone medallion at mid-span.
- **Load path:** each top tile rests on the full edge of its side tiles, so the ceramic carries the weight. The plastic locates the tiles and locks the joints against sway.

## Files (in `output/`)

| File | What | For N cubes | For 3 cubes |
|------|------|-------------|-------------|
| `thickness_gauge.3mf` | comb to measure tile thickness (print once) | 1 | 1 |
| `fit_test.3mf` | 10 mm slice of half a hub, to try on real tiles | 1 | 1 |
| `hub.3mf` | universal hub, body + gold relief | 4 × (N + 1) | 16 |
| `plug.3mf` | fills the empty channel of each end hub | 8 | 8 |
| `trim.3mf` | cornice clip for a tile's front edge, body + gold lines | 4 × N | 12 |
| `medallion.3mf` | mid-span keystone clip with sunburst, body + gold relief | 2 × N | 6 |
| tiles | | N top, N bottom, 2N side | 3 + 3 + 6 |

- Trims and medallions are optional. Set `TRIMS = False` in `model.py` to drop them from the preview.
- A 3-cube shelf takes about 1.1 kg of PLA, almost all black, with about 30 g of gold.

## Workflow

1. **Measure tiles.** Print `thickness_gauge`. Find the narrowest slot each kind of tile slides into, then set `T_SHELF` (top and bottom tiles) and `T_SIDE` (side tiles) in `core.py` to that number minus 0.1. Set `TILE_W` in `model.py` to your top tile length; this sizes the trims.
2. **Regenerate and test.** Run `uv run projects/tile-shelf-connectors/model.py`, then `uv run projects/tile-shelf-connectors/test_fit.py` (it must print ALL PASSED).
3. **Fit test.** Print `fit_test` and push it onto a tile corner, using both slots. Each tile should need firm hand pressure and stay put when shaken, without needing a mallet.
   - Too tight: lower `CRUSH` in `core.py` by 0.1.
   - Too loose: raise it by 0.1.
4. **Print the set**, then assemble.

## Print settings (Bambu Studio)

- **Two colours:** `hub`, `trim` and `medallion` each contain two parts, body and relief. When Bambu Studio asks whether to load them as a single object with multiple parts, answer **Yes**. Then set the body to matte black PLA and the relief to silk gold PLA. The colour change only happens in the last ~6 layers, so filament waste is tiny.
- **Orientation:** as exported, decorated face up. Plug and fit test stand on their back ends. No supports, no brim.
- **Layers and walls:** 0.20 mm layers, 4 walls, 20% gyroid infill.
- **Top surface:** turn on **ironing** (top surfaces only) for a glassy finish on the faces.
- **Time:** about 2 h per hub. Four hubs fit on one plate.

## Key parameters

| File | Name | Default | Notes |
|------|------|---------|-------|
| core.py | `T_SHELF`, `T_SIDE` | 8.0 | nominal tile thicknesses |
| core.py | `THICK_TOL` | 0.3 | tiles within ±0.3 of nominal fit without reprinting |
| core.py | `CRUSH` | 0.3 | crush-rib bite at nominal thickness |
| core.py | `HUB` | 48 | cube size |
| deco.py | `CROWN_INSETS`, `CORBEL_LEVELS` | | crown tiers and corbel setbacks |
| deco.py | `RAY_ANGLES`, `RELIEF` | 9 rays, 1.2 mm | sunburst and relief height |
| model.py | `TILE_W`, `CUBES`, `TRIMS` | 300, 3, on | sets trim length and the preview |

## Assembly

1. **Bottom:** lay the bottom tiles in a row, glaze up. Slide hubs onto the front and back corners, crown down (it becomes the plinth). Push a plug into the empty channel of each end hub.
2. **Sides:** drop each cube's two side tiles straight down into the side slots.
3. **Top:** lay the top tiles glaze-down and slide on the top hubs (and plugs). Turn the joined top over and lower it onto the side tiles.
4. **Trims:** clip trims onto the front edge of every top and bottom tile, with the medallion in the middle. On bottom tiles, the keystone points up.
5. Lift the shelf from the bottom, never by the top.

## Print log

| Date | Version | Result | Change for next |
|------|---------|--------|-----------------|
