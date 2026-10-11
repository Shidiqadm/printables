"""Art Deco styling for the tile shelf: "skyscraper corner" hub, end plugs, cornice trims.

Same interface as cube.py: silhouette(), hub(), plug(), CROWN, HAS_TRIMS, HUB_FACE_UP.

Only the outside changes; the tile channels and crush ribs come from core.py untouched.

Hub:  stepped crown on the cap (a stepped plinth when the hub is flipped to the bottom),
      corner blocks stepping in like Deco corbels, and a raised front relief: a spire up
      the column, two speed lines across the tile band and a sunburst fan from the point
      where the tiles meet. The relief is a separate body for a second (gold) filament.
Plug: end plug whose outer face carries the speed lines round the corner.
Trim: C-section clip for the front edge of a top/bottom tile between two hubs, with speed
      lines; a medallion with a stepped keystone and sunburst sits at mid-span.
"""

import math

from build123d import *

from core import (
    CRUSH, FRONT, H2, LEAD, PROFILE_PLANE, PROTRUDE, RIB_R, T_SHELF, TS, X1, ZBOT, ZTOP,
    hub_body, near, plug_body, rect,
)

# ---- Style parameters (mm) -------------------------------------------------
CROWN_STEP = 1.6          # height of each crown / plinth tier
CROWN_INSETS = (4.0, 10.0)  # how far each tier steps in from the hub sides
CORBEL_STEP = 2.0         # how far each corbel setback steps in
CORBEL_LEVELS = (-9.0, -18.0, -27.0)  # Z of the three setbacks
RELIEF = 1.2              # height of the raised (gold) relief
RELIEF_MARGIN = 1.5       # relief keeps this far inside the silhouette
SPEED_Z = (0.3 * TS, 0.7 * TS)  # speed lines across the tile band
LINE_W = 0.9              # width of speed lines
RAY_W = 1.1               # width of sunburst rays
RAY_ANGLES = [-90 + k * 18 for k in range(-4, 5)]  # degrees, fanning downwards
RING_R = 5.0              # sunburst hub ring radius
FACE_CHAMFER = 0.6        # chamfer on silhouette corners and face edges

# Trim / medallion
TRIM_FACE = FRONT - 1.0   # trim face sits 1 mm behind the hub face
LIP = 7.0                 # how far the trim lips reach over/under the tile
LIP_T = 2.0               # lip thickness
TRIM_GAP = 0.5            # gap between trim pieces and to the hubs
MEDALLION_W = 36.0        # medallion width
KEY_STEPS = ((-10.0, 0.0), (-18.0, 8.0), (-28.0, 16.0))  # (bottom Z, width reduction)

CROWN = CROWN_STEP * len(CROWN_INSETS)
HAS_TRIMS = True          # cornice trims + medallions belong to this style
HUB_FACE_UP = True        # print decorated face up: relief prints as top surfaces
HUB_HALF_DIAG = math.hypot(H2, ZBOT)  # long enough for rays to reach the silhouette


def _polygon(points: list[tuple[float, float]], chamfer_len: float) -> Sketch:
    """Closed CCW polygon with its convex corners chamfered."""
    poly = Sketch() + Polygon(*points, align=None)
    convex = []
    n = len(points)
    for i, (x, y) in enumerate(points):
        px, py = points[i - 1]
        nx, ny = points[(i + 1) % n]
        if (x - px) * (ny - y) - (y - py) * (nx - x) > 0:
            convex.append((x, y))
    return chamfer(near(poly, convex), chamfer_len)


def silhouette() -> Sketch:
    """Front outline of the Deco hub: crown on top, stepped corbels below."""
    d = CORBEL_STEP
    s1, s2, s3 = (-z for z in CORBEL_LEVELS)
    right = [
        (H2 - 3 * d, ZBOT), (H2 - 3 * d, -s3), (H2 - 2 * d, -s3), (H2 - 2 * d, -s2),
        (H2 - d, -s2), (H2 - d, -s1), (H2, -s1), (H2, ZTOP),
    ]
    z = ZTOP
    for inset in CROWN_INSETS:
        right += [(H2 - inset, z), (H2 - inset, z + CROWN_STEP)]
        z += CROWN_STEP
    left = [(-x, y) for x, y in reversed(right)]
    return _polygon(right + left, FACE_CHAMFER)


def _fan(apex: tuple[float, float], length: float) -> Sketch:
    rays = Sketch()
    for a in RAY_ANGLES:
        rays += Pos(*apex) * Rot(0, 0, a) * Pos(RING_R + 1.5, 0) * Rectangle(
            length, RAY_W, align=(Align.MIN, Align.CENTER))
    ring = Pos(*apex) * (Circle(RING_R + 0.5) - Circle(RING_R - 0.5))
    half = Pos(apex[0], apex[1]) * Rectangle(4 * RING_R, 2 * RING_R, align=(Align.CENTER, Align.MAX))
    return rays + (ring & half)


def hub_relief_sketch() -> Sketch:
    spire = rect(-1.6, 1.6, -RING_R + 0.5, ZTOP + CROWN - 0.8)
    lines = Sketch()
    for z in SPEED_Z:
        lines += rect(-H2, H2, z - LINE_W / 2, z + LINE_W / 2)
    art = spire + lines + _fan((0.0, 0.0), 2 * HUB_HALF_DIAG)
    return art & offset(silhouette(), amount=-RELIEF_MARGIN)


def _relief(sketch: Sketch, face_y: float) -> Part:
    """Raise a front-face XZ sketch by RELIEF in front of the face at Y = face_y."""
    plane = Plane(origin=(0, face_y, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    return extrude(plane * sketch, amount=RELIEF)


def _chamfer_face(part: Part, face_y: float) -> Part:
    return chamfer(part.edges().filter_by_position(Axis.Y, face_y - 1e-3, face_y + 1e-3), FACE_CHAMFER)


def hub() -> tuple[Part, Part, Part]:
    """(body, crush_ribs, relief) of the Deco hub in the shelf frame, front-top position."""
    body, ribs = hub_body(silhouette())
    body = _chamfer_face(body, -FRONT)
    return body, ribs, _relief(hub_relief_sketch(), -FRONT)


def plug() -> Part:
    """End plug; speed-line grooves on its outer face continue the hub's front lines."""
    p = plug_body(ZBOT)
    for z in SPEED_Z:
        p -= Pos(H2, 0, z) * Box(1.0, 200, LINE_W, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    return p


# ---- Cornice trim and medallion --------------------------------------------
def _trim_profile() -> Sketch:
    """YZ section of the clip: front plate + lips over and under the tile (tile at Z 0..T)."""
    pts = [
        (-TRIM_FACE, -LIP_T), (LIP, -LIP_T), (LIP, 0.0), (0.0, 0.0), (0.0, TS),
        (LIP, TS), (LIP, TS + LIP_T), (-TRIM_FACE, TS + LIP_T),
    ]
    prof = Sketch() + Polygon(*pts, align=None)
    prof = chamfer(near(prof, [(LIP, 0.0), (LIP, TS)]), 0.8)     # lead-in
    return chamfer(near(prof, [(-TRIM_FACE, -LIP_T), (-TRIM_FACE, TS + LIP_T),
                               (LIP, -LIP_T), (LIP, TS + LIP_T)]), 0.5)


def _trim_lines(length: float) -> Sketch:
    lines = Sketch()
    for z in (-LIP_T + 1.6, TS / 2, TS + LIP_T - 1.6):
        lines += rect(-length / 2 + 2.0, length / 2 - 2.0, z - LINE_W / 2, z + LINE_W / 2)
    return lines


def _trim_ribs(length: float) -> Part:
    ribs = []
    for y in (2.0, 5.0):
        c = (0, y, TS - PROTRUDE + RIB_R)
        ribs.append(Pos(*c) * Rot(0, 90, 0) * Cylinder(RIB_R, length - 4.0))
    return Part(Compound(ribs).fuse())


def trim(length: float) -> tuple[Part, Part, Part]:
    """(body, crush_ribs, relief): straight cornice clip of the given length, centred on X=0."""
    plane = Plane(origin=(-length / 2, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    body = extrude(plane * _trim_profile(), amount=length)   # long edges chamfered in profile
    return body, _trim_ribs(length), _relief(_trim_lines(length), -TRIM_FACE)


def _keystone_outline() -> Sketch:
    """Stepped keystone below the tile edge; its top overlaps the trim's lower lip."""
    w = MEDALLION_W / 2
    right_down, top = [], 0.0
    for bottom, red in KEY_STEPS:
        right_down += [(w - red / 2, top), (w - red / 2, bottom)]
        top = bottom
    points = list(reversed(right_down)) + [(-x, y) for x, y in right_down]   # CCW
    return _polygon(points, FACE_CHAMFER)


def medallion() -> tuple[Part, Part, Part]:
    """Mid-span clip with a stepped keystone and sunburst, hanging below the tile edge."""
    body, ribs, _ = trim(MEDALLION_W)
    key_plane = Plane(origin=(0, -TRIM_FACE, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    key = extrude(key_plane * _keystone_outline(), amount=-(TRIM_FACE + LIP))
    body = body + key
    art = _trim_lines(MEDALLION_W) + (
        _fan((0.0, -LIP_T), 40.0) & offset(_keystone_outline(), amount=-RELIEF_MARGIN))
    return body, ribs, _relief(art, -TRIM_FACE)


def trim_half_length(pitch: float) -> float:
    """Length of each trim half for a given hub pitch."""
    span = pitch - 2 * H2 - 2 * TRIM_GAP
    return (span - MEDALLION_W - 2 * TRIM_GAP) / 2
