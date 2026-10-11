"""Plain cube styling (r2): grooved 3x3-block cube, like the reference photos.

Same interface as deco.py, so model.py and test_fit.py can build either style:
    silhouette(), hub() -> (body, crush_ribs, relief | None), plug(), CROWN, HAS_TRIMS,
    HUB_FACE_UP
"""

from build123d import *

from core import FRONT, H2, HUB, TS, X1, ZBOT, ZTOP, hub_body, plug_body, rect

ROUND = 2.0               # radius on the cube's long edges
EDGE = 1.0                # chamfer on the front face edges (bed side when printing)
GROOVE_W = 1.0            # decorative grooves along the tile planes
GROOVE_D = 0.6

CROWN = 0.0               # nothing above the cap
HAS_TRIMS = False         # the cube style has no cornice trims
HUB_FACE_UP = False       # print front face down: smooth bed finish on the visible face


def silhouette() -> Sketch:
    return fillet(rect(-H2, H2, ZBOT, ZTOP).vertices(), ROUND)


def _grooves() -> Part:
    """Grooves where the tile planes meet the front and top faces."""
    cuts = []
    for x in (-X1, X1):                             # front face, vertical
        cuts.append(Pos(x, -FRONT, 0) * Box(GROOVE_W, 2 * GROOVE_D, 2 * HUB))
        cuts.append(Pos(x, 0, ZTOP) * Box(GROOVE_W, 3 * HUB, 2 * GROOVE_D))   # top face
    for z in (0.0, TS):                             # front face, horizontal
        cuts.append(Pos(0, -FRONT, z) * Box(2 * HUB, 2 * GROOVE_D, GROOVE_W))
    return Part(Compound(cuts).fuse())


def hub() -> tuple[Part, Part, None]:
    """(body, crush_ribs, None) of the plain cube hub in the shelf frame."""
    body, ribs = hub_body(silhouette())
    face = body.edges().filter_by_position(Axis.Y, -FRONT - 1e-3, -FRONT + 1e-3)
    body = chamfer(face, EDGE) - _grooves()
    return body, ribs, None


def plug() -> Part:
    return plug_body(ZBOT)
