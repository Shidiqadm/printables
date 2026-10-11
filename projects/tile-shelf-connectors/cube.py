"""Plain cube styling (r2): grooved 3x3-block cube, like the reference photos.

Same interface as deco.py, so model.py and test_fit.py can build either style:
    DIMS, silhouette(), hub() -> (body, crush_ribs, relief | None), plug(), CROWN,
    HAS_TRIMS, HUB_FACE_UP, HAS_MID (+ mid_hub(), mid_plug() when True)
"""

from build123d import *

from core import FRONT, TS, X1, ZTOP, Hub, hub_body, plug_body, rect

# 44 mm face, only 20 mm front-to-back, side tiles clamped 24 mm: about half the plastic of
# a full 44 mm cube. The physical fit test showed a short grip holds; tiles are trapped
# front-to-back by the hubs anyway, so depth mostly buys sway stiffness.
DIMS = Hub(44.0, thick=20.0, clamp=24.0)
ROUND = 2.0               # radius on the cube's long edges
EDGE = 1.0                # chamfer on the front face edges (bed side when printing)
GROOVE_W = 1.0            # decorative grooves along the tile planes
GROOVE_D = 0.6

CROWN = 0.0               # nothing above the cap
HAS_TRIMS = False         # the cube style has no cornice trims
HAS_MID = True            # middle hub + plug for stacking a second row
HUB_FACE_UP = False       # print front face down: smooth bed finish on the visible face


def silhouette(mid: bool = False) -> Sketch:
    top = DIMS.mid_top if mid else ZTOP
    return fillet(rect(-DIMS.h2, DIMS.h2, DIMS.zbot, top).vertices(), ROUND)


def _grooves(mid: bool = False) -> Part:
    """Grooves where the tile planes meet the front and top faces."""
    cuts = []
    span = 4 * DIMS.size
    for x in (-X1, X1):                             # front face, vertical
        cuts.append(Pos(x, -FRONT, 0) * Box(GROOVE_W, 2 * GROOVE_D, span))
        if not mid:                                 # top face (a mid hub has tiles on top)
            cuts.append(Pos(x, 0, ZTOP) * Box(GROOVE_W, 3 * DIMS.size, 2 * GROOVE_D))
    for z in (0.0, TS):                             # front face, horizontal
        cuts.append(Pos(0, -FRONT, z) * Box(2 * DIMS.size, 2 * GROOVE_D, GROOVE_W))
    return Part(Compound(cuts).fuse())


def hub() -> tuple[Part, Part, None]:
    """(body, crush_ribs, None) of the plain cube hub in the shelf frame."""
    body, ribs = hub_body(DIMS, silhouette())
    face = body.edges().filter_by_position(Axis.Y, -FRONT - 1e-3, -FRONT + 1e-3)
    body = chamfer(face, EDGE) - _grooves()
    return body, ribs, None


def plug() -> Part:
    return plug_body(DIMS)


def mid_hub() -> tuple[Part, Part, None]:
    """(body, crush_ribs, None) of the middle hub joining a lower and an upper row."""
    body, ribs = hub_body(DIMS, silhouette(mid=True), mid=True)
    face = body.edges().filter_by_position(Axis.Y, -FRONT - 1e-3, -FRONT + 1e-3)
    body = chamfer(face, EDGE) - _grooves(mid=True)
    return body, ribs, None


def mid_plug() -> Part:
    return plug_body(DIMS, mid=True)
