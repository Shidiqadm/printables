"""Tile shelf connectors: friction-fit corners that turn leftover tiles into a cube shelf.

Spec:    docs/superpowers/specs/2026-10-11-tile-shelf-connectors-design.md
Run:     uv run projects/tile-shelf-connectors/model.py
Outputs: projects/tile-shelf-connectors/output/
           middle.3mf, end.3mf, end_mirrored.3mf   the connectors (print orientation)
           fit_test.3mf                            short middle section to try on real tiles
           thickness_gauge.3mf                     comb to find tile thickness without calipers

Coordinates while modelling ("shelf frame"): X along the row, Y = depth (0 = front face
of the tiles, +Y to the back), Z up. A connector is modelled at the front-top corner of a
side tile: Z=0 is the side tile's top edge, X=0 its mid-plane. Parts are rotated onto their
front plate for printing at the very end.
"""

from build123d import *

from printlib import A1, check, export, fit, preview

# ---- Parameters (mm) -------------------------------------------------------
T_SHELF = 8.0             # top / bottom tile thickness (measure with thickness_gauge)
T_SIDE = 8.0              # side tile thickness
THICK_TOL = 0.30          # tiles may be this much thinner/thicker than nominal
CLEAR = THICK_TOL + fit("snug", "linear")   # slot = T + 0.4: a +0.3 tile still slides in
CRUSH = 0.30              # crush-rib interference at nominal (0 at -TOL, 0.6 at +TOL)
RIB = 2.0                 # rib separating neighbouring top tiles
PLATE = A1.wall(8)        # 3.36: jaws and walls, 8 extrusion lines = solid
CAP = A1.wall(10)         # 4.2: cap over the top tiles (foot under bottom tiles)
ARM = 28.0                # clamp reach along each tile, beyond the side tile
DEPTH = 30.0              # how far the connector reaches back along the tile edges
FRONT = 3.0               # front plate (15 layers)
EDGE = 1.0                # chamfer on outside corners / visible face
LEAD = 1.0                # lead-in chamfer at slot mouths
GUSSET = 3.0              # fillet in the inside corners where jaws meet (stress relief)
RIB_R = 2.0               # crush-rib radius (wide, gentle ramp for tiles sliding across)
RIB_END = 3.0             # crush ribs stop this far before the back mouth...
RIB_RAMP = 2.0            # ...after ramping down over this length

# Assembly preview only (does not change the printed parts)
TILE_W = 300.0            # top/bottom tile length along the row
TILE_D = 300.0            # shelf depth (tile size front to back)
SIDE_H = 300.0            # side tile height
CUBES = 3

# ---- Derived ---------------------------------------------------------------
TS = T_SHELF + CLEAR            # shelf slot height
XW = (T_SIDE + CLEAR) / 2       # half width of the side slot
XJ = XW + PLATE                 # outer face of the side jaws
U = XW + ARM                    # wing end
TOP = TS + CAP                  # top of the cap
PROTRUDE = CLEAR + CRUSH        # how far a crush rib reaches into its slot

PROFILE_PLANE = Plane(origin=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))  # (u,v) -> (X,0,Z)


def _rect(u0: float, u1: float, v0: float, v1: float) -> Sketch:
    return Pos(u0, v0) * Rectangle(u1 - u0, v1 - v0, align=(Align.MIN, Align.MIN))


def _near(sketch: Sketch, points: list[tuple[float, float]], tol: float = 1e-3):
    return [
        v for v in sketch.vertices()
        if any(abs(v.X - u) < tol and abs(v.Y - w) < tol for u, w in points)
    ]


def _outer(kind: str, arm: float) -> Sketch:
    """Outline of the connector seen from the front, before slots are cut."""
    u_wing = XW + arm
    left = -u_wing if kind == "middle" else -XJ
    shape = _rect(left, u_wing, -PLATE, TOP) + _rect(-XJ, XJ, -arm, TOP)
    convex = [(u_wing, TOP), (u_wing, -PLATE), (XJ, -arm), (-XJ, -arm), (left, TOP)]
    concave = [(XJ, -PLATE)]
    if kind == "middle":
        convex.append((left, -PLATE))
        concave.append((-XJ, -PLATE))
    shape = chamfer(_near(shape, convex), EDGE)
    return fillet(_near(shape, concave), GUSSET)


def _slots(kind: str, arm: float) -> Sketch:
    u_wing = XW + arm
    side = _rect(-XW, XW, -arm - 1, 0)
    if kind == "middle":
        return _rect(RIB / 2, u_wing + 1, 0, TS) + _rect(-u_wing - 1, -RIB / 2, 0, TS) + side
    return _rect(-XW, u_wing + 1, 0, TS) + side


def _crush_rib(u: float, v: float, depth: float) -> Part:
    """Half-round rib along Y whose crest sits at (u, v); ramps into the wall near the mouth."""
    # centre sits RIB_R behind the crest, on the wall side
    if abs(v - (TS - PROTRUDE)) < 1e-6:          # on the cap underside, pointing -v
        c, back = (u, v + RIB_R), (0, PROTRUDE)
    else:                                         # on the +u side jaw, pointing -u
        c, back = (u + RIB_R, v), (PROTRUDE, 0)
    full_len = depth - RIB_END - RIB_RAMP
    straight = extrude(Plane.XZ.offset(0) * Pos(c[0], c[1]) * Circle(RIB_R), amount=-full_len)
    start = Plane.XZ.offset(-full_len) * Pos(c[0], c[1]) * Circle(RIB_R)
    end = Plane.XZ.offset(-(full_len + RIB_RAMP)) * Pos(c[0] + back[0], c[1] + back[1]) * Circle(RIB_R)
    return straight + loft([start, end], ruled=True)


def connector(kind: str = "middle", arm: float = ARM, depth: float = DEPTH) -> tuple[Part, Part]:
    """Return (body, crush_ribs) in the shelf frame, front-top position.

    kind: "middle" (two wings + rib) or "end" (one wing, closed outer wall on -X).
    """
    u_wing = XW + arm
    outline = _outer(kind, arm)
    profile = outline - _slots(kind, arm)
    mouths = [(u_wing, TS), (u_wing, 0), (XW, -arm), (-XW, -arm)]
    if kind == "middle":
        mouths += [(-u_wing, TS), (-u_wing, 0)]
    profile = chamfer(_near(profile, mouths), LEAD)

    body = extrude(PROFILE_PLANE * profile, amount=-depth)          # +Y, into the shelf
    body += extrude(PROFILE_PLANE * outline, amount=FRONT)          # front plate, -Y

    # lead-in chamfer around the back mouths of the slots
    back_edges = body.edges().filter_by_position(Axis.Y, depth - 1e-3, depth + 1e-3)
    def on_slot(e: Edge) -> bool:
        m = e.center()
        horiz = abs(m.Z - TS) < 1e-3 or (abs(m.Z) < 1e-3 and abs(m.X) > XW)
        vert = abs(abs(m.X) - XW) < 1e-3 and m.Z < 0
        return horiz or vert
    body = chamfer([e for e in back_edges if on_slot(e)], LEAD)
    # visible front face edges (also the bed side, so this hides elephant's foot)
    body = chamfer(body.edges().filter_by_position(Axis.Y, -FRONT - 1e-3, -FRONT + 1e-3), EDGE)

    rib_v_cap = TS - PROTRUDE
    if kind == "middle":
        cap_us = [XW + 3, u_wing - 4, -(XW + 3), -(u_wing - 4)]
    else:
        cap_us = [-XW + 3, u_wing - 4]
    ribs = [_crush_rib(u, rib_v_cap, depth) for u in cap_us]
    ribs += [_crush_rib(XW - PROTRUDE, v, depth) for v in (-6.0, -(arm - 5.0))]
    rib_part = Part(Compound(ribs).fuse()) if len(ribs) > 1 else ribs[0]
    return body, rib_part


def solid(kind: str, arm: float = ARM, depth: float = DEPTH, mirrored: bool = False) -> Part:
    body, ribs = connector(kind, arm, depth)
    part = body + ribs
    return mirror(part, about=Plane.YZ) if mirrored else part


def print_pose(part: Part) -> Part:
    """Front plate down on the bed, centred on the origin."""
    p = Rot(90, 0, 0) * part
    bb = p.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * p


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


def side_positions() -> list[float]:
    xs = [0.0, TILE_W + RIB / 2 - XW]
    for _ in range(CUBES - 2):
        xs.append(xs[-1] + TILE_W + RIB)
    xs.append(xs[-1] + RIB / 2 + TILE_W - XW)
    return xs


def assembly() -> tuple[dict[str, Part], dict[str, Part]]:
    """Connectors and tiles of a CUBES-wide row, in the shelf frame. Preview/tests only."""
    mid, end = solid("middle"), solid("end")
    end_m = solid("end", mirrored=True)
    z0 = TOP                      # bottom tile top face (foot under it is TOP thick)
    zt = z0 + SIDE_H              # side tile top edge
    xs = side_positions()
    conns: dict[str, Part] = {}
    for i, x in enumerate(xs):
        if 0 < i < len(xs) - 1:
            place = {"FT": (0, zt, None, mid), "BT": (TILE_D, zt, Rz, mid),
                     "FB": (0, z0, Ry, mid), "BB": (TILE_D, z0, Rx, mid)}
        elif i == 0:
            place = {"FT": (0, zt, None, end), "BT": (TILE_D, zt, Rz, end_m),
                     "FB": (0, z0, Ry, end_m), "BB": (TILE_D, z0, Rx, end)}
        else:
            place = {"FT": (0, zt, None, end_m), "BT": (TILE_D, zt, Rz, end),
                     "FB": (0, z0, Ry, end), "BB": (TILE_D, z0, Rx, end_m)}
        for tag, (y, z, rot, p) in place.items():
            conns[f"c{i}{tag}"] = Pos(x, y, z) * (rot * p if rot else p)

    tiles: dict[str, Part] = {}
    for i, x in enumerate(xs):
        tiles[f"side{i}"] = Pos(x, 0, z0) * Box(T_SIDE, TILE_D, SIDE_H,
                                                 align=(Align.CENTER, Align.MIN, Align.MIN))
    for c in range(CUBES):
        x_l = xs[c] - XW if c == 0 else xs[c] + RIB / 2
        x_r = xs[c + 1] + XW if c == CUBES - 1 else xs[c + 1] - RIB / 2
        length = x_r - x_l - 0.1                      # leave a hair so faces don't coincide
        cx = (x_l + x_r) / 2
        tiles[f"top{c}"] = Pos(cx, 0, zt) * Box(length, TILE_D, T_SHELF,
                                               align=(Align.CENTER, Align.MIN, Align.MIN))
        tiles[f"bottom{c}"] = Pos(cx, 0, z0) * Box(length, TILE_D, T_SHELF,
                                                  align=(Align.CENTER, Align.MIN, Align.MAX))
    return conns, tiles


parts = {
    "middle": print_pose(solid("middle")),
    "end": print_pose(solid("end")),
    "end_mirrored": print_pose(solid("end", mirrored=True)),
    "fit_test": print_pose(solid("middle", arm=14.0, depth=10.0)),
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
