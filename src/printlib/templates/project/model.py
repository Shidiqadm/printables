"""__TITLE__

Run:     uv run projects/__SLUG__/model.py
Outputs: projects/__SLUG__/output/  (3MF for Bambu Studio, STEP, STL)
"""

from build123d import *

from printlib import A1, check, export, fit, holes, preview

# ---- Parameters (mm) -------------------------------------------------------
WIDTH = 40.0
DEPTH = 20.0
HEIGHT = 10.0
WALL = A1.wall(3)          # 1.26 mm = 3 perimeters
CHAMFER_BOTTOM = 0.4       # hides elephant's foot on the first layer
EDGE_FILLET = 1.0

# ---- Model -----------------------------------------------------------------
with BuildPart() as model:
    Box(WIDTH, DEPTH, HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN))
    fillet(model.edges().filter_by(Axis.Z), EDGE_FILLET)
    chamfer(model.edges().group_by(Axis.Z)[0], CHAMFER_BOTTOM)
    with Locations((0, 0, HEIGHT)):
        Hole(holes("M3").clearance / 2)

part = model.part

# ---- Output ----------------------------------------------------------------
if __name__ == "__main__":
    check(part, "__SLUG__")
    preview(part)
    export(part, "__SLUG__")
