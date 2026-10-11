# 3D Prints: parametric models for a Bambu Lab A1

This repo is for designing 3D-printable parts as Python code (build123d), previewing them live and exporting files to print in Bambu Studio.

## Setup at a glance

| Thing | Value |
|-------|-------|
| Printer | Bambu Lab A1 + AMS lite (4 slots), open frame, bed-slinger |
| Build volume | 256 x 256 x 256 mm |
| Nozzle | 0.4 mm (line width 0.42 mm) |
| Default layer | 0.20 mm |
| Material | PLA / PLA+ only (no enclosure, so no ABS/ASA) |
| Slicer | Bambu Studio (installed in /Applications) |
| CAD | build123d 0.13 (Python 3.13 via uv), bd_warehouse for fasteners and threads |
| Viewer | standalone OCP viewer at http://localhost:3939 |
| Measuring | the user has **no calipers**: ask for measurements with a ruler, from datasheets, or design adjustable/test-fit pieces |
| Remote | github.com/Shidiqadm/printables (public) |

## Layout

```
CLAUDE.md                 this file
tolerances.toml           fit clearances + fastener hole sizes (single source of truth)
src/printlib/             shared helpers (import as `printlib`)
  printer.py              A1 / PLA constants, wall(n), layers(n)
  tolerances.py           fit("slip"), holes("M3").insert, magnet()
  check.py                check(part): validity, size vs bed, on-bed, mass bound
  export.py               export(part_or_dict, name) -> <model dir>/output/{3mf,step,stl}
  viewer.py               preview(*parts): pushes to the viewer if running, else skips
  gridfinity.py           bin(...), baseplate(...) built from the Gridfinity spec
  cli.py                  `uv run new-project`, `uv run export-all`
  templates/project/      skeleton copied by new-project
projects/<slug>/          one folder per design: model.py, README.md, output/ (gitignored)
calibration/              test prints (tolerance_coupon first)
```

## Commands

```bash
uv run new-project "Desk cable clip"      # scaffold projects/desk-cable-clip/
uv run projects/<slug>/model.py           # build, check, preview, export
uv run export-all                         # rebuild every model
uv run python -m ocp_viewer --port 3939   # live viewer (or preview_start "cad-viewer")
uv run slice <file.stl|3mf> --process "0.28mm Extra Draft @BBL A1" --set wall_loops=3 --copies 4
                                          # headless Bambu Studio slice: real time + grams
```

## Workflow for a new design

1. Ask what it is for, what it mates with, and which dimensions are known vs guessed. Write them in the project README's dimensions table with the source.
2. `uv run new-project "<title>"`, then put every dimension as a named UPPER_CASE parameter at the top of `model.py`.
3. Build with `BuildPart` (builder mode) unless algebra mode is clearly simpler.
4. Run the script. `check()` must show valid, one solid (unless multi-body is intended), on the bed, fits the build volume.
5. Start the viewer (`preview_start` with name `cad-viewer`), push the part, screenshot it in the browser pane and actually look at it before reporting done. Check from below too for anything printed face-down.
6. Tell the user the file to open: `projects/<slug>/output/<slug>.3mf`, plus orientation, supports needed (ideally none), and any special slicer setting.
7. After a test print, log the result in the project README's print log and adjust parameters.

## Design rules (A1, 0.4 nozzle, PLA)

- **Walls**: model as multiples of 0.42 mm. Use `A1.wall(n)`: 2 perimeters = 0.84 (minimum), 3 = 1.26 (default), 4 = 1.68 (structural). Never thinner than 0.84.
- **Floors/tops**: at least 4 layers (0.8 mm); 1.2 mm or more for anything load-bearing.
- **Overhangs**: 45 degrees max without supports. Prefer chamfers over fillets on downward-facing edges.
- **Bridges**: up to about 25 mm is clean in PLA; longer needs a redesign or supports.
- **Bed-side edges**: 0.4 mm chamfer on every edge touching the bed, including the bottom of holes, to cancel elephant's foot.
- **Horizontal holes** (axis parallel to bed): use a teardrop or flat-topped hole to avoid sagging, or orient the part so holes are vertical.
- **Holes print small, pegs print true.** Always take clearances from `fit()` / `holes()`, never hardcode.
- **Text**: at least 4 mm tall with a bold font; engrave or emboss 0.6 mm (3 layers). For AMS color text, make it a separate body and export as a dict.
- **Pin/feature minimum**: around 2 mm diameter for pins, 0.8 mm for ribs.
- **Strength**: layers are the weak axis. Orient so loads run along layers, not peeling them apart. Snap-fit arms should lie flat on the bed.
- **Heat**: PLA softens at about 55 C, so warn about car interiors, sunny windows and anything near heat.
- **Fasteners**: prefer heat-set inserts for parts that get reassembled; self-tapping holes (`holes("M3").tap`) for screw-once parts; captive nut traps when inserts aren't available. Use `bd_warehouse.fastener` for exact screw/nut/insert geometry.
- **Print-in-place**: gap of `fit("gap", "print_in_place")` mm (0.35 default).
- **Multi-color (AMS)**: up to 4 filaments. Export bodies as `export({"base": a, "text": b}, name)`; they become separate objects in the 3MF so each gets its own filament.
- **Size**: the bed is 256 x 256 mm, but leave around 5 mm margin. Split large parts with alignment pins or dovetails.

## Print-time findings (A1, PLA, measured with `uv run slice`)

- Chunky parts are limited by how fast PLA melts (volumetric flow): **print time tracks grams**. Speed overrides do nothing.
- The levers that do work:
  - layer height: 0.20 to 0.28 mm is about −19%, and XY fit is unaffected;
  - wall count: each extra loop costs a lot on parts with many slot walls;
  - less model volume.
- Plating many copies saves only about 0.5 min of overhead per plate. Prefer small batches (about 3 h plates) so one failure costs little.
- Slice a design before claiming a print time. Ship `print_plan.py`-style sliced `.gcode.3mf` plates when the user wants ready-to-print files.

## Tolerances

`tolerances.toml` holds every clearance. Until `[calibration].calibrated = true` the values are generic defaults; mention this when a fit matters, and suggest printing `calibration/tolerance_coupon` if not done yet. When the user reports coupon results, update the `[fit.*]` values (number on the coupon / 100 = clearance in mm), set `calibrated = true`, the date and a short note.

## Gridfinity

Use `printlib.gridfinity` (`bin(gx, gy, units, divisions=(nx, ny), magnets=True, lip=True)` and `baseplate(gx, gy)`). It was written from the spec because the third-party gridfinity_build123d package is incompatible with build123d 0.13. Stacking and baseplate fit were verified by interference checks. Max baseplate on the A1 is 6x6 (252 mm).

## Conventions

- Units are millimetres. Z is up; the bed is the XY plane at Z=0; parts are modelled in print orientation.
- Every model script ends with the `if __name__ == "__main__":` block calling `check`, `preview`, `export`.
- `output/` folders are gitignored (regenerable). STEP and 3MF are the deliverables; STL is for Printables uploads.
- Git identity for this repo is the GitHub noreply address set in `.git/config`. Never use the work email anywhere in this repo (commits, files, metadata).
