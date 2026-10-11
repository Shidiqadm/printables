"""Blurry wall clock: hands sit deep inside a white bowl behind a frosted window.

Own parametric take on the "Blurry - The Fading Time" clock idea (LayerLoft.Studio),
rebuilt from its photos and assembly video, not from its files.

Stack, wall to front:
  housing      colored back shell, hangs on one screw (keyhole), battery opening
  bowl         white; movement bolts to its back, its centre pocket holds the hour disk
  hour_disk    white cup on the hour tube; the hour hand pegs into it
  minute_dome  white dome on the minute shaft; the minute hand slides into its slot
  hour_hand    orange bar with a peg
  minute_hand  orange bar
  window       translucent disc ("blurry glass")
  ring         colored front ring, bayonet twist-lock onto the housing (turn clockwise)

Only the orange hands contrast with the white bowl, and they sit 9-11 mm behind the
window, so the translucent PLA blurs them into soft bars.

Run:     uv run projects/blurry-wall-clock/model.py
Outputs: projects/blurry-wall-clock/output/<part>.{3mf,step,stl}, each in print orientation
"""

import math

from build123d import *

from printlib import check, export, fit, preview

# ---- Movement (generic 56 x 56 x 16 mm quartz, M8 thread, 16 mm shaft) ------------
# Heights are measured from the movement's front face. GUESSED: check against yours
# with a ruler and adjust before printing the hour disk / minute dome.
MOVE_W = 56.0              # body width/height (common size)
MOVE_D = 16.0              # body depth
THREAD_D = 8.0             # M8 threaded tube
THREAD_LEN = 8.0           # threaded part of the shaft
HOUR_TUBE_TIP = 12.0       # tip of the hour tube (where the hour hand would sit)
MINUTE_TIP = 15.0          # tip of the minute shaft
HOUR_BORE = 5.0            # hour hand hole (common: 5.0, some 5.2-5.6)
MINUTE_BORE = 3.1          # minute hand hole, round press-fit type (some 3.6-3.9)
NUT_STACK = 3.0            # washer + hex nut on the front of the bowl

# ---- Overall -----------------------------------------------------------------------
R_OUT = 106.0              # outer radius (212 mm diameter, like the original)
FRONT_Z = 48.0             # overall depth
WINDOW_T = 1.6             # window thickness (8 layers @ 0.2); thicker = blurrier
LIP_T = 2.0                # ring lip in front of the window
LIP_R_IN = 99.0            # visible window radius
RING_WALL = 2.1            # 5 perimeters
NECK_WALL = 3.0            # housing neck under the ring

# ---- Housing -----------------------------------------------------------------------
FLOOR_T = 2.4              # back plate, 12 layers (carries the keyhole)
BACK_R = 85.0              # back face radius; flares out at 45 deg to R_OUT
WALL = 2.5                 # housing wall (normal thickness)
FLARE_FILLET = 10.0        # soft shoulder where the flare turns vertical
SEAM_Z = 28.0              # top of the housing's full-diameter part (ring covers above)
NECK_TOP = 34.0            # top of the neck / bowl seat
SEAT = 2.0                 # 45 deg conical seat that centres the bowl
OPENING = 62.0             # square opening in the back: battery access without disassembly
KEY_Y = 64.0               # keyhole centre above the clock centre
KEY_HEAD_D = 9.0           # screw head passes here
KEY_SLOT_W = 4.5           # screw shank slides up here
KEY_SLOT_L = 12.0
KEY_HEAD_H = 3.0           # room behind the slot for the screw head

# ---- Bayonet (3 lugs on the ring, L-grooves in the neck) ---------------------------
LUG_ANGLES = (0.0, 120.0, 240.0)
LUG_W_DEG = 12.0
LUG_DEPTH = 1.0            # radial
LUG_H = 2.0
GROOVE_DEPTH = 1.2
TRAVEL_DEG = 25.0          # twist from entry slot to locked
RAMP = 0.6                 # groove ceiling drops this much over the twist: pulls the ring tight
PRELOAD = 0.1              # lug sits this far "into" the ceiling when locked (ring flexes)

# ---- Bowl (white, solid "lens": flat back on the bed, sculpted front) --------------
BOWL_BACK_Z = FLOOR_T + MOVE_D + 0.6          # movement face presses here
BOWL_CENTER_T = 3.0                           # clamped between nut and movement
POCKET_R = 53.0                               # centre pocket for the hour disk
BOWL_BACK_R = 89.0                            # flat back radius, then 45 deg cone
BOWL_SIDE_R = 100.6                           # outer cylinder inside the neck
RIM_R_OUT = 103.6
RIM_R_IN = 100.0
FLOOR_FLAT_R = 72.0                           # flat floor ring, then curves up to the rim
KEY_W = 8.0                                   # anti-rotation key at 12 o'clock

# ---- Hands ---------------------------------------------------------------------------
DISK_R = POCKET_R - 1.0
DISK_PLATE = 1.2
DISK_SKIRT = 1.26
DISK_HUB_D = 11.0
PEG_R = 40.0               # hour hand peg position on the disk
PEG = (4.0, 2.4)           # radial x tangential
PEG_SLEEVE = 3.0
HAND_T = 2.0
HOUR_HAND = (37.0, 70.0, 5.5)     # from r, to r, width
MINUTE_HAND = (22.0, 85.0, 4.0)
DOME_R = 32.0
DOME_H = 7.0
DOME_SIDE = 5.0
SLOT_DEPTH = 10.0
GAP = 0.4                  # running clearance between moving layers

# ---- Derived heights (Z from the wall) ---------------------------------------------
FACE_Z = BOWL_BACK_Z                          # movement front face
POCKET_Z = BOWL_BACK_Z + BOWL_CENTER_T        # pocket floor (nut sits here)
PLATE_TOP = FACE_Z + HOUR_TUBE_TIP            # hour disk top, flush with the hour tube tip
FLOOR_Z = PLATE_TOP - 0.5                     # bowl floor ring, just below the disk
HOUR_BAR_Z = PLATE_TOP + GAP
DOME_Z = PLATE_TOP + 0.5
MINUTE_BAR_Z = HOUR_BAR_Z + HAND_T + GAP
RIM_Z = FRONT_Z - LIP_T - WINDOW_T            # window rests on the bowl rim
RING_R_IN = R_OUT - RING_WALL
NECK_R = RING_R_IN - fit("slip", "linear") / 2 - 0.05
NECK_R_IN = NECK_R - NECK_WALL
WINDOW_R = RING_R_IN - 0.3


def rz_face(pts: list[tuple[float, float]]) -> Face:
    """Closed (radius, z) polygon in the XZ plane, ready to revolve about Z."""
    return Plane.XZ * Polygon(*pts, align=None)


def revolve_rz(pts, arc=360.0, start=0.0) -> Part:
    solid = revolve(rz_face(pts), Axis.Z, arc)
    return Rot(0, 0, start) * solid if start else solid


def circle_edges(part: Part, r: float, z: float, tol: float = 0.05) -> ShapeList:
    return ShapeList(
        e for e in part.edges().filter_by(GeomType.CIRCLE)
        if abs(e.radius - r) < tol and abs(e.arc_center.Z - z) < tol
    )


# ---- Housing ---------------------------------------------------------------------------
def housing() -> Part:
    flare_top = R_OUT - BACK_R                      # z where the 45 deg flare meets R_OUT
    off = WALL * math.sqrt(2)                       # horizontal offset of the inner cone
    r_in = R_OUT - WALL                             # inner radius of the vertical wall
    ledge = r_in - NECK_R_IN                        # inner 45 deg step up to the neck
    z_inner_cone = r_in - (BACK_R - off)            # inner cone meets the inner wall
    prof = [
        (0, 0), (BACK_R, 0), (R_OUT, flare_top), (R_OUT, SEAM_Z),
        (NECK_R, SEAM_Z), (NECK_R, NECK_TOP), (NECK_R_IN + SEAT, NECK_TOP),
        (NECK_R_IN, NECK_TOP - SEAT), (NECK_R_IN, SEAM_Z),
        (r_in, SEAM_Z - ledge), (r_in, z_inner_cone),
        (BACK_R - off + FLOOR_T, FLOOR_T), (0, FLOOR_T),
    ]
    body = revolve_rz(prof)
    body = fillet(circle_edges(body, R_OUT, flare_top), FLARE_FILLET)

    # Bayonet grooves: undercut ledge with a ramped ceiling, entry slot at the far end.
    for phi in LUG_ANGLES:
        body -= groove_cut(phi)

    # Anti-rotation notch for the bowl key at 12 o'clock (+Y).
    notch_w = KEY_W + fit("slip", "linear")
    body -= Pos(0, (NECK_R_IN + R_OUT) / 2, NECK_TOP + 0.1) * Box(
        notch_w, R_OUT - NECK_R_IN + 1, 4.1, align=(Align.CENTER, Align.CENTER, Align.MAX)
    )

    # Back: battery opening and keyhole boss.
    opening = Box(OPENING, OPENING, 3 * FLOOR_T)
    body -= fillet(opening.edges().filter_by(Axis.Z), 4)
    boss = Pos(0, KEY_Y, FLOOR_T) * Box(20, 30, KEY_HEAD_H + 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body += boss
    head_y = KEY_Y - KEY_SLOT_L / 2
    body -= Pos(0, head_y, 0) * Cylinder(KEY_HEAD_D / 2, 2 * FLOOR_T + 0.01)
    body -= Pos(0, KEY_Y, 0) * Box(KEY_SLOT_W, KEY_SLOT_L, 2 * FLOOR_T + 0.01)
    body -= Pos(0, KEY_Y - 1, FLOOR_T) * Box(
        KEY_HEAD_D + 1, KEY_SLOT_L + KEY_HEAD_D, KEY_HEAD_H, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # 0.4 mm elephant's-foot chamfer on every bed edge except the already-sloped rim.
    bed = body.edges().filter_by_position(Axis.Z, -0.01, 0.01)
    bed = ShapeList(e for e in bed if not (e.geom_type == GeomType.CIRCLE and abs(e.radius - BACK_R) < 0.1))
    body = chamfer(bed, 0.4)
    return body


def groove_cut(phi: float) -> Part:
    """Material removed from the neck for one lug: ramped undercut + vertical entry slot."""
    r0 = NECK_R - GROOVE_DEPTH
    r_tip = NECK_R - LUG_DEPTH - fit("slip", "linear") / 2    # lug inner face
    lug_top_in = SEAM_Z + 0.9 + LUG_H - LUG_DEPTH   # lug top at its inner edge (45 deg face)
    c_lock = lug_top_in - PRELOAD
    c_open = c_lock + RAMP
    half = LUG_W_DEG / 2 + 1.0
    pieces = []
    step = 1.0
    a = phi - half
    while a < phi + TRAVEL_DEG + half - 1e-6:
        t = min(max((a + step / 2 - phi) / TRAVEL_DEG, 0.0), 1.0)
        c = c_lock + (c_open - c_lock) * t
        # ceiling parallel to the lug's 45 deg top face, through (r_tip, c)
        prof = [(r0, SEAM_Z), (R_OUT, SEAM_Z), (R_OUT, c + (R_OUT - r_tip)), (r0, c - (r_tip - r0))]
        pieces.append(revolve_rz(prof, step + 0.02, a))
        a += step
    slot = revolve_rz(
        [(r0, SEAM_Z), (R_OUT, SEAM_Z), (R_OUT, NECK_TOP + 1), (r0, NECK_TOP + 1)],
        2 * half, phi + TRAVEL_DEG - half,
    )
    return _fuse(pieces + [slot])


def _fuse(parts: list[Part]) -> Part:
    out = parts[0]
    for p in parts[1:]:
        out += p
    return out


# ---- Ring ----------------------------------------------------------------------------
def ring() -> Part:
    bottom = SEAM_Z + 0.3
    prof = [
        (RING_R_IN, bottom), (R_OUT, bottom), (R_OUT, FRONT_Z - 1.0), (R_OUT - 1.0, FRONT_Z),
        (LIP_R_IN + 0.4, FRONT_Z), (LIP_R_IN, FRONT_Z - 0.4), (LIP_R_IN, FRONT_Z - LIP_T),
        (RING_R_IN, FRONT_Z - LIP_T),
    ]
    body = revolve_rz(prof)
    r_tip = NECK_R - LUG_DEPTH - fit("slip", "linear") / 2      # lug inner face
    z0 = SEAM_Z + 0.9
    lug = [(RING_R_IN + 0.5, z0), (r_tip, z0), (r_tip, z0 + LUG_H - LUG_DEPTH),
           (RING_R_IN + 0.5, z0 + LUG_H - LUG_DEPTH + (RING_R_IN + 0.5 - r_tip))]
    for phi in LUG_ANGLES:
        body += revolve_rz(lug, LUG_W_DEG, phi - LUG_W_DEG / 2)
    return body


# ---- Bowl ----------------------------------------------------------------------------
def bowl() -> Part:
    zb = BOWL_BACK_Z
    z_side = zb + (BOWL_SIDE_R - BOWL_BACK_R)
    seat_z = NECK_TOP - SEAT                       # where the seat cone starts on the housing
    flare0 = (BOWL_SIDE_R, seat_z - (NECK_R_IN - BOWL_SIDE_R))
    flare1 = (RIM_R_OUT, flare0[1] + (RIM_R_OUT - BOWL_SIDE_R))
    outer = [(0, zb), (BOWL_BACK_R, zb), (BOWL_SIDE_R, z_side), flare0, flare1,
             (RIM_R_OUT, RIM_Z), (0, RIM_Z)]
    body = revolve_rz(outer)

    # Front cavity: centre pocket, flat floor ring, quarter-ellipse up to the rim.
    a = RIM_R_IN - FLOOR_FLAT_R
    b = RIM_Z - FLOOR_Z
    with BuildSketch(Plane.XZ) as cav:
        with BuildLine():
            Polyline((0, POCKET_Z), (POCKET_R, POCKET_Z), (POCKET_R, FLOOR_Z), (FLOOR_FLAT_R, FLOOR_Z))
            EllipticalCenterArc((FLOOR_FLAT_R, FLOOR_Z + b), a, b, 270, arc_size=90)
            Polyline((RIM_R_IN, RIM_Z), (RIM_R_IN, RIM_Z + 1), (0, RIM_Z + 1), (0, POCKET_Z))
        make_face()
    body -= revolve(cav.sketch, Axis.Z)

    body -= Pos(0, 0, zb) * Cylinder((THREAD_D + fit("loose")) / 2, 2 * BOWL_CENTER_T + 1)

    # Key at 12 o'clock, 45 deg underside so it prints without support.
    key_face = Plane.YZ * Polygon(
        (BOWL_BACK_R + 8, zb + 8), (NECK_R - 0.15, zb + 8 + NECK_R - 0.15 - BOWL_BACK_R - 8),
        (NECK_R - 0.15, flare1[1]), (BOWL_BACK_R + 8, flare1[1]), align=None,
    )
    body += extrude(key_face, KEY_W / 2, both=True)
    return body


# ---- Hour disk, minute dome, hands ---------------------------------------------------
def hour_disk() -> Part:
    z_bot = POCKET_Z + 1.0
    prof = [(0, z_bot), (DISK_R, z_bot), (DISK_R, PLATE_TOP), (0, PLATE_TOP)]
    body = revolve_rz(prof)
    body -= revolve_rz([(0, z_bot - 0.1), (DISK_R - DISK_SKIRT, z_bot - 0.1),
                        (DISK_R - DISK_SKIRT, PLATE_TOP - DISK_PLATE), (0, PLATE_TOP - DISK_PLATE)])
    hub_bot = max(POCKET_Z + NUT_STACK + 0.5, FACE_Z + THREAD_LEN + 0.5)   # clear nut and thread
    body += Pos(0, 0, hub_bot) * Cylinder(DISK_HUB_D / 2, PLATE_TOP - hub_bot, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body -= Cylinder(HOUR_BORE / 2 + 0.05, 200)
    sleeve_bot = PLATE_TOP - DISK_PLATE - PEG_SLEEVE
    body += Pos(0, PEG_R, sleeve_bot) * Box(PEG[1] + 3, PEG[0] + 3, PLATE_TOP - sleeve_bot,
                                             align=(Align.CENTER, Align.CENTER, Align.MIN))
    hole = (PEG[0] + fit("snug", "linear"), PEG[1] + fit("snug", "linear"))
    body -= Pos(0, PEG_R, 0) * Box(hole[1], hole[0], 200)
    body = chamfer(circle_edges(body, DISK_R, PLATE_TOP), 0.4)          # bed edge when printed face down
    return body


def minute_dome() -> Part:
    z0 = DOME_Z
    with BuildSketch(Plane.XZ) as s:
        with BuildLine():
            Polyline((0, z0), (DOME_R, z0), (DOME_R, z0 + DOME_SIDE))
            EllipticalCenterArc((0, z0 + DOME_SIDE), DOME_R, DOME_H - DOME_SIDE, 0, arc_size=90)
            Line((0, z0 + DOME_H), (0, z0))
        make_face()
    body = revolve(s.sketch, Axis.Z)
    body -= Pos(0, 0, z0) * Cylinder(MINUTE_BORE / 2 + 0.05, DOME_H - 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    slot_h = HAND_T + fit("snug", "linear")
    slot_w = MINUTE_HAND[2] + fit("snug", "linear")
    body -= Pos(0, DOME_R - SLOT_DEPTH / 2 + 0.5, MINUTE_BAR_Z - fit("snug", "linear") / 2) * Box(
        slot_w, SLOT_DEPTH + 1, slot_h, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    body = chamfer(circle_edges(body, DOME_R, z0), 0.4)
    return body


def _bar(r0: float, r1: float, w: float, z: float) -> Part:
    with BuildSketch(Plane.XY.offset(z)) as s:
        SlotCenterToCenter(r1 - r0 - w, w, rotation=90)
    return Pos(0, (r0 + r1) / 2, 0) * extrude(s.sketch, HAND_T)


def hour_hand() -> Part:
    r0, r1, w = HOUR_HAND
    bar = _bar(r0, r1, w, HOUR_BAR_Z)
    peg_bot = PLATE_TOP - DISK_PLATE - PEG_SLEEVE + 0.3
    peg = Pos(0, PEG_R, peg_bot) * Box(PEG[1], PEG[0], HOUR_BAR_Z - peg_bot + 0.01,
                                       align=(Align.CENTER, Align.CENTER, Align.MIN))
    peg = chamfer(peg.edges().group_by(Axis.Z)[0], 0.3)                 # lead-in
    return bar + peg


def minute_hand() -> Part:
    r0, r1, w = MINUTE_HAND
    return _bar(r0, r1, w, MINUTE_BAR_Z)


def window() -> Part:
    return Pos(0, 0, RIM_Z) * Cylinder(WINDOW_R, WINDOW_T, align=(Align.CENTER, Align.CENTER, Align.MIN))


# ---- Test piece ------------------------------------------------------------------------
def hand_fit_test() -> Part:
    """Push onto the movement's shafts to pick HOUR_BORE / MINUTE_BORE (row of 5 each)."""
    plate = Box(66, 26, 3, align=(Align.CENTER, Align.CENTER, Align.MIN))
    plate = fillet(plate.edges().filter_by(Axis.Z), 3)
    for i, d in enumerate((-0.2, -0.1, 0.0, 0.1, 0.2)):
        x = -24 + 12 * i
        plate -= Pos(x, 6, 0) * Cylinder((HOUR_BORE + d) / 2 + 0.05, 10)
        plate -= Pos(x, -6, 0) * Cylinder((MINUTE_BORE + d) / 2 + 0.05, 10)
        for k in range(i + 1):                                  # 1-5 notches on the edge = column
            plate -= Pos(x - 4 + 2 * k, 13, 3) * Box(0.8, 3, 1.2)
    return chamfer(plate.edges().group_by(Axis.Z)[0], 0.4)


# ---- Print poses ------------------------------------------------------------------------
def on_bed(p: Part) -> Part:
    return Pos(0, 0, -p.bounding_box().min.Z) * p


def flipped(p: Part) -> Part:
    return on_bed(Rot(180, 0, 0) * p)


def parts() -> dict[str, Part]:
    """Assembly coordinates: Z from the wall, 12 o'clock = +Y."""
    return {
        "housing": housing(), "bowl": bowl(), "hour_disk": hour_disk(),
        "minute_dome": minute_dome(), "hour_hand": hour_hand(), "minute_hand": minute_hand(),
        "window": window(), "ring": ring(),
    }


PRINT_POSE = {
    "housing": on_bed, "bowl": on_bed, "hour_disk": flipped, "minute_dome": on_bed,
    "hour_hand": flipped, "minute_hand": on_bed, "window": on_bed, "ring": flipped,
}

COLORS = {
    "housing": "#5cc3be", "ring": "#5cc3be", "bowl": "#f4f2ee", "hour_disk": "#f4f2ee",
    "minute_dome": "#f4f2ee", "hour_hand": "#ff6a2b", "minute_hand": "#ff6a2b", "window": "#e8e8e8",
}


def show(ps: dict[str, Part], time=(10, 10), explode: float = 0.0) -> None:
    hh, mm = time
    a_min = -6.0 * mm
    a_hour = -(30.0 * (hh % 12) + 0.5 * mm)
    rot = {"hour_disk": a_hour, "hour_hand": a_hour, "minute_dome": a_min, "minute_hand": a_min}
    order = list(ps)
    objs = []
    for i, (name, p) in enumerate(ps.items()):
        q = Rot(0, 0, rot.get(name, 0.0)) * p
        q = Pos(0, 0, explode * order.index(name)) * q
        q.color = Color(COLORS[name], 0.45 if name == "window" else 1.0)
        objs.append(q)
    preview(*objs, names=list(ps))


if __name__ == "__main__":
    import sys

    ps = parts()
    total = 0.0
    for name, p in ps.items():
        pose = PRINT_POSE[name](p)
        r = check(pose, name)
        total += r["max_mass_g"]
        export(pose, name)
    test = hand_fit_test()
    check(test, "hand_fit_test")
    export(test, "hand_fit_test")
    print(f"[info] solid upper bound, all parts: {total:.0f} g")
    print(f"[info] window gap: hour bar {RIM_Z - HOUR_BAR_Z - HAND_T:.1f} mm, "
          f"minute bar {RIM_Z - MINUTE_BAR_Z - HAND_T:.1f} mm")
    show(ps, explode=float(sys.argv[1]) if len(sys.argv) > 1 else 0.0)
