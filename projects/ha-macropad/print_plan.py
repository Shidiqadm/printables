"""Slice ready-to-print Bambu Lab A1 plates for an HK remote, with the quality settings baked in.

Run:  uv run projects/ha-macropad/print_plan.py [hk22 | hk4] [test | all]   (after model.py; default hk22)
      uv run projects/ha-macropad/print_plan.py coupon   the stem test, output/coupon/stem-test.gcode.3mf
Out:  projects/ha-macropad/output/<slug>/print/
        1_shell.gcode.3mf         the shell, deck on the bed
        2_plate_base.gcode.3mf    switch plate + base (plain base: no AMS label swap)
        3_keycaps.gcode.3mf       4 keycaps (pick the orange filament for one in Bambu Studio)
        0_test_plate_keycap.gcode.3mf   with "test": the plate and one keycap, to check the
                                  switch fit, the snaps and the stem fit before the full set
        <slug>-all-parts.gcode.3mf      with "all": every part on one plate (shell, plate, base,
                                  4 keycaps)

Each file is a sliced Bambu Studio project: open it to check, or send it straight to the
printer. Why these settings (found by slicing and comparing every layer against the model,
see README "Print settings"):
  - Arachne walls: the classic wall generator left small voids round the speaker grille, the
    LED dots and the plate corners, where a wall is not a whole number of lines wide.
    Arachne varies the line width to fill them.
  - Slow outer walls on the shell: 60 mm/s at 2000 mm/s2 (Bambu's High Quality values), so
    the walls show no ringing. It stays at 0.20 mm layers: every height in the model (plate
    seat, snap catches, sensor cradle) sits on a 0.2 mm layer line.
  - Slow first layer: the shell's deck (the face you see) and the base's underside are the
    first layer, so they get 30 mm/s and 60 mm/s solid infill for well-fused lines.
  - Seam at the back: the shell is turned over left-to-right, so the seam lands on the
    USB-C wall.
  - Normal layer-by-layer printing. "By object" (each part finished before the next) would
    stop strings between parts, but Bambu Studio then keeps a wide print-head clearance round
    every part, so the parts can't be arranged freely. Cooler PLA (210 C) and travel round
    the walls keep the strings down instead.
"""

import sys
import zipfile
from pathlib import Path

from printlib.slicer import slice_model

HERE = Path(__file__).parent
OUT = HERE / "output"

QUALITY = {
    "wall_generator": "arachne",
    "wall_loops": "3",
    "seam_position": "back",
    "initial_layer_speed": "30",
    "initial_layer_infill_speed": "60",
    "reduce_crossing_wall": "1",       # travel round walls, not across the visible ones
    "enable_support": "0",
    "brim_type": "no_brim",
    "sparse_infill_density": "15%",
}
SHELL = {"outer_wall_speed": "60", "outer_wall_acceleration": "2000", "inner_wall_speed": "150"}
# Keycaps print top-down at 0.20 mm, like the fit coupon's posts, so the socket fits the same.
# Every plate: the flow cap keeps 210 C hot enough for any PLA (full walls, no gaps) and cool enough to
# string less than the 220 C preset.
COOL = {"nozzle_temperature": ["210"], "nozzle_temperature_initial_layer": ["215"],
        "filament_max_volumetric_speed": ["12"]}


def plates(slug: str) -> dict:
    o = OUT / slug
    return {
        "1_shell": ("0.20mm Standard @BBL A1", [(o / f"{slug}-shell.stl", 1)], SHELL),
        # 0.20 mm: the 1.6 mm plate and the 2.0 mm base are whole numbers of layers
        "2_plate_base": ("0.20mm Standard @BBL A1", [(o / f"{slug}-plate.stl", 1), (o / f"{slug}-base-base.stl", 1)],
                         {}),
        "3_keycaps": ("0.20mm Standard @BBL A1", [(o / f"{slug}-keycap.stl", 4)], SHELL),
    }


# All parts on one plate, every height on the 0.2 mm grid.


def all_parts(slug: str) -> dict:
    o = OUT / slug
    return {f"{slug}-all-parts": ("0.20mm Standard @BBL A1",
                                  [(o / f"{slug}-shell.stl", 1), (o / f"{slug}-plate.stl", 1),
                                   (o / f"{slug}-base-base.stl", 1), (o / f"{slug}-keycap.stl", 4)], SHELL)}


def test_plate(slug: str) -> dict:
    o = OUT / slug
    return {"0_test_plate_keycap": ("0.20mm Standard @BBL A1",
                                    [(o / f"{slug}-plate.stl", 1), (o / f"{slug}-keycap.stl", 1)], SHELL)}


def coupon() -> dict:
    """The stem test alone, with the keycaps' settings, so its sockets print like theirs."""
    return {"stem-test": ("0.20mm Standard @BBL A1", [(OUT / "coupon" / "stem-test.stl", 1)], SHELL)}


def main() -> None:
    slug = next((a for a in sys.argv[1:] if a in ("hk22", "hk4")), "hk22")
    test, every = "test" in sys.argv[1:], "all" in sys.argv[1:]
    stems = "coupon" in sys.argv[1:]
    out = OUT / "coupon" if stems else OUT / slug / "print"
    out.mkdir(parents=True, exist_ok=True)
    total_min = total_g = 0.0
    chosen = coupon() if stems else test_plate(slug) if test else all_parts(slug) if every else plates(slug)
    for name, (process, parts, extra) in chosen.items():
        missing = [p for p, _ in parts if not p.exists()]
        if missing:
            sys.exit(f"missing {missing}: run model.py first")
        r = slice_model(parts, process, {**QUALITY, **extra}, out_dir=out, name=name,
                        filament_overrides=COOL)
        with zipfile.ZipFile(r.output) as z:  # keep the plate preview next to the file
            png = next((n for n in z.namelist() if n.endswith("plate_1.png")), None)
            if png:
                (out / f"{name}.png").write_bytes(z.read(png))
        total_min += r.minutes
        total_g += r.grams
        print(f"{name}: {r}")
    h, m = divmod(round(total_min), 60)
    what = "stem test" if stems else "test" if test else "for one " + slug
    print(f"total {what}: {h}h{m:02d}m, {total_g:.0f} g PLA")


if __name__ == "__main__":
    main()
