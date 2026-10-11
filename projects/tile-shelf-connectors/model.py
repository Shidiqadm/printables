"""Tile shelf hubs: heavy-duty cube connectors that turn leftover tiles into a cube shelf.

Spec:    docs/superpowers/specs/2026-10-11-tile-shelf-connectors-design.md
Run:     uv run projects/tile-shelf-connectors/model.py
Test:    uv run projects/tile-shelf-connectors/test_fit.py
Outputs: projects/tile-shelf-connectors/output/
           hub.3mf              universal cube hub, used at every corner
           plug.3mf             fills the unused channel of hubs at the ends of the row
           fit_test.3mf         10 mm slice of half a hub, to try on real tiles
           thickness_gauge.3mf  comb to find tile thickness without calipers

Shelf frame used while modelling: X along the row, Y = depth (0 = front face of the
tiles, +Y to the back), Z up. A hub is modelled at the front-top corner between two cubes:
X=0 is the middle of its centre column, Z=0 is the top edge of the side tiles. Each cube
has its own two side tiles (double walls); every top tile rests on the full edge of its
side tiles. Parts are rotated onto their front face for printing at the very end.
"""

from build123d import *

from printlib import A1, check, export, fit, preview

# ---- Parameters (mm) -------------------------------------------------------
T_SHELF = 8.0             # top / bottom tile thickness (measure with thickness_gauge)
T_SIDE = 8.0              # side tile thickness
THICK_TOL = 0.30          # tiles may be this much thinner/thicker than nominal
CLEAR = THICK_TOL + fit("snug", "linear")   # slot = T + 0.4: a +0.3 tile still slides in
CRUSH = 0.30              # crush-rib interference at nominal (0 at -TOL, 0.6 at +TOL)
HUB = 48.0                # cube size
COLUMN = 8.0              # centre column between the two cubes' side tiles
CAP = A1.wall(12)         # 5.04: cap over the top tiles (foot under the bottom tiles)
FRONT = 5.0               # solid front face that ties the blocks together (25 layers)
ROUND = 2.0               # radius on the cube's long edges
EDGE = 1.0                # chamfer on front and back face edges (front = bed side)
LEAD = 1.0                # lead-in chamfer at slot mouths
GROOVE_W = 1.0            # decorative grooves along the tile planes
GROOVE_D = 0.6
RIB_R = 2.0               # crush-rib radius (wide, gentle ramp for tiles sliding across)
RIB_END = 3.0             # crush ribs stop this far before the back mouth...
RIB_RAMP = 2.0            # ...after ramping down over this length

# Assembly preview only (does not change the printed parts)
TILE_W = 300.0            # top/bottom tile length along the row
TILE_D = 300.0            # shelf depth (tile size front to back)
SIDE_H = 300.0            # side tile height
CUBES = 3

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
PITCH = TILE_W + COLUMN         # hub spacing along the row

assert H2 - X2 >= 8, f"corner blocks only {H2 - X2:.1f} mm: increase HUB"
assert ZBOT < -25, "side tile clamp too short: increase HUB"

PROFILE_PLANE = Plane(origin=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))  # (u,v) -> (X,0,Z)


def _rect(u0: float, u1: float, v0: float, v1: float) -> Sketch:
    return Pos(u0, v0) * Rectangle(u1 - u0, v1 - v0, align=(Align.MIN, Align.MIN))


def _near(sketch: Sketch, points: list[tuple[float, float]], tol: float = 1e-3):
    return [
        v for v in sketch.vertices()
        if any(abs(v.X - u) < tol and abs(v.Y - w) < tol for u, w in points)
    ]


def _outer() -> Sketch:
    sq = _rect(-H2, H2, ZBOT, ZTOP)
    return fillet(sq.vertices(), ROUND)


def _channel(sign: int) -> Sketch:
    """L-shaped channel for one cube: top tile (horizontal) + side tile (vertical)."""
    top = _rect(X1, H2 + 1, 0, TS)
    side = _rect(X1, X2, ZBOT - 1, 0)
    ch = top + side
    return mirror(ch, about=Plane.YZ) if sign < 0 else ch


def _profile() -> Sketch:
    prof = _outer() - _channel(1) - _channel(-1)
    mouths = []
    for s in (1, -1):
        mouths += [(s * H2, TS), (s * H2, 0), (s * X1, ZBOT), (s * X2, ZBOT)]
    return chamfer(_near(prof, mouths), LEAD)


def _crush_rib(wall: tuple[float, float], n: tuple[float, float], depth: float) -> Part:
    """Half-round rib along Y on the wall point `wall`, bulging along unit vector `n`."""
    cu = wall[0] + n[0] * (PROTRUDE - RIB_R)
    cv = wall[1] + n[1] * (PROTRUDE - RIB_R)
    full_len = depth - RIB_END - RIB_RAMP
    straight = extrude(Plane.XZ * Pos(cu, cv) * Circle(RIB_R), amount=-full_len)
    start = Plane.XZ.offset(-full_len) * Pos(cu, cv) * Circle(RIB_R)
    end = Plane.XZ.offset(-(full_len + RIB_RAMP)) * Pos(cu - n[0] * PROTRUDE, cv - n[1] * PROTRUDE) * Circle(RIB_R)
    return straight + loft([start, end], ruled=True)


def _grooves() -> Part:
    """Decorative grooves where the tile planes meet the front and top faces."""
    cuts = []
    for x in (-X1, X1):                             # front face, vertical
        cuts.append(Pos(x, -FRONT, 0) * Box(GROOVE_W, 2 * GROOVE_D, 2 * HUB))
        cuts.append(Pos(x, 0, ZTOP) * Box(GROOVE_W, 3 * HUB, 2 * GROOVE_D))   # top face
    for z in (0.0, TS):                             # front face, horizontal
        cuts.append(Pos(0, -FRONT, z) * Box(2 * HUB, 2 * GROOVE_D, GROOVE_W))
    return Part(Compound(cuts).fuse())


def hub(depth: float = DEPTH) -> tuple[Part, Part]:
    """Return (body, crush_ribs) in the shelf frame, front-top position."""
    body = extrude(PROFILE_PLANE * _profile(), amount=-depth)       # +Y, into the shelf
    body += extrude(PROFILE_PLANE * _outer(), amount=FRONT)         # solid front, -Y

    def on_slot(e: Edge) -> bool:
        m = e.center()
        x = abs(m.X)
        cap_or_block = (abs(m.Z - TS) < 1e-3 or abs(m.Z) < 1e-3) and x > X1 + 1e-3
        side_faces = (abs(x - X1) < 1e-3 or abs(x - X2) < 1e-3) and m.Z < -1e-3
        return cap_or_block or side_faces

    back = body.edges().filter_by_position(Axis.Y, depth - 1e-3, depth + 1e-3)
    body = chamfer([e for e in back if on_slot(e)], LEAD)
    face_edges = body.edges().filter_by_position(Axis.Y, -FRONT - 1e-3, -FRONT + 1e-3)
    body = chamfer(face_edges, EDGE)
    body -= _grooves()

    ribs = []
    for s in (1, -1):
        for x in (X1 + 3.0, H2 - 4.0):                       # cap underside, pushing down
            ribs.append(_crush_rib((s * x, TS), (0, -1), depth))
        for z in (-6.0, ZBOT + 5.0):                          # corner-block face, pushing in
            ribs.append(_crush_rib((s * X2, z), (-s, 0), depth))
    return body, Part(Compound(ribs).fuse())


def solid_hub(depth: float = DEPTH) -> Part:
    body, ribs = hub(depth)
    return body + ribs


def plug() -> Part:
    """Fills the right-hand channel of a hub (nominal tile thickness, so the ribs grip it)."""
    prof = _rect(X1, H2, 0, T_SHELF) + _rect(X1, X1 + T_SIDE, ZBOT, 0)
    p = extrude(PROFILE_PLANE * prof, amount=-DEPTH)
    ends = p.edges().filter_by_position(Axis.Y, -1e-3, 1e-3) + \
        p.edges().filter_by_position(Axis.Y, DEPTH - 1e-3, DEPTH + 1e-3)
    return chamfer(ends, 0.5)


def print_pose(part: Part, back_down: bool = False) -> Part:
    """Front face (or back face) down on the bed, centred on the origin."""
    p = Rot(-90 if back_down else 90, 0, 0) * part
    bb = p.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * p


def fit_test() -> Part:
    """Right half of a hub (column + one channel), 10 mm deep: tests both slots cheaply."""
    half = solid_hub(depth=10.0) & Pos(-X1, -FRONT - 1, ZBOT - 1) * Box(
        H2 + X1 + 1, 30, HUB + 2, align=(Align.MIN, Align.MIN, Align.MIN))
    return half


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


# ---- Assembly preview ------------------------------------------------------
Rz, Rx, Ry = Rot(0, 0, 180), Rot(180, 0, 0), Rot(0, 180, 0)
POSES = {"FT": (0.0, None), "BT": (TILE_D, Rz), "FB": (0.0, Ry), "BB": (TILE_D, Rx)}


def assembly() -> tuple[dict[str, Part], dict[str, Part]]:
    """Hubs, plugs and tiles of a CUBES-wide row in the shelf frame. Preview/tests only."""
    h, pl = solid_hub(), plug()
    pl_left = mirror(pl, about=Plane.YZ)
    z0 = ZTOP                     # bottom tile top face (the foot under it is ZTOP thick)
    zt = z0 + SIDE_H              # side tile top edge
    parts: dict[str, Part] = {}
    for i in range(CUBES + 1):
        x = i * PITCH
        for tag, (y, rot) in POSES.items():
            z = zt if tag.endswith("T") else z0
            place = Pos(x, y, z) * rot if rot else Pos(x, y, z)
            parts[f"hub{i}{tag}"] = place * h
            if i == 0:
                parts[f"plug{i}{tag}"] = place * (pl_left if tag in ("FT", "BB") else pl)
            elif i == CUBES:
                parts[f"plug{i}{tag}"] = place * (pl if tag in ("FT", "BB") else pl_left)

    tiles: dict[str, Part] = {}
    for c in range(CUBES):
        xl, xr = c * PITCH + X1, (c + 1) * PITCH - X1
        cx, length = (xl + xr) / 2, xr - xl - 0.1        # a hair short so faces don't coincide
        tiles[f"top{c}"] = Pos(cx, 0, zt) * Box(length, TILE_D, T_SHELF,
                                               align=(Align.CENTER, Align.MIN, Align.MIN))
        tiles[f"bottom{c}"] = Pos(cx, 0, z0) * Box(length, TILE_D, T_SHELF,
                                                  align=(Align.CENTER, Align.MIN, Align.MAX))
        for name, xs in (("L", xl), ("R", xr - T_SIDE)):
            tiles[f"side{c}{name}"] = Pos(xs, 0, z0) * Box(
                T_SIDE, TILE_D, SIDE_H, align=(Align.MIN, Align.MIN, Align.MIN))
    return parts, tiles


parts = {
    "hub": print_pose(solid_hub()),
    "plug": print_pose(plug(), back_down=True),
    "fit_test": print_pose(fit_test()),
    "thickness_gauge": thickness_gauge(),
}

if __name__ == "__main__":
    for name, p in parts.items():
        check(p, name)
        export(p, name)
    conns, tiles = assembly()
    preview(*conns.values(), *tiles.values(),
            names=list(conns) + list(tiles),
            colors=["#c8642d"] * len(conns) + ["#e8e4dc"] * len(tiles))
