"""Keycap for MX-style stems: a low square cap with draft on the sides, a flat top and a
crisp 45 degree edge round it.

Fits plain MX crosses and box stems (Outemu dust-proof, Kailh BOX): there the cross stands
inside a square rim, and the cap's round post goes down inside that rim, as an MX cap's does.

Printed top-down, the top face on the bed: it takes the plate's texture, like the shell's
deck. The walls and the post grow straight up from the inside of the top (no supports), and
the socket opens upwards, exactly as on the fit coupon's posts. (A finger dish would leave the
middle of the top off the bed, so the top is flat.)

Grip: the slots are wider than the stem's arms, so the cross goes in either way round. Four
crush ribs, one at each arm end, are what hold the cap: they stand RIB_GRIP into the stem's
path, and the stem flattens them the first time the cap goes on. Both arms are 4.0 mm long
(only their thickness differs), so every rib squeezes the same.
"""

from build123d import Align, Axis, Box, Cone, Cylinder, Pos, RectangleRounded, Rot, chamfer, loft

from printlib import A1

# ---- Parameters (mm) -------------------------------------------------------
CAP = 18.0                 # footprint at the skirt (standard 1u cap)
CAP_TOP = 16.6             # footprint at the top face (side draft)
CAP_H = 7.0
CAP_R = 2.4                # plan-view corner radius at the skirt
TOP_CHAMFER = 0.6          # edge round the top (on the bed): crisp, no elephant's foot
CAP_WALL = A1.wall(3)      # 1.26
TOP_T = 1.8                # top thickness
SKIRT_CHAMFER = 0.3        # skirt edge

# MX stem socket. The cross arms are 4.0 mm long; one arm is thicker than the other.
# Measured on Kailh BOX stems: 1.30-1.42 and 1.10-1.24 mm (Kailh spec 1.32 / 1.10); Cherry MX
# 1.31. Both slots are cut for the thick arm, so the cap goes on either way round; it grips
# on the thick arm. Printed holes shrink, so the slop is tuned with the fit coupon.
STEM_D = 5.5               # post: fits inside a box stem's square rim (box switches take MX caps)
POST_CHAMFER = 0.2         # post tip, so it slides into a box stem's rim
CROSS_L = 4.1
CROSS_W = 1.32
STEM_DEPTH = 4.0
STEM_SLOP = 0.10
SOCKET_LEAD = 0.3          # chamfer at the socket mouth: lead-in for the stem

# Crush ribs at the arm ends. A cap with no designed squeeze (v0.8) slid off with a light
# pull, although the same socket felt snug on the coupon: it only held if the print came out
# small. The stem test now varies RIB_GRIP; pick by pulling the post off, not by pushing on.
STEM_ARM = 4.0             # stem arm length, both arms (Cherry MX datasheet)
RIB_GRIP = 0.10            # squeeze per arm end
RIB_R = 0.35               # half-round rib
RIB_START = 0.4            # depth below the mouth where the ribs begin (below the mouth chamfer)
RIB_LEAD = 0.3             # 45 degree lead-in on the rib's mouth end

CEN_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def tapered_block(bottom, top, h, r_bottom):
    """Rounded square lofted from `bottom` to `top`, corner radius scaled with size."""
    r_top = r_bottom * top / bottom
    return loft([RectangleRounded(bottom, bottom, r_bottom),
                 Pos(0, 0, h) * RectangleRounded(top, top, r_top)])


def cross(slop, depth, grow=0.0):
    l, w = CROSS_L + slop + grow, CROSS_W + slop + grow
    return Box(l, w, depth, align=CEN_MIN) + Box(w, l, depth, align=CEN_MIN)


def crush_ribs(grip):
    """Four upright half-round ribs, one beyond each arm end, standing `grip` into the stem's
    path; their mouth ends are chamfered 45 degrees, so the stem rides up onto them."""
    rib = Pos(0, 0, RIB_START) * Cylinder(RIB_R, STEM_DEPTH - RIB_START + 0.02, align=CEN_MIN)
    rib = chamfer(rib.edges().group_by(Axis.Z)[0], length=RIB_LEAD)
    d = STEM_ARM / 2 - grip + RIB_R
    return Pos(d, 0) * rib + Pos(-d, 0) * rib + Pos(0, d) * rib + Pos(0, -d) * rib


def socket(slop, grip=RIB_GRIP):
    """The cross socket, opening at z = 0, with a 45 degree lead-in at the mouth and crush
    ribs at the arm ends."""
    s = Pos(0, 0, -0.01) * cross(slop, STEM_DEPTH + 0.01)
    lead = loft([Pos(0, 0, -0.01) * RectangleRounded(CROSS_L + slop + 2 * SOCKET_LEAD,
                                                    CROSS_W + slop + 2 * SOCKET_LEAD, 0.3),
                 Pos(0, 0, SOCKET_LEAD) * RectangleRounded(CROSS_L + slop, CROSS_W + slop, 0.05)])
    lead2 = loft([Pos(0, 0, -0.01) * RectangleRounded(CROSS_W + slop + 2 * SOCKET_LEAD,
                                                     CROSS_L + slop + 2 * SOCKET_LEAD, 0.3),
                  Pos(0, 0, SOCKET_LEAD) * RectangleRounded(CROSS_W + slop, CROSS_L + slop, 0.05)])
    return s + lead + lead2 - crush_ribs(grip)


def make_keycap(slop=STEM_SLOP, grip=RIB_GRIP):
    """Keycap in its use orientation: skirt at z = 0, top at z = CAP_H, centred on x/y."""
    cap = tapered_block(CAP, CAP_TOP, CAP_H, CAP_R)
    cap = chamfer(cap.edges().group_by(Axis.Z)[-1], length=TOP_CHAMFER)
    cap = chamfer(cap.edges().group_by(Axis.Z)[0], length=SKIRT_CHAMFER)

    inner_h = CAP_H - TOP_T
    shrink = (CAP - CAP_TOP) * inner_h / CAP_H
    inner = CAP - 2 * CAP_WALL
    cap -= Pos(0, 0, -0.01) * tapered_block(inner, inner - shrink, inner_h + 0.01, CAP_R - CAP_WALL / 2)

    cap += Pos(0, 0, POST_CHAMFER) * Cylinder(STEM_D / 2, inner_h - POST_CHAMFER + 0.01, align=CEN_MIN)
    cap += Cone(STEM_D / 2 - POST_CHAMFER, STEM_D / 2, POST_CHAMFER + 0.01, align=CEN_MIN)
    return cap - socket(slop, grip)


def stem_test_post(grip, slop=STEM_SLOP):
    """The cap's post for the fit coupon, standing on the coupon (z = 0) with the socket
    opening at its top: the same diameter, socket and ribs (squeeze `grip`) as the cap, long
    enough to go down inside a box stem's rim. It prints mouth-up, like the cap's post."""
    h = STEM_DEPTH + 0.6
    post = Cylinder(STEM_D / 2, h - POST_CHAMFER, align=CEN_MIN)
    post += Pos(0, 0, h - POST_CHAMFER - 0.01) * Cone(STEM_D / 2, STEM_D / 2 - POST_CHAMFER, POST_CHAMFER + 0.01,
                                                       align=CEN_MIN)
    return post - Pos(0, 0, h) * Rot(180, 0, 0) * socket(slop, grip)
