"""Fit-tolerance coupon: one plate with graded holes + two test pegs.

Run:  uv run calibration/tolerance_coupon/model.py
Then print output/tolerance_coupon.3mf (all three objects, one plate, PLA, 0.20 mm).
See README.md in this folder for how to read the results.
"""

from build123d import *

from printlib import check, export, preview

NOMINAL = 10.0                                  # peg size (round Ø and square side)
CLEARANCES = [0.0, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]  # total, added to NOMINAL
PITCH = 14.0
PLATE_T = 5.0
MARGIN = 4.0
ROW_ROUND_Y = 11.0
ROW_SQUARE_Y = -10.0
LABEL_Y = 0.5
TEXT_SIZE = 4.5
ENGRAVE = 0.6                                   # 3 layers at 0.2 mm
FOOT_CHAMFER = 0.4                              # elephant's-foot relief on bed-side edges
PEG_H = 12.0

n = len(CLEARANCES)
plate_w = n * PITCH + 2 * MARGIN - (PITCH - NOMINAL)
xs = [(i - (n - 1) / 2) * PITCH for i in range(n)]

with BuildPart() as plate:
    with BuildSketch():
        with Locations((0, 0.5)):
            RectangleRounded(plate_w, 2 * (ROW_ROUND_Y + NOMINAL / 2 + MARGIN) - 1, 2.0)
    extrude(amount=PLATE_T)
    for x, c in zip(xs, CLEARANCES):
        with Locations((x, ROW_ROUND_Y, PLATE_T)):
            Hole((NOMINAL + c) / 2)
        with Locations((x, ROW_SQUARE_Y, 0)):
            Box(NOMINAL + c, NOMINAL + c, PLATE_T, align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT)
    # relieve every bed-side edge (plate outline and hole bottoms)
    chamfer(plate.edges().group_by(Axis.Z)[0], FOOT_CHAMFER)
    with BuildSketch(Plane.XY.offset(PLATE_T)):
        for x, c in zip(xs, CLEARANCES):
            with Locations((x, LABEL_Y)):
                Text(f"{round(c * 100)}", font_size=TEXT_SIZE, font_style=FontStyle.BOLD)
    extrude(amount=-ENGRAVE, mode=Mode.SUBTRACT)

def peg(round_: bool) -> Part:
    with BuildPart() as p:
        if round_:
            Cylinder(NOMINAL / 2, PEG_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        else:
            Box(NOMINAL, NOMINAL, PEG_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        chamfer(p.edges().group_by(Axis.Z)[0], FOOT_CHAMFER)
        chamfer(p.edges().group_by(Axis.Z)[-1], 0.8)  # lead-in so the peg finds the hole
    return p.part

plate_y_max = plate.part.bounding_box().max.Y
peg_round = Pos(-8, plate_y_max + 10, 0) * peg(True)
peg_square = Pos(8, plate_y_max + 10, 0) * peg(False)

parts = {"plate": plate.part, "peg_round": peg_round, "peg_square": peg_square}

if __name__ == "__main__":
    for name, shape in parts.items():
        check(shape, name)
    preview(*parts.values(), names=list(parts))
    export(parts, "tolerance_coupon")
