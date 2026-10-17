"""Keycap for MX-style stems: a low square cap with draft on the sides, a rounded top edge
and a soft spherical dish for the fingertip.

Printed upright, skirt on the bed: no supports, the cross socket prints vertically, and the
shallow dish comes out smooth with fine layers (see README, keycap settings).
"""

from build123d import Align, Axis, Box, Cylinder, Pos, RectangleRounded, Sphere, chamfer, fillet, loft

from printlib import A1

# ---- Parameters (mm) -------------------------------------------------------
CAP = 18.0                 # footprint at the skirt (standard 1u cap)
CAP_TOP = 16.6             # footprint at the top face (side draft)
CAP_H = 7.0
CAP_R = 2.4                # plan-view corner radius at the skirt
TOP_EDGE_R = 0.9
CAP_WALL = A1.wall(3)      # 1.26
TOP_T = 1.8                # top thickness at the edge of the dish
DISH_R = 50.0              # sphere radius of the finger dish
DISH_DEPTH = 0.5           # at the centre: shallow, so the layer steps stay far apart
SKIRT_CHAMFER = 0.3        # bed edge: crisp skirt, no elephant's foot

# MX stem socket. Cherry stem cross: 4.0 mm arms, 1.17 / 1.1 mm thick; printed holes
# shrink, so the slop is tuned with the fit coupon.
STEM_D = 5.5
CROSS_L = 4.1
CROSS_W = 1.17
STEM_DEPTH = 4.0
STEM_SLOP = 0.20
SOCKET_LEAD = 0.3          # chamfer at the socket mouth (on the bed): lead-in for the stem

CEN_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def tapered_block(bottom, top, h, r_bottom):
    """Rounded square lofted from `bottom` to `top`, corner radius scaled with size."""
    r_top = r_bottom * top / bottom
    return loft([RectangleRounded(bottom, bottom, r_bottom),
                 Pos(0, 0, h) * RectangleRounded(top, top, r_top)])


def cross(slop, depth, grow=0.0):
    l, w = CROSS_L + slop + grow, CROSS_W + slop + grow
    return Box(l, w, depth, align=CEN_MIN) + Box(w, l, depth, align=CEN_MIN)


def socket(slop):
    """The cross socket, opening at z = 0, with a 45 degree lead-in at the mouth."""
    s = Pos(0, 0, -0.01) * cross(slop, STEM_DEPTH + 0.01)
    lead = loft([Pos(0, 0, -0.01) * RectangleRounded(CROSS_L + slop + 2 * SOCKET_LEAD,
                                                    CROSS_W + slop + 2 * SOCKET_LEAD, 0.3),
                 Pos(0, 0, SOCKET_LEAD) * RectangleRounded(CROSS_L + slop, CROSS_W + slop, 0.05)])
    lead2 = loft([Pos(0, 0, -0.01) * RectangleRounded(CROSS_W + slop + 2 * SOCKET_LEAD,
                                                     CROSS_L + slop + 2 * SOCKET_LEAD, 0.3),
                  Pos(0, 0, SOCKET_LEAD) * RectangleRounded(CROSS_W + slop, CROSS_L + slop, 0.05)])
    return s + lead + lead2


def make_keycap(slop=STEM_SLOP):
    """Keycap in its use orientation: skirt at z = 0, top at z = CAP_H, centred on x/y."""
    cap = tapered_block(CAP, CAP_TOP, CAP_H, CAP_R)
    cap = fillet(cap.edges().group_by(Axis.Z)[-1], radius=TOP_EDGE_R)
    cap = chamfer(cap.edges().group_by(Axis.Z)[0], length=SKIRT_CHAMFER)
    cap -= Pos(0, 0, CAP_H - DISH_DEPTH + DISH_R) * Sphere(DISH_R)

    inner_h = CAP_H - TOP_T
    shrink = (CAP - CAP_TOP) * inner_h / CAP_H
    inner = CAP - 2 * CAP_WALL
    cap -= Pos(0, 0, -0.01) * tapered_block(inner, inner - shrink, inner_h + 0.01, CAP_R - CAP_WALL / 2)

    cap += Cylinder(STEM_D / 2, inner_h + 0.01, align=CEN_MIN)
    return cap - socket(slop)


def stem_socket_post(slop, h):
    """A free-standing stem socket for the fit coupon (same opening as the cap)."""
    return Cylinder(STEM_D / 2 + 1.5, h, align=CEN_MIN) - socket(slop)
