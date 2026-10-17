"""HK radar pods: corner-mounted presence sensors that also act as the remote's ESP-NOW
gateway. An ESP32-C3 SuperMini runs ESPHome, behind a solid 0.8 mm radar window.

Two variants share the pod shell, the slide-on rails and the orange corner bracket:
  ld2410c  HLK-LD2410C radar + SuperMini soldered back to back as one sandwich. The
           sandwich slides in from the open back; its radar edges rest on two side ribs.
  ld2450   HLK-LD2450 tracking radar (44 x 15 mm), long side horizontal, its ends in two card
           guides; the SuperMini stands behind its middle, wired with the 4-pin cable.

In both, the SuperMini stands USB-C end down in a floor channel, a ceiling stop above it
takes the push when the cable goes in, and the cable leaves through the pod floor.

Printed parts:
  pod      prints window-down, so the window is flat and solid
  bracket  orange corner wedge for two walls meeting at 90 degrees (VHB tape on its back
           faces); its face tilts down by TILT and the pod slides down onto its rails

Radar window: <= 1/8 wavelength in PLA (0.8 mm), solid, no metal or paint (Hi-Link radome
guidance). RADOME_GAP = 12.4 (one wavelength at 24 GHz) is Hi-Link's ideal; the default
keeps the pod slim.

World frame: the walls are the planes x = 0 and y = 0, the room is +x/+y, z is up.
Pod frame (on the bracket face): x across the face, y up the face, z out of the face.
"""

from math import cos, radians, sin, sqrt
from types import SimpleNamespace

from build123d import (
    Align, Axis, Box, Compound, Location, Plane, Polygon, Pos, Rot, SlotCenterToCenter, Vector,
    chamfer, extrude,
)

from printlib import A1, fit
from style import USB_PORT_H, USB_PORT_W, USB_SKIN, interference, rounded_block, usb_receptacle

CEN_MIN = (Align.CENTER, Align.CENTER, Align.MIN)

# ---- Shared parameters (mm) ------------------------------------------------
POD_H = 28.0
POD_R = 4.0                # corner radius seen from the front
POD_EDGE = 1.2             # 45 degree chamfer on the front edges (on the bed when printing)
POD_WALL = A1.wall(5)      # 2.1
FRONT_T = 2.0
RADOME_T = A1.layers(4)    # 0.8 radar window
RADOME_GAP = 3.0           # antenna -> window inner surface
BACK_GAP = 0.6             # sandwich / SuperMini back -> bracket face (room for a foam pad)

SM_L, SM_W = 22.52, 18.0   # ESP32-C3 SuperMini PCB
SM_USB_OVERHANG = 1.0      # receptacle past the PCB edge: not published, measure yours
SEAT_CLEAR = fit("slip", "linear") / 2       # per side, SuperMini in its floor channel
SEAT_DEPTH = POD_WALL - USB_SKIN - SM_USB_OVERHANG  # PCB end into the floor: 0.7 mm skin left
TOP_STOP_GAP = 0.3         # ceiling stop -> SuperMini top end

# Slide mount: grooves in the pod's side walls, open at the bottom; rails on the bracket
GROOVE_Z, GROOVE_W, GROOVE_DEPTH = 1.0, 1.8, 1.0
GROOVE_STOP = 3.0          # groove ends this far below the pod top: the pod rests on the rails
RAIL_CLEAR = fit("loose", "linear") / 2      # per side, tongue in groove (slides freely)
RAIL_POST = A1.wall(4)
BRACKET_MARGIN = 1.0       # face extends this far past the pod top and bottom
CHORD_MARGIN = 1.2         # extra face width beyond the rails at the narrowest (bottom) edge

VARIANTS = {
    # LD2410C sandwich (measure yours): radar antenna side forward, SuperMini behind
    "ld2410c": dict(TILT=20.0, LD_W=22.0, LD_H=16.0, LD_STACK=2.8, LD_CLEAR=fit("slip", "linear") / 2,
                    STACK_T=8.0, STACK_USB_FROM_BACK=1.6, SM_PCB_Z=(0.0, 4.0), WINDOW=(20.0, 18.0)),
    # LD2450 + separate SuperMini (measure yours)
    "ld2450": dict(TILT=10.0, LD_W=44.0, LD_H=15.0, LD_STACK=3.0, LD_CLEAR=0.25,
                   LD_CONN=(6.0, 6.0, 5.0), LD_CONN_X=18.5, LD_HEADER=(4.0, 8.0, 6.0), SM_T=4.6, SM_USB_FROM_BACK=1.6, WIRE_GAP=1.6,
                   GUIDE_W=2.0, GUIDE_LEN=4.0, GUIDE_SLOT_CLEAR=0.1, WINDOW=(40.0, 18.0)),
}


def config(kind: str) -> SimpleNamespace:
    c = SimpleNamespace(kind=kind, **VARIANTS[kind])
    c.INNER_W = c.LD_W + 2 * c.LD_CLEAR
    c.POD_W = round(c.INNER_W + 2 * POD_WALL, 2)
    c.FLOOR_IN = -POD_H / 2 + POD_WALL
    c.CEIL_IN = POD_H / 2 - POD_WALL
    c.SM_Y0 = c.FLOOR_IN - SEAT_DEPTH  # USB end of the SuperMini PCB, in the floor channel
    c.SM_YC = c.SM_Y0 + SM_L / 2
    if kind == "ld2410c":
        c.STACK_Z0 = BACK_GAP
        c.LD_Z1 = c.STACK_Z0 + c.STACK_T  # radar antenna face
        c.USB_Z = c.STACK_Z0 + c.STACK_USB_FROM_BACK
        c.SM_Z = (c.STACK_Z0 + c.SM_PCB_Z[0], c.STACK_Z0 + c.SM_PCB_Z[1])
        c.LD_YC = c.SM_Y0 + (SM_L - c.LD_H) / 2 + c.LD_H / 2  # boards centred on each other
    else:
        c.SM_Z = (BACK_GAP, BACK_GAP + c.SM_T)
        c.LD_Z1 = c.SM_Z[1] + c.WIRE_GAP + c.LD_STACK
        c.USB_Z = BACK_GAP + c.SM_USB_FROM_BACK
        c.LD_YC = 0.0
        c.GUIDE_X0 = c.INNER_W / 2 - c.GUIDE_W
    c.POD_D = round(c.LD_Z1 + RADOME_GAP + RADOME_T, 2)
    c.FRONT_IN = c.POD_D - FRONT_T
    # The window must stay between the ribs / card guides, or they'd hang over it in print
    assert c.WINDOW[0] / 2 <= (c.GUIDE_X0 if kind == "ld2450" else c.INNER_W / 2 - 1.0), "window undercuts"

    a = radians(c.TILT)
    c.FACE_W = c.POD_W + 2 * (RAIL_CLEAR + RAIL_POST)
    c.FACE_H = POD_H + 2 * BRACKET_MARGIN
    r_bottom = c.FACE_W / 2 + CHORD_MARGIN  # corner -> face centre, bottom edge (horizontal)
    c.R_C = r_bottom + (c.FACE_H / 2) * sin(a)
    c.Z_C = (c.FACE_H / 2) * cos(a)
    c.A = a
    u = Vector(-1 / sqrt(2), 1 / sqrt(2), 0)                  # across the face, horizontal
    n = Vector(cos(a) / sqrt(2), cos(a) / sqrt(2), -sin(a))   # out of the face, tilted down
    c.FACE = Plane(origin=(c.R_C / sqrt(2), c.R_C / sqrt(2), c.Z_C), x_dir=u, z_dir=n)
    return c


def pod_local(c):
    """Pod in the pod frame: back face on z = 0 (against the bracket), front at z = POD_D."""
    pod = Pos(-c.POD_W / 2, -POD_H / 2, 0) * rounded_block(c.POD_W, POD_H, c.POD_D, POD_R)
    pod = chamfer(pod.edges().group_by(Axis.Z)[-1], length=POD_EDGE)
    cav_h = POD_H - 2 * POD_WALL
    pod -= Pos(-c.INNER_W / 2, -cav_h / 2, -0.01) * rounded_block(c.INNER_W, cav_h, c.FRONT_IN + 0.01,
                                                                   max(POD_R - POD_WALL, 0.5))
    # Radar window: the front wall thinned to RADOME_T in front of the radar
    ww, wh = c.WINDOW
    pod -= Pos(0, c.LD_YC, c.FRONT_IN - 0.01) * Box(ww, wh, FRONT_T - RADOME_T + 0.01, align=CEN_MIN)

    if c.kind == "ld2410c":
        # Side ribs the radar's front edges rest against; a foam pad on the bracket face holds
        # the sandwich forward from behind
        rib_len = c.FRONT_IN - c.LD_Z1
        for s in (-1, 1):
            pod += Pos(s * (c.INNER_W / 2 - 0.5), c.LD_YC, c.LD_Z1) * Box(1.02, c.LD_H, rib_len + 0.01,
                                                                           align=CEN_MIN)
    else:
        # Card guides: a block on each side wall with a slot the radar's end slides into; the
        # slot stops at the antenna face, so the block's front part sets the window gap
        z0 = c.LD_Z1 - c.GUIDE_LEN
        for s in (-1, 1):
            xc = s * (c.GUIDE_X0 + c.GUIDE_W / 2)
            block = Pos(xc, 0, z0) * Box(c.GUIDE_W + 0.02, cav_h + 0.02, c.FRONT_IN - z0 + 0.01, align=CEN_MIN)
            block -= Pos(xc, c.LD_YC, z0 - 0.01) * Box(c.GUIDE_W + 1, c.LD_H + 2 * c.GUIDE_SLOT_CLEAR,
                                                     c.LD_Z1 - z0 + 0.01, align=CEN_MIN)
            pod += block

    # Floor channel: the SuperMini's USB end drops in, fixing it sideways and front-to-back.
    # Open at the back, so the board slides straight in.
    z0, z1 = c.SM_Z[0] - SEAT_CLEAR, c.SM_Z[1] + SEAT_CLEAR
    pod -= Pos(0, c.SM_Y0, -0.01) * Box(SM_W + 2 * SEAT_CLEAR, SEAT_DEPTH + 0.01, z1 + 0.01,
                                        align=(Align.CENTER, Align.MIN, Align.MIN))
    # Ceiling stop: takes the push when the cable goes in. Its front side slopes at 45 degrees,
    # which is its underside when the pod prints window-down.
    sm_top = c.SM_Y0 + SM_L
    stop_l = c.CEIL_IN - (sm_top + TOP_STOP_GAP)
    if stop_l > 0.2:
        y_bot, y_top = sm_top + TOP_STOP_GAP, c.CEIL_IN + 0.01
        prof = Plane.YZ * Polygon((y_bot, z0), (y_top, z0), (y_top, z1 + stop_l), (y_bot, z1), align=None)
        pod += extrude(prof, amount=3.0, both=True)
    # USB-C through the floor, under the board
    slot = extrude(SlotCenterToCenter(USB_PORT_W - USB_PORT_H, USB_PORT_H), amount=POD_WALL + 2)
    pod -= Location((0, -POD_H / 2 - 1, c.USB_Z), (-90, 0, 0)) * slot
    # Slide grooves in both side walls, open at the bottom
    groove_h = POD_H - GROOVE_STOP
    for s in (-1, 1):
        pod -= Pos(s * (c.POD_W / 2 - GROOVE_DEPTH / 2 + 0.01), -POD_H / 2 - 0.01 + groove_h / 2, GROOVE_Z) * Box(
            GROOVE_DEPTH + 0.02, groove_h + 0.02, GROOVE_W, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return pod


def rails_local(c):
    """Two L-rails on the bracket face (pod frame) whose tongues run in the pod's grooves."""
    y_top = POD_H / 2 - GROOVE_STOP  # the groove's closed end rests on the rail tops
    y_bot = -c.FACE_H / 2
    h = y_top - y_bot
    rails = []
    for s in (-1, 1):
        post = Pos(s * (c.POD_W / 2 + RAIL_CLEAR + RAIL_POST / 2), y_bot + h / 2, -0.01) * Box(
            RAIL_POST, h, GROOVE_Z + GROOVE_W + 0.01, align=CEN_MIN)
        x_t0 = s * (c.POD_W / 2 - GROOVE_DEPTH + RAIL_CLEAR)  # tongue tip, clear of the groove floor
        x_t1 = s * (c.POD_W / 2 + RAIL_CLEAR + 0.01)          # joins the post
        tongue = Pos((x_t0 + x_t1) / 2, y_bot + h / 2, GROOVE_Z + RAIL_CLEAR) * Box(
            abs(x_t1 - x_t0), h, GROOVE_W - 2 * RAIL_CLEAR, align=CEN_MIN)
        rails += [post, tongue]
    return rails


def make_bracket(c):
    z_b = c.Z_C - (c.FACE_H / 2) * cos(c.A)
    z_t = c.Z_C + (c.FACE_H / 2) * cos(c.A)
    reach = c.R_C + c.FACE_H  # generous: trimmed by the face plane
    wedge = Pos(0, 0, z_b) * Box(reach, reach, z_t - z_b, align=(Align.MIN, Align.MIN, Align.MIN))
    wedge -= c.FACE * Box(400, 400, 200, align=CEN_MIN)  # everything in front of the face
    for r in rails_local(c):
        wedge += c.FACE * r
    # Trim the rail ends flush with the flat bottom, so the bracket sits on the bed
    return wedge & (Pos(0, 0, z_b) * Box(reach, reach, z_t - z_b + 20, align=(Align.MIN, Align.MIN, Align.MIN)))


def parts_local(c):
    sm = Pos(0, c.SM_YC, c.SM_Z[0]) * Box(SM_W, SM_L, c.SM_Z[1] - c.SM_Z[0], align=CEN_MIN)
    sm += Pos(0, 0, 0) * usb_receptacle(0, c.USB_Z, c.SM_Y0 - SM_USB_OVERHANG, inward=1)
    ld = Pos(0, c.LD_YC, c.LD_Z1 - c.LD_STACK) * Box(c.LD_W, c.LD_H, c.LD_STACK, align=CEN_MIN)
    wires_z0, wires_z1 = c.SM_Z[1], c.LD_Z1 - c.LD_STACK
    parts = {"radar": ld, "esp32c3": sm}
    if c.kind == "ld2450":
        cw, ch, ct = c.LD_CONN
        parts["radar"] += Pos(c.LD_CONN_X, c.LD_YC, c.LD_Z1 - ct) * Box(cw, ch, ct - c.LD_STACK + 0.01, align=CEN_MIN)
        hw, hh, ht = c.LD_HEADER  # 2 x 4 pin header at the other end (insulator + pins)
        parts["radar"] += Pos(-c.LD_CONN_X, c.LD_YC, c.LD_Z1 - ht) * Box(hw, hh, ht - c.LD_STACK + 0.01, align=CEN_MIN)
    if wires_z1 > wires_z0:  # wiring between the boards stays above the floor
        h = (c.SM_Y0 + SM_L) - c.FLOOR_IN
        parts["wires"] = Pos(0, c.FLOOR_IN + h / 2, wires_z0) * Box(SM_W, h, wires_z1 - wires_z0, align=CEN_MIN)
    return parts


def walls(c):
    """Two thin slabs standing for the room walls (preview only)."""
    h = 110
    return Compound([Pos(-1, 0, -35) * Box(1, 100, h, align=(Align.MIN, Align.MIN, Align.MIN)),
                     Pos(0, -1, -35) * Box(100, 1, h, align=(Align.MIN, Align.MIN, Align.MIN))])


def build(kind: str) -> SimpleNamespace:
    c = config(kind)
    pod_l = pod_local(c)
    return SimpleNamespace(c=c, pod_local=pod_l, pod=c.FACE * pod_l, bracket=make_bracket(c),
                           parts={k: c.FACE * v for k, v in parts_local(c).items()})


def fit_check(a) -> list[str]:
    return interference({"pod": a.pod, "bracket": a.bracket}, a.parts)


def print_poses(a) -> dict:
    bb = a.bracket.bounding_box()
    return {
        "pod": Pos(0, 0, a.c.POD_D) * Rot(180, 0, 0) * a.pod_local,  # window on the bed
        "bracket": Pos(0, 0, -bb.min.Z) * a.bracket,                  # on its flat bottom
    }
