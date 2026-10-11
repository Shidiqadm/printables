"""KAYO-style toyetic desk lamp: a tilting "robot head" between the two arms of a bent-sheet stand.

Reference: makeyo.fr KAYO (17 cm high, 18 cm wide, 19.6 cm long, 8x 10x2 magnets) and the
Makeyo assembly video (youtube.com/shorts/DPzgkipscrE). Rebuilt from photos for personal use:
do not publish or sell these files. Our change: B22 bayonet holder instead of E14.

Run:     uv run projects/kayo-lamp/model.py
Outputs: projects/kayo-lamp/output/  one 3MF/STEP/STL per part, in print orientation,
         plus kayo-lamp-assembly.step for reference.

Frames
  lamp: X = width, Y = forward (the way the lamp looks), Z = up, table at Z = 0.
  head: X = width, Y = head axis (towards the eyes), Z = up of the head, origin at head centre.
        The head sits in the lamp at TILT degrees, turning about the pivot.

How it goes together (as in the video)
  stand (orange)       one bent sheet: two tapered arms joined by the base
  shell_bottom         open tray with a threaded "ear" on each side near the back; a printed
                       screw goes through each arm into a captive printed nut behind the ear
  box + face_plate     black reflector box at the front of the tray, B22 holder through its
                       back wall, black face plate with two eye holes snapped on its front
  shell_top            cover; notches clear the ears. Both shells share the angled front and
                       back cuts and are open at the back, where the cable leaves
  eyes (white)         pushed into the face plate last
  4 magnet pairs       box to tray (2) and box to cover (2)
"""

from math import acos, atan2, cos, pi, radians, sin, sqrt, tan

from bd_warehouse.thread import IsoThread
from build123d import *
from build123d import Shape

from printlib import A1, check, export, fit, magnet, preview

# ---- Parameters (mm) -------------------------------------------------------
# Head (outer size of the orange shells)
HEAD_L = 184.0             # along the top edge
HEAD_W = 150.0
HEAD_H = 65.0
HEAD_R = 15.0              # outer corner radius
SHELL_T = A1.wall(6)       # 2.52, thick enough for 1.3 mm magnet pockets
SLIT = 3.0                 # gap between cover and tray: the "mouth line"
SLIT_FROM_TOP = 38.0       # slit centre below the head top (photo: ~58% down)
FRONT_ANGLE = 21.0         # front end leans back (top overhangs): vertical when the head is at TILT
BACK_ANGLE = 23.0          # back end of both shells leans the other way (side photo)

# Reflector box, face plate, eyes
BOX_GAP = 0.25             # per side, box to shells
BOX_T = A1.wall(4)         # 1.68
BOX_DEPTH = 80.0           # face front to back wall: room for a B22 G45 globe bulb
BACK_T = 3.0
HOLDER_HOLE = 29.0         # B22 holder with threaded skirt + shade ring (barrel ~26, ring ~32)
FACE_INSET = 4.0           # straight face plate, this far behind the tray's front lip (bottom of the angled front)
FACE_T = 2.4
LEDGE_W = 2.0              # face plate rests on this inner ledge
LEDGE_T = 2.4
RIDGE = 0.5                # snap ridges that keep the face plate on
EYE_D = 42.0
EYE_PITCH = 54.0           # centre to centre
EYE_FLANGE_D = 47.0
EYE_FLANGE_T = 0.8
EYE_PLUG_T = 1.2
EYE_X_W = 3.0              # "X" mark on the eyes
EYE_X_H = 0.8

# Magnets: 10 x 2 discs. The shell magnet sticks out of its shallow pocket and drops
# into a wider pocket on the box, which also locates the box.
MAG = magnet("d10x2")
MAG_SHELL_DEPTH = 1.3      # leaves 1.22 mm of shell skin over the magnet
MAG_LOCATE = 0.9
MAG_X = 50.0
MAG_FROM_BACK = 40.0       # along the box, from its back wall

# Pivot: one printed M12 screw per side into a captive printed nut in the tray's ear
PIVOT_FROM_BACK = 59.0     # along the top edge, from the top back corner
TILT = 21.0                # head tilt shown in the photos (adjustable on the lamp)
PIVOT_Z = 89.0             # pivot height above the table
EAR_R = 11.0
EAR_IN = 8.0               # ear boss depth inside the tray wall
SCREW_D = 12.0
SCREW_P = 1.75
THREAD_COMP = 0.15         # radial allowance per printed thread (screw and nut)
PIVOT_HOLE = SCREW_D + 0.8 # arm and ear holes, the screw turns in them
NUT_AF = 18.0
NUT_T = 6.0
KNOB_D = 22.0              # screw head = the white "ear" button
KNOB_T = 9.0

# Stand (one bent sheet)
STAND_T = A1.wall(7)       # 2.94
ARM_GAP = 1.5              # head side to arm (the ear's outer ring fills it)
BEND_R = 10.0              # inner bend radius
FOOT_FRONT = 113.0         # front tip of the foot, ahead of the pivot (~10 mm past the head front)
FOOT_BACK = 10.0           # back edge of the foot, ahead of the pivot (side photo ~7)
TAB_R = 22.0               # rounded arm top around the pivot (side photo)
BED_CHAMFER = 0.4

# Bulb + holder, only for the balance estimate
BULB_G = 75.0              # B22 holder + G45 LED bulb, rough

# ---- Derived ---------------------------------------------------------------
V_SLIT = HEAD_H / 2 - SLIT_FROM_TOP              # slit centre height in the head frame
U_PIVOT = -HEAD_L / 2 + PIVOT_FROM_BACK
BW = HEAD_W - 2 * (SHELL_T + BOX_GAP)           # box outer
BH = HEAD_H - 2 * (SHELL_T + BOX_GAP)
BR = HEAD_R - SHELL_T - BOX_GAP
IW, IH, IR = BW - 2 * BOX_T, BH - 2 * BOX_T, BR - BOX_T   # box inner


def u_front(v: float, inset: float = 0.0) -> float:
    """Front end plane (shifted back by inset along the axis), as u at head height v."""
    return HEAD_L / 2 - inset - (HEAD_H / 2 - v) * tan(radians(FRONT_ANGLE))


def u_back(v: float) -> float:
    """Back end plane of the cover, as u at head height v."""
    return -HEAD_L / 2 + (HEAD_H / 2 - v) * tan(radians(BACK_ANGLE))


U_FACE = u_front(-HEAD_H / 2, FACE_INSET)       # face plate front: square to the axis, behind the lip
U_FRONT = U_FACE + 1.0                          # box front (snap ridges live in this 1 mm)
U_BOX_BACK = U_FACE - BOX_DEPTH
MAG_U = U_BOX_BACK + MAG_FROM_BACK
X_ARM_IN = HEAD_W / 2 + ARM_GAP                 # arm inner face

# Along the pivot axis, s = distance outward from the shell outer face
S_ARM_OUT = ARM_GAP + STAND_T
S_EAR_IN = -(SHELL_T + EAR_IN)                  # inner face of the ear boss
S_SCREW_END = S_EAR_IN + 0.5
SCREW_LEN = S_ARM_OUT - S_SCREW_END


def along_u(face: Sketch, u0: float, u1: float) -> Part:
    """Extrude a head cross-section (sketched in XY as x, v) from u0 to u1 along the head axis."""
    return Rot(90, 0, 0) * Pos(0, 0, -u1) * extrude(face, u1 - u0)


def teardrop(r: float, tip: str = "y") -> Sketch:
    """Circle with a 45 deg tip ("y", "-y" or "x") so sideways holes and bosses print cleanly."""
    c, t = r * cos(radians(45)), r * sqrt(2)
    pts = {"y": [(-c, c), (c, c), (0, t)], "-y": [(-c, -c), (c, -c), (0, -t)], "x": [(c, -c), (c, c), (t, 0)]}[tip]
    return Circle(r) + Polygon(*pts, align=None)


def rrect(w: float, h: float, r: float) -> Sketch:
    return RectangleRounded(w, h, r)


def between(back, front) -> Part:
    """Everything between two planes across the head, each given as u = f(v)."""
    lo, hi = -HEAD_H, HEAD_H
    sk = Polygon((back(hi), hi), (front(hi), hi), (front(lo), lo), (back(lo), lo), align=None)
    return extrude(Plane.YZ.offset(-HEAD_W) * sk, 2 * HEAD_W, dir=(1, 0, 0))


def on_side(face: Sketch, x0: float, length: float, sign: int) -> Part:
    """Extrude a (u, v) sketch along X from x = sign * x0, by length towards sign (outward)."""
    return extrude(Plane.YZ.offset(sign * x0) * face, length, dir=(sign, 0, 0))


# ---- Shells ----------------------------------------------------------------
ring = rrect(HEAD_W, HEAD_H, HEAD_R) - rrect(HEAD_W - 2 * SHELL_T, HEAD_H - 2 * SHELL_T, HEAD_R - SHELL_T)
upper_cut = Pos(0, V_SLIT + SLIT / 2 - 100) * Rectangle(HEAD_W + 10, 200)
lower_cut = Pos(0, V_SLIT - SLIT / 2 + 100) * Rectangle(HEAD_W + 10, 200)

head_keep = between(u_back, u_front)                       # angled front and back ends
shell_top = along_u(ring - upper_cut, -HEAD_L, HEAD_L) & head_keep
shell_top -= Pos(0, U_PIVOT, V_SLIT) * Cylinder(EAR_R + 0.6, HEAD_W + 10, rotation=(0, 90, 0))   # ear notches

shell_bottom = along_u(ring - lower_cut, -HEAD_L, HEAD_L) & head_keep   # same angled ends as the cover
ear_at = Pos(U_PIVOT, V_SLIT)
x_wall_in = HEAD_W / 2 - SHELL_T
for sign in (1, -1):
    shell_bottom += on_side(ear_at * teardrop(EAR_R, "-y"), x_wall_in - EAR_IN, EAR_IN + SHELL_T, sign)  # ear + boss
    shell_bottom += on_side(ear_at * Circle(EAR_R), HEAD_W / 2, ARM_GAP, sign)                         # bearing ring
    shell_bottom -= on_side(ear_at * teardrop(PIVOT_HOLE / 2, "y"), x_wall_in - EAR_IN - 1, EAR_IN + SHELL_T + ARM_GAP + 2, sign)
    nut = ear_at * RegularPolygon((NUT_AF + 0.4) / sqrt(3), 6, rotation=90)                         # vertex up
    shell_bottom -= on_side(nut, x_wall_in - EAR_IN - 1, NUT_T + 0.3 + 1, sign)

for x in (-MAG_X, MAG_X):
    z_in = HEAD_H / 2 - SHELL_T
    shell_top -= Pos(x, MAG_U, z_in) * Cylinder(MAG.hole_d / 2, MAG_SHELL_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    shell_bottom -= Pos(x, MAG_U, -z_in) * Cylinder(MAG.hole_d / 2, MAG_SHELL_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MAX))

# ---- Reflector box ---------------------------------------------------------
box = along_u(rrect(BW, BH, BR) - rrect(IW, IH, IR), U_BOX_BACK, U_FRONT)
box += along_u(rrect(IW + 0.2, IH + 0.2, IR + 0.1), U_BOX_BACK, U_BOX_BACK + BACK_T)
box -= Pos(0, U_BOX_BACK, 0) * Cylinder(HOLDER_HOLE / 2, 3 * BACK_T, rotation=(90, 0, 0))
for x in (-55, -48, -41, -34, 34, 41, 48, 55):
    box -= Pos(x, U_BOX_BACK, 0) * Box(3.0, 3 * BACK_T, 30.0)

# Face plate ledge, 45 deg underneath so it prints without support (box prints back-down)
u_ledge = U_FACE - FACE_T
ledge = along_u(rrect(IW + 0.2, IH + 0.2, IR + 0.1) - rrect(IW - 2 * LEDGE_W, IH - 2 * LEDGE_W, IR - LEDGE_W),
                u_ledge - LEDGE_T, u_ledge)
inner_loop = ledge.faces().sort_by(Axis.Y)[0].inner_wires()[0]
box += chamfer(inner_loop.edges(), LEDGE_W - 0.05)

# Snap ridges just in front of the face plate (ramp in, flat face holds the plate)
for x in (-40, 40):
    for side in (1, -1):
        zi = side * IH / 2
        tri = Polygon((U_FACE, zi), (U_FACE, zi - side * RIDGE), (U_FRONT, zi), align=None)
        box += extrude(Plane.YZ.offset(x - 6) * tri, 12, dir=(1, 0, 0))

# Magnet pads on top and bottom walls (teardrop pockets: they are sideways when printing)
mag_depth = MAG_LOCATE + MAG.depth
mag_pad_t = mag_depth + A1.wall(2) - BOX_T
for x in (-MAG_X, MAG_X):
    for side in (1, -1):
        z_out = side * BH / 2
        z_in = side * IH / 2
        lo, hi = MAG_U - 9, MAG_U + 10
        prof = Polygon((lo - mag_pad_t, z_in + side * 0.5), (lo, z_in - side * mag_pad_t),
                       (hi, z_in - side * mag_pad_t), (hi, z_in + side * 0.5), align=None)
        box += extrude(Plane.YZ.offset(x - 8) * prof, 16, dir=(1, 0, 0))
        locate = extrude(Plane.XY.offset(z_out) * Pos(x, MAG_U) * teardrop(MAG.hole_d / 2 + 0.4), MAG_LOCATE, dir=(0, 0, -side))
        seat = extrude(Plane.XY.offset(z_out - side * MAG_LOCATE) * Pos(x, MAG_U) * teardrop(MAG.hole_d / 2), MAG.depth, dir=(0, 0, -side))
        box -= locate + seat

# ---- Face plate and eyes (modelled in print orientation) -------------------
# FACE_AT places the print frame (front face on z = 0, +z into the head) in the head
FACE_AT = Pos(0, U_FACE, 0) * Rot(90, 0, 0)
face_plate = extrude(rrect(IW - 0.2, IH - 0.2, IR - 0.1), FACE_T)
for x in (-EYE_PITCH / 2, EYE_PITCH / 2):
    face_plate -= Pos(x, 0, 0) * Cylinder((EYE_D + fit("slip")) / 2, 3 * FACE_T)
face_plate = chamfer(face_plate.edges().group_by(Axis.Z)[0], BED_CHAMFER)

eye = Cylinder(EYE_FLANGE_D / 2, EYE_FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
eye += Pos(0, 0, EYE_FLANGE_T) * Cylinder(EYE_D / 2, EYE_PLUG_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
bar = Pos(0, 0, EYE_FLANGE_T + EYE_PLUG_T) * Box(EYE_D * 0.62, EYE_X_W, EYE_X_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
eye += Rot(0, 0, 45) * bar + Rot(0, 0, -45) * bar
eye = chamfer(eye.edges().group_by(Axis.Z)[0], BED_CHAMFER)

# ---- Pivot screw and nut (print orientation, axis = Z) ---------------------
screw = Cylinder(KNOB_D / 2, KNOB_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
screw = chamfer(screw.edges().group_by(Axis.Z)[0], 1.2)          # outer face down on the bed
screw = fillet(screw.edges().group_by(Axis.Z)[-1], 1.0)
thread = IsoThread(SCREW_D, SCREW_P, SCREW_LEN, external=True, end_finishes=("square", "chamfer"),
                   manufacturing_compensation=THREAD_COMP)
screw += Pos(0, 0, KNOB_T) * (Cylinder(thread.min_radius, SCREW_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN)) + thread)

nut = extrude(RegularPolygon(NUT_AF / sqrt(3), 6), NUT_T)
nut = chamfer(nut.edges().group_by(Axis.Z)[0], BED_CHAMFER)
nut -= Cylinder(SCREW_D / 2 + THREAD_COMP, 3 * NUT_T)
nut += IsoThread(SCREW_D, SCREW_P, NUT_T, external=False, end_finishes=("chamfer", "chamfer"),
                 manufacturing_compensation=THREAD_COMP)

# ---- Stand -----------------------------------------------------------------
# Front view: two arms and the base as one bent sheet ...
xc = X_ARM_IN + STAND_T / 2
z_arm_top = PIVOT_Z + TAB_R + 5
with BuildSketch(Plane.XZ) as front_view:
    with BuildLine():
        FilletPolyline((-xc, z_arm_top), (-xc, STAND_T / 2), (xc, STAND_T / 2), (xc, z_arm_top),
                       radius=BEND_R + STAND_T / 2)
    trace(line_width=STAND_T)
sheet = Pos(0, -50, 0) * extrude(front_view.sketch, FOOT_FRONT + 60, dir=(0, 1, 0))


def tangent(py: float, pz: float, sign: int) -> tuple[float, float]:
    """Point where a line from (py, pz) touches the pivot tab circle."""
    d = sqrt(py ** 2 + (pz - PIVOT_Z) ** 2)
    a = atan2(pz - PIVOT_Z, py) + sign * acos(TAB_R / d)
    return TAB_R * cos(a), PIVOT_Z + TAB_R * sin(a)


# ... cut by the side view: foot on the table, edges running up to the round tab at the pivot
t_front = tangent(FOOT_FRONT, 0, +1)
t_back = tangent(FOOT_BACK, 0, -1)
a_m = (atan2(t_front[1] - PIVOT_Z, t_front[0]) + atan2(t_back[1] - PIVOT_Z, t_back[0]) + 2 * pi) / 2
with BuildSketch(Plane.YZ.offset(-120)) as side_view:
    with BuildLine():
        Line((FOOT_BACK, 0), (FOOT_FRONT, 0))
        Line((FOOT_FRONT, 0), t_front)
        ThreePointArc(t_front, (TAB_R * cos(a_m), PIVOT_Z + TAB_R * sin(a_m)), t_back)
        Line(t_back, (FOOT_BACK, 0))
    make_face()
stand = sheet & extrude(side_view.sketch, 240, dir=(1, 0, 0))
stand -= extrude(Plane.YZ.offset(-120) * Pos(0, PIVOT_Z) * teardrop(PIVOT_HOLE / 2), 240, dir=(1, 0, 0))
try:
    stand = chamfer(stand.edges().group_by(Axis.Z)[0].filter_by(Axis.X), BED_CHAMFER)
except Exception as e:  # cosmetic only
    print(f"[stand] bed chamfer skipped: {e}")


# ---- Assembly --------------------------------------------------------------
def head_to_lamp(shape: Shape) -> Shape:
    """Place a head-frame shape on the stand at TILT."""
    return Pos(0, 0, PIVOT_Z) * Rot(TILT, 0, 0) * Pos(0, -U_PIVOT, -V_SLIT) * shape


def on_axis(shape: Shape, s: float, sign: int) -> Shape:
    """Put a part printed along +Z on the pivot axis of side `sign`, its z=0 face at s, +Z pointing inward."""
    turn = Rot(0, -90, 0) if sign > 0 else Rot(0, 90, 0)
    return Pos(sign * (HEAD_W / 2 + s), U_PIVOT, V_SLIT) * turn * shape


face_in_head = FACE_AT * face_plate
eyes_in_head = [FACE_AT * Pos(x, 0, FACE_T + EYE_FLANGE_T) * Rot(180, 0, 0) * eye for x in (-EYE_PITCH / 2, EYE_PITCH / 2)]
head_parts = {
    "shell_top": shell_top,
    "shell_bottom": shell_bottom,
    "box": box,
    "face_plate": face_in_head,
    "eye_l": eyes_in_head[0],
    "eye_r": eyes_in_head[1],
    "screw_l": on_axis(screw, S_ARM_OUT + KNOB_T, -1),
    "screw_r": on_axis(screw, S_ARM_OUT + KNOB_T, 1),
    "nut_l": on_axis(nut, S_EAR_IN + NUT_T, -1),
    "nut_r": on_axis(nut, S_EAR_IN + NUT_T, 1),
}
assembly = {"stand": stand, **{k: head_to_lamp(v) for k, v in head_parts.items()}}

ORANGE, BLACK, WHITE = "#ff5a1f", "#1d1d1f", "#f4f1ea"
COLORS = {"stand": ORANGE, "shell_top": ORANGE, "shell_bottom": ORANGE, "box": BLACK, "face_plate": BLACK,
          "eye_l": WHITE, "eye_r": WHITE, "screw_l": WHITE, "screw_r": WHITE, "nut_l": BLACK, "nut_r": BLACK}


def on_bed(shape: Shape) -> Shape:
    bb = shape.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * shape


# Print orientation for each part
prints = {
    "stand": stand,                                         # foot down, as it stands
    "shell_top": on_bed(Rot(0, 180, 0) * shell_top),        # top face on the bed
    "shell_bottom": on_bed(shell_bottom),                   # bottom face on the bed
    "box": on_bed(Rot(90, 0, 0) * box),                     # back wall on the bed
    "face_plate": face_plate,                               # front face on the bed
    "eye": eye,                                             # print 2
    "screw": screw,                                         # print 2, button face down
    "nut": nut,                                             # print 2
}


def balance_report() -> None:
    """Centre of mass vs the foot, at a few tilts (thin sheet parts print nearly solid)."""
    for tilt in (-20, 0, TILT, 45, 70):
        def y_of(u: float, v: float) -> float:
            return (u - U_PIVOT) * cos(radians(tilt)) - (v - V_SLIT) * sin(radians(tilt))
        parts = [(p.volume / 1000 * 1.24 * 0.95, y_of(p.center().Y, p.center().Z)) for p in head_parts.values()]
        parts.append((BULB_G, y_of(U_BOX_BACK + 5, 0)))
        parts.append((stand.volume / 1000 * 1.24 * 0.95, stand.center().Y))
        y_cg = sum(m * y for m, y in parts) / sum(m for m, _ in parts)
        print(f"[balance] tilt {tilt:>4} deg: CG at y = {y_cg:5.1f} mm  (foot spans {FOOT_BACK:.0f} .. {FOOT_FRONT:.0f})")


# ---- Output ----------------------------------------------------------------
if __name__ == "__main__":
    for name, p in prints.items():
        check(p, f"kayo-{name}")
    bb = Compound(list(assembly.values())).bounding_box()
    print(f"[assembly] {bb.size.X:.1f} wide x {bb.size.Y:.1f} long x {bb.size.Z:.1f} high (KAYO: 180 x 196 x 170)")
    balance_report()
    preview(*assembly.values(), names=list(assembly), colors=[COLORS[k] for k in assembly])
    for name, p in prints.items():
        export(p, f"kayo-{name}")
    export(assembly, "kayo-lamp-assembly", formats=("step",))
