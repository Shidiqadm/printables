"""Slice ready-to-print Bambu Lab A1 plates for the cube-style tile shelf.

Run:  uv run projects/tile-shelf-connectors/print_plan.py      (after model.py)
Out:  projects/tile-shelf-connectors/output/cube/print/
        1_test_plate.gcode.3mf   thickness gauge + fit test   (print once, first)
        2_hub_plate.gcode.3mf    4 hubs + 2 plugs             (print 4x for a 3-cube shelf)
        3_mid_plate.gcode.3mf    4 middle hubs + 2 mid plugs  (print 2x per extra row)

Each file is a sliced Bambu Studio project: open it to check, or send it straight to the
printer. Settings were picked by slicing variants in Bambu Studio (see README):
0.28mm Extra Draft preset + 3 walls is the fastest that keeps the hub sturdy, because the
hub is limited by how fast PLA can be melted (time tracks grams), not by motion speed.
"""

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from model import CUBES, ROWS  # noqa: E402
from printlib.slicer import slice_model  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "output"
PRINT_DIR = OUT / "cube" / "print"

PROCESS = "0.28mm Extra Draft @BBL A1"
OVERRIDES = {
    "wall_loops": "3",            # 1.26 mm walls: sturdy cap/clamp; +6 min/hub vs 2 walls
    "sparse_infill_density": "15%",
    "sparse_infill_pattern": "grid",   # fastest pattern on Bambu; plenty for compression
    "enable_support": "0",        # nothing overhangs
    "brim_type": "no_brim",       # 44 mm footprint sticks fine on textured PEI
}

PLATES = {
    "1_test_plate": [(OUT / "thickness_gauge.stl", 1), (OUT / "cube" / "fit_test.stl", 1)],
    "2_hub_plate": [(OUT / "cube" / "hub.stl", 4), (OUT / "cube" / "plug.stl", 2)],
    "3_mid_plate": [(OUT / "cube" / "mid_hub.stl", 4), (OUT / "cube" / "mid_plug.stl", 2)],
}
# hubs: 4 per joint line (front/back x top/bottom); plugs: 8 at the ends. Each plate = 4 + 2.
REPEATS = {
    "1_test_plate": 1,
    "2_hub_plate": (4 * (CUBES + 1)) // 4,              # top + bottom hubs
    "3_mid_plate": (2 * (CUBES + 1) * (ROWS - 1)) // 4,  # middle hubs between rows
}


def main() -> None:
    PRINT_DIR.mkdir(parents=True, exist_ok=True)
    total_min = total_g = 0.0
    for name, parts in PLATES.items():
        if REPEATS[name] == 0:
            continue
        missing = [p for p, _ in parts if not p.exists()]
        if missing:
            sys.exit(f"missing {missing}: run model.py first")
        r = slice_model(parts, PROCESS, OVERRIDES, out_dir=PRINT_DIR, name=name)
        with zipfile.ZipFile(r.output) as z:     # keep the plate preview next to the file
            png = next((n for n in z.namelist() if n.endswith("plate_1.png")), None)
            if png:
                (PRINT_DIR / f"{name}.png").write_bytes(z.read(png))
        n = REPEATS[name]
        total_min += r.minutes * n
        total_g += r.grams * n
        print(f"{name}: {r}  (print x{n})")
    h, m = divmod(round(total_min), 60)
    print(f"total for a {CUBES}-cube x {ROWS}-row shelf: {h}h{m:02d}m, {total_g:.0f} g PLA")


if __name__ == "__main__":
    main()
