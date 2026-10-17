"""HK hub: the ESP-NOW gateway. An ESP32-C3 SuperMini on USB power relays the remote's key
presses to Home Assistant over Wi-Fi. Same design language as the remote.

Printed parts:
  shell  deck with one status dot, walls with 4 clip pockets and the USB-C port, and a
         light tube that carries the board's blue LED (GPIO8) up to the dot. Prints deck-down.
  base   accent bottom plate with the board cradle and 4 snap clips (no screws). Prints flat.
  dot    optional clear/white plug for the dot (AMS colour swap with the shell)
"""

from types import SimpleNamespace

from build123d import Box, Cylinder, Plane, Polygon, Pos, Rot, extrude

from printlib import A1
from style import (
    BASE, CEN_MIN, CRADLE_LIP, CRADLE_WALL, DECK, LEDGE_W, POCKET_CLEAR, WALL,
    USB_RECEPT_H, USB_RECEPT_W, base_plate, body_block, cavity, interference, label, round_hole_top,
    usb_pcb_edge, usb_port_cut, usb_receptacle,
)

# ---- Parameters (mm) -------------------------------------------------------
W, D = 38.0, 32.0
H_MIN = 12.0               # proportion (and clip length); grows if the board needs more
NAME = "HUB"

# ESP32-C3 SuperMini: 22.52 x 18.0 PCB, USB-C on a short edge, BOOT/RST and the LEDs on top
SM_L, SM_W, SM_T = 22.52, 18.0, 1.0
SM_PARTS_H = 1.8           # chip, buttons, LEDs
SM_USB_OVERHANG = 1.0      # receptacle past the PCB edge: not published, measure yours
SM_LEDGE = 1.0
SM_LED_DX, SM_LED_DY = -6.5, 6.0  # blue LED from the PCB centre (x right, y towards USB): measure yours

# Status dot + light tube
DOT_D = 1.2                # same dot as the remote's micro-LED dots
TUBE_ID, TUBE_WALL = 2.6, A1.wall(2)
TUBE_GAP = 0.4             # tube end above the tallest top-side part

# Snap clips: cantilevers on the base that click into pockets in the shell walls
CLIP_W, CLIP_T = 6.0, A1.wall(3)
CLIP_HOOK = 0.3            # how far the hook reaches into the wall
CLIP_HOOK_H = 1.2
CLIP_GAP = 0.1             # clip -> wall inner face
CLIP_TOP_GAP = 0.3         # clip tip -> deck underside
POCKET_EXTRA = 0.2         # pocket clearance round the hook
CLIP_DY = 7.0              # clips at D/2 +- CLIP_DY on the left and right walls

# ---- Derived ---------------------------------------------------------------
BACK_IN = D - WALL
POCKET_W, POCKET_L = SM_W + POCKET_CLEAR, SM_L + POCKET_CLEAR
BOARD_XC = W / 2
PCB_Z = BASE + SM_LEDGE
PCB_Y1 = usb_pcb_edge(D, SM_USB_OVERHANG)  # USB edge of the PCB
PCB_YC = PCB_Y1 - SM_L / 2
USB_Z = PCB_Z + SM_T + USB_RECEPT_H / 2
H = round(max(H_MIN, PCB_Z + SM_T + USB_RECEPT_H + 1.0 + DECK), 1)
DECK_UNDER = H - DECK
LED = (BOARD_XC + SM_LED_DX, PCB_YC + SM_LED_DY)
TUBE_BOTTOM = PCB_Z + SM_T + SM_PARTS_H + TUBE_GAP
CLIP_TIP = DECK_UNDER - CLIP_TOP_GAP
CLIP_L = CLIP_TIP - BASE
CLIPS = [(side, D / 2 + dy) for side in (-1, 1) for dy in (-CLIP_DY, CLIP_DY)]


def clip(side, y):
    """Clip on the left (side=-1) or right (side=+1) wall: beam + hook with a lead-in on top
    and a 45 degree retention face underneath (snaps shut, pulls open with a firm tug)."""
    s = side
    x_out = (W - WALL - CLIP_GAP) if s > 0 else (WALL + CLIP_GAP)
    x_in = x_out - s * CLIP_T
    z0, z1 = BASE - 0.01, CLIP_TIP
    zh = z1 - CLIP_HOOK_H
    pts = [(x_in, z0), (x_out, z0), (x_out, zh), (x_out + s * CLIP_HOOK, zh + CLIP_HOOK),
           (x_out + s * CLIP_HOOK, z1 - 0.6), (x_out, z1), (x_in, z1)]
    if s < 0:
        pts = pts[::-1]  # keep the outline counter-clockwise
    prof = Plane.XZ * Polygon(*pts, align=None)
    return Pos(0, y, 0) * extrude(prof, amount=CLIP_W / 2, both=True)


def clip_pocket(side, y):
    """Pocket in the wall's inner face that the hook clicks into."""
    s = side
    x_face = (W - WALL) if s > 0 else WALL
    depth = CLIP_HOOK + CLIP_GAP + POCKET_EXTRA
    zh = CLIP_TIP - CLIP_HOOK_H
    return Pos(x_face + s * depth / 2, y, zh - 0.05) * Box(depth + 0.02, CLIP_W + 2 * POCKET_EXTRA,
                                                          CLIP_HOOK_H + 0.05 + POCKET_EXTRA, align=CEN_MIN)


def clip_strain():
    """Peak bending strain of a clip when the hook is pushed fully in (cantilever, tip load)."""
    flex_l = CLIP_L - CLIP_HOOK_H / 2
    return 1.5 * CLIP_T * (CLIP_HOOK + CLIP_GAP) / flex_l ** 2


def make_shell():
    body = body_block(W, D, H)
    body -= cavity(W, D, BASE - 0.01, DECK_UNDER)
    for side, y in CLIPS:
        body -= clip_pocket(side, y)
    body -= usb_port_cut(BOARD_XC, USB_Z, D, SM_USB_OVERHANG, SM_W, PCB_Z, SM_T)
    # Status dot + light tube down to just above the blue LED
    tube_l = DECK_UNDER - TUBE_BOTTOM
    tube = Pos(*LED, TUBE_BOTTOM) * Cylinder(TUBE_ID / 2 + TUBE_WALL, tube_l + 0.01, align=CEN_MIN)
    tube -= Pos(*LED, TUBE_BOTTOM - 0.01) * Cylinder(TUBE_ID / 2, tube_l + 0.02, align=CEN_MIN)
    usb_l = 7.5  # keep the tube clear of the USB receptacle, wherever the LED turns out to be
    tube -= Pos(BOARD_XC, PCB_Y1 + SM_USB_OVERHANG - usb_l / 2, PCB_Z + SM_T) * Box(
        USB_RECEPT_W + 0.4, usb_l + 0.4, USB_RECEPT_H + 0.2, align=CEN_MIN)
    body += tube
    return body - round_hole_top(*LED, H, DOT_D, DECK)


def make_base():
    lid = base_plate(W, D)
    for side, y in CLIPS:
        lid += clip(side, y)
    # Board cradle: walls + edge ledge, open at the USB end
    h = SM_LEDGE + SM_T + CRADLE_LIP
    y0 = PCB_Y1 - POCKET_L
    outer0 = y0 - CRADLE_WALL
    c = Pos(BOARD_XC, (outer0 + BACK_IN) / 2, BASE) * Box(POCKET_W + 2 * CRADLE_WALL, BACK_IN - outer0, h,
                                                         align=CEN_MIN)
    c -= Pos(BOARD_XC, (y0 + BACK_IN) / 2 + 0.01, BASE + SM_LEDGE) * Box(POCKET_W, BACK_IN - y0 + 0.02, h,
                                                                        align=CEN_MIN)
    c -= Pos(BOARD_XC, (y0 + BACK_IN) / 2 + LEDGE_W / 2, BASE - 0.01) * Box(
        POCKET_W - 2 * LEDGE_W, BACK_IN - y0 - LEDGE_W + 0.02, h + 0.02, align=CEN_MIN)
    lid += c
    return lid - label(NAME, W / 2, D / 2, extra=0.01)


def supermini():
    usb_l = 7.5
    pcb = Pos(BOARD_XC, PCB_YC, PCB_Z) * Box(SM_W, SM_L, SM_T, align=CEN_MIN)
    parts_ = Pos(BOARD_XC, PCB_YC - usb_l / 2, PCB_Z + SM_T) * Box(SM_W - 1.0, SM_L - usb_l, SM_PARTS_H,
                                                                     align=CEN_MIN)
    return pcb + parts_ + usb_receptacle(BOARD_XC, USB_Z, PCB_Y1 + SM_USB_OVERHANG)


def build() -> SimpleNamespace:
    lens = Pos(*LED, DECK_UNDER) * Cylinder(DOT_D / 2, DECK, align=CEN_MIN)
    return SimpleNamespace(shell=make_shell(), base=make_base(), label=label(NAME, W / 2, D / 2),
                           dot=lens, board=supermini())


def fit_check(a) -> list[str]:
    return interference({"shell": a.shell, "base": a.base}, {"supermini": a.board})


def print_poses(a) -> dict:
    flip = Pos(0, D, H) * Rot(180, 0, 0)  # deck on the bed
    return {
        "shell": flip * a.shell,
        "shell-ams": {"shell": flip * a.shell, "dot": flip * a.dot},
        "base": {"base": a.base, "label": a.label},
    }
