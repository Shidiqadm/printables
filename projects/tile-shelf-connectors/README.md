# Tile shelf connectors: cube and Art Deco styles

**Status:** test-print
**Created:** 2026-10-11
**Spec:** [design spec (r3)](../../docs/superpowers/specs/2026-10-11-tile-shelf-connectors-design.md)

## Purpose

Heavy-duty cube hubs that turn leftover ceramic tiles into a low, single-row cube shelf. They're friction-fit: no glue, screws or tools, and the tiles come back out undamaged. Each top tile rests on the full edge of its side tiles, so the ceramic carries the weight; the plastic locates the tiles and locks the joints against sway.

There are two styles. Both share the same tile channels and grip (`core.py`), so they fit the same tiles identically, and you can even mix them in one shelf.

| Style | Look | Pieces | Colours |
|-------|------|--------|---------|
| **cube** (`cube.py`) | Grooved 48 mm cube with a 3×3 block pattern, like the reference photos | hub, plug | one colour, e.g. terracotta |
| **deco** (`deco.py`) | "Skyscraper corner": stepped crown/plinth, stepped corbels, gold spire, speed lines and sunburst | hub, plug, cornice trim, keystone medallion | matte black + silk gold |

## Files (in `output/`)

| File | What | For N cubes | For 3 cubes |
|------|------|-------------|-------------|
| `thickness_gauge.3mf` | comb to measure tile thickness (print once, shared) | 1 | 1 |
| `<style>/fit_test.3mf` | 10 mm slice of half a hub, to try on real tiles | 1 | 1 |
| `<style>/hub.3mf` | universal hub (deco: body + gold relief) | 4 × (N + 1) | 16 |
| `<style>/plug.3mf` | fills the empty channel of each end hub | 8 | 8 |
| `deco/trim.3mf` | cornice clip for a tile's front edge, body + gold lines | 4 × N | 12 |
| `deco/medallion.3mf` | mid-span keystone clip with sunburst, body + gold relief | 2 × N | 6 |
| tiles | | N top, N bottom, 2N side | 3 + 3 + 6 |

PLA for a 3-cube shelf:
- **cube:** about 0.9 kg.
- **deco:** about 1.1 kg with trims, roughly 30 g of it gold. The trims and medallions are optional.

## Workflow

1. **Measure tiles.** Print `thickness_gauge`. Find the narrowest slot each kind of tile slides into, then set `T_SHELF` (top and bottom tiles) and `T_SIDE` (side tiles) in `core.py` to that number minus 0.1. Set `TILE_W` in `model.py` to your top tile length; this sizes the trims.
2. **Regenerate and test.** Run `uv run projects/tile-shelf-connectors/model.py` (both styles; add `cube` or `deco` to build one), then `uv run projects/tile-shelf-connectors/test_fit.py` (it must print ALL PASSED).
3. **Fit test.** Print `fit_test` and push it onto a tile corner, using both slots. Each tile should need firm hand pressure and stay put when shaken, without needing a mallet.
   - Too tight: lower `CRUSH` in `core.py` by 0.1.
   - Too loose: raise it by 0.1.
4. **Print the set**, then assemble.

## Print settings (Bambu Studio)

Both styles: PLA, 0.20 mm layers, 4 walls, 20% gyroid infill, no supports, no brim. Print as exported. About 2 h per hub; four hubs fit on one plate.

**cube**
- The hub prints grooved face down, so the visible face gets the smooth bed finish.

**deco**
- Hub, trim and medallion print decorated face up.
- **Two colours:** each of these files contains two parts, body and relief. When Bambu Studio asks whether to load them as a single object with multiple parts, answer **Yes**. Then set the body to matte black PLA and the relief to silk gold PLA. The colour change only happens in the last ~6 layers, so filament waste is tiny.
- **Top surface:** turn on **ironing** (top surfaces only) for a glassy finish on the faces.

## Key parameters

| File | Name | Default | Notes |
|------|------|---------|-------|
| core.py | `T_SHELF`, `T_SIDE` | 8.0 | nominal tile thicknesses |
| core.py | `THICK_TOL` | 0.3 | tiles within ±0.3 of nominal fit without reprinting |
| core.py | `CRUSH` | 0.3 | crush-rib bite at nominal thickness |
| core.py | `HUB` | 48 | cube size |
| cube.py | `ROUND`, `GROOVE_W` | 2, 1.0 | edge radius and groove width |
| deco.py | `CROWN_INSETS`, `CORBEL_LEVELS` | | crown tiers and corbel setbacks |
| deco.py | `RAY_ANGLES`, `RELIEF` | 9 rays, 1.2 mm | sunburst and relief height |
| model.py | `TILE_W`, `CUBES` | 300, 3 | sets the trim length and the preview |

## Assembly

1. **Bottom:** lay the bottom tiles in a row, glaze up. Slide hubs onto the front and back corners, cap side down (on deco hubs the crown becomes the plinth). Push a plug into the empty channel of each end hub.
2. **Sides:** drop each cube's two side tiles straight down into the side slots.
3. **Top:** lay the top tiles glaze-down and slide on the top hubs (and plugs). Turn the joined top over and lower it onto the side tiles.
4. **Trims (deco only):** clip trims onto the front edge of every top and bottom tile, with the medallion in the middle. On bottom tiles, the keystone points up.
5. Lift the shelf from the bottom, never by the top.

## Print log

| Date | Version | Result | Change for next |
|------|---------|--------|-----------------|
