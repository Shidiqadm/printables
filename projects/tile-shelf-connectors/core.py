"""Functional core of the tile shelf hub: parameters, tile channels, crush ribs, plug.

Everything that decides whether tiles fit lives here and is covered by test_fit.py.
The outside shape (style) comes from deco.py; nothing here depends on it.

Shelf frame: X along the row, Y = depth (0 = front face of the tiles, +Y to the back),
Z up. A hub is modelled at the front-top corner between two cubes: X=0 is the middle of
its centre column, Z=0 is the top edge of the side tiles.
"""

from build123d import *

from printlib import A1, fit

# ---- Tiles and grip --------------------------------------------------------
T_SHELF = 8.0             # top / bottom tile thickness (measure with thickness_gauge)
T_SIDE = 8.0              # side tile thickness
THICK_TOL = 0.30          # tiles may be this much thinner/thicker than nominal
CLEAR = THICK_TOL + fit("snug", "linear")   # slot = T + 0.4: a +0.3 tile still slides in
CRUSH = 0.30              # crush-rib interference at nominal (0 at -TOL, 0.6 at +TOL)
RIB_R = 2.0               # crush-rib radius (wide, gentle ramp for tiles sliding across)
RIB_END = 3.0             # hub crush ribs stop this far before the back mouth...
RIB_RAMP = 2.0            # ...after ramping down over this length
LEAD = 1.0                # lead-in chamfer at slot mouths

# ---- Hub -------------------------------------------------------------------
HUB = 48.0                # cube size (without crown)
COLUMN = 8.0              # centre column between the two cubes' side tiles
CAP = A1.wall(12)         # 5.04: cap over the top tiles
FRONT = 5.0               # solid front face that ties the blocks together

# ---- Derived ---------------------------------------------------------------
TS = T_SHELF + CLEAR            # top-tile slot height
TW = T_SIDE + CLEAR             # side-tile slot width
X1 = COLUMN / 2                 # column face = inner face of the side slot
X2 = X1 + TW                    # corner-block face = outer face of the side slot
H2 = HUB / 2
ZTOP = TS + CAP                 # top of the cap
ZBOT = ZTOP - HUB               # bottom of the hub
DEPTH = HUB - FRONT             # slot depth along Y
PROTRUDE = CLEAR + CRUSH        # how far a crush rib reaches into its slot

assert H2 - X2 >= 8, f"corner blocks only {H2 - X2:.1f} mm: increase HUB"
assert ZBOT < -25, "side tile clamp too short: increase HUB"

PROFILE_PLANE = Plane(origin=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))  # (u,v) -> (X,0,Z)


def rect(u0: float, u1: float, v0: float, v1: float) -> Sketch:
    return Pos(u0, v0) * Rectangle(u1 - u0, v1 - v0, align=(Align.MIN, Align.MIN))


def near(sketch: Sketch, points: list[tuple[float, float]], tol: float = 1e-3):
    """Vertices of a 2D sketch lying on any of the given (u, v) points."""
    return [
        v for v in sketch.vertices()
        if any(abs(v.X - u) < tol and abs(v.Y - w) < tol for u, w in points)
    ]


def channel(sign: int) -> Sketch:
    """L-shaped channel for one cube: top tile (horizontal) + side tile (vertical)."""
    ch = rect(X1, H2 + 1, 0, TS) + rect(X1, X2, ZBOT - 5, 0)
    return mirror(ch, about=Plane.YZ) if sign < 0 else ch


def profile(outline: Sketch) -> Sketch:
    """Cut both channels out of a hub outline and chamfer their mouths."""
    prof = outline - channel(1) - channel(-1)
    mouths = []
    for s in (1, -1):
        mouths += [(s * H2, TS), (s * H2, 0)]
    bottom = prof.vertices().sort_by(Axis.Y)[0].Y
    for s in (1, -1):
        mouths += [(s * X1, bottom), (s * X2, bottom)]
    return chamfer(near(prof, mouths), LEAD)


def crush_rib_y(wall: tuple[float, float], n: tuple[float, float], depth: float) -> Part:
    """Half-round rib along Y on wall point (x, z), bulging along unit vector n (in XZ)."""
    cu = wall[0] + n[0] * (PROTRUDE - RIB_R)
    cv = wall[1] + n[1] * (PROTRUDE - RIB_R)
    full_len = depth - RIB_END - RIB_RAMP
    straight = extrude(Plane.XZ * Pos(cu, cv) * Circle(RIB_R), amount=-full_len)
    start = Plane.XZ.offset(-full_len) * Pos(cu, cv) * Circle(RIB_R)
    end = Plane.XZ.offset(-(full_len + RIB_RAMP)) * Pos(cu - n[0] * PROTRUDE, cv - n[1] * PROTRUDE) * Circle(RIB_R)
    return straight + loft([start, end], ruled=True)


def hub_body(outline: Sketch, depth: float = DEPTH) -> tuple[Part, Part]:
    """Return (body, crush_ribs) for a hub with the given outside outline (XZ sketch)."""
    body = extrude(PROFILE_PLANE * profile(outline), amount=-depth)   # +Y, into the shelf
    body += extrude(PROFILE_PLANE * outline, amount=FRONT)            # solid front, -Y

    def on_slot(e: Edge) -> bool:
        m = e.center()
        x = abs(m.X)
        cap_or_block = (abs(m.Z - TS) < 1e-3 or abs(m.Z) < 1e-3) and x > X1 + 1e-3
        side_faces = (abs(x - X1) < 1e-3 or abs(x - X2) < 1e-3) and m.Z < -1e-3
        return cap_or_block or side_faces

    back = body.edges().filter_by_position(Axis.Y, depth - 1e-3, depth + 1e-3)
    body = chamfer([e for e in back if on_slot(e)], LEAD)

    ribs = []
    for s in (1, -1):
        for x in (X1 + 3.0, H2 - 4.0):                       # cap underside, pushing down
            ribs.append(crush_rib_y((s * x, TS), (0, -1), depth))
        for z in (-6.0, ZBOT + 5.0):                          # corner-block face, pushing in
            ribs.append(crush_rib_y((s * X2, z), (-s, 0), depth))
    return body, Part(Compound(ribs).fuse())


def plug_body(bottom: float = ZBOT) -> Part:
    """Fills the right-hand channel (nominal tile thickness, so the ribs grip it)."""
    prof = rect(X1, H2, 0, T_SHELF) + rect(X1, X1 + T_SIDE, bottom, 0)
    p = extrude(PROFILE_PLANE * prof, amount=-DEPTH)
    ends = p.edges().filter_by_position(Axis.Y, -1e-3, 1e-3) + \
        p.edges().filter_by_position(Axis.Y, DEPTH - 1e-3, DEPTH + 1e-3)
    return chamfer(ends, 0.5)


def print_pose(parts: dict[str, Part], face_up: bool = True) -> dict[str, Part]:
    """Rotate pieces together so the front face points up (or down), resting on Z=0."""
    rot = Rot(-90, 0, 0) if face_up else Rot(90, 0, 0)
    turned = {k: rot * p for k, p in parts.items()}
    bbs = [p.bounding_box() for p in turned.values()]
    cx = (min(b.min.X for b in bbs) + max(b.max.X for b in bbs)) / 2
    cy = (min(b.min.Y for b in bbs) + max(b.max.Y for b in bbs)) / 2
    z0 = min(b.min.Z for b in bbs)
    return {k: Pos(-cx, -cy, -z0) * p for k, p in turned.items()}


# ---- Thickness gauge (find tile thickness without calipers) ---------------
GAUGE_SIZES = [5.0 + 0.5 * i for i in range(15)]   # 5.0 ... 12.0 mm


def thickness_gauge() -> Part:
    """Comb with labelled slots on two edges; the tightest slot a tile enters ~ its thickness."""
    rows = [GAUGE_SIZES[:8], GAUGE_SIZES[8:]]
    pitch, depth, thick, band = 13.0, 12.0, 5.0, 10.0
    width = len(rows[0]) * pitch + 6
    height = 2 * depth + band
    with BuildPart() as g:
        Box(width, height, thick, align=(Align.CENTER, Align.CENTER, Align.MIN))
        for r, sizes in enumerate(rows):
            sgn = 1 if r == 0 else -1
            for i, s in enumerate(sizes):
                x = (i - (len(rows[0]) - 1) / 2) * pitch
                with Locations((x, sgn * (height / 2 - depth / 2), 0)):
                    Box(s, depth + 0.01, thick, mode=Mode.SUBTRACT,
                        align=(Align.CENTER, Align.CENTER, Align.MIN))
        chamfer(g.edges().group_by(Axis.Z)[0], 0.4)
        with BuildSketch(Plane.XY.offset(thick)):
            for r, sizes in enumerate(rows):
                sgn = 1 if r == 0 else -1
                for i, s in enumerate(sizes):
                    x = (i - (len(rows[0]) - 1) / 2) * pitch
                    with Locations((x, sgn * 2.4)):
                        Text(f"{s:g}", font_size=3.6, font_style=FontStyle.BOLD,
                             rotation=0 if r == 0 else 180)
        extrude(amount=-0.6, mode=Mode.SUBTRACT)
    return g.part
