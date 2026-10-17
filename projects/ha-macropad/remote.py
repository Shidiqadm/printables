"""HK remote: a battery Home Assistant remote with four MX keys, in two layouts.

  bar     HK-4, 112 x 34 mm desk bar: keys in a row, sensor column on the right
  square  HK-22, 53 x 74 mm handheld: keys in a square, sensor row at the back

Printed parts (per layout):
  shell   unibody: deck with the key well, light window and micro-LED dots; walls with the
          speaker grille and the USB-C port; insert bosses; the light sensor's snap cradle.
          Prints deck-down, no supports.
  plate   1.6 mm switch plate. Drops into the well and rests on its 45 degree ledge, so key
          presses push it onto the shell; two snap beams click it in, so it can't lift when a
          keycap is pulled. Prints top-down.
  base    accent base plate with the XIAO cradle, battery bay, buzzer seat and the name
          engraved underneath. Prints flat.
  keycap  keycap.py (print 4: 3 + 1 accent)

The keys sit in a well: the plate is WELL_DEPTH below the deck, so the deck hides the
switch housings and only a dark gap shows round the caps. Every key has a micro-LED dot
behind it (bar) or beside it (square), for press feedback and scene state.

Frame: x = width (left to right), y = depth (front to back), z = up; origin at the
front-left-bottom corner of the base.
"""

from math import ceil, sqrt
from types import SimpleNamespace

from build123d import (
    Align, Box, Compound, Cone, Cylinder, Location, Plane, Polygon, Pos, RectangleRounded, Rot,
    SlotCenterToCenter, chamfer, extrude, loft,
)

from keycap import CAP, CAP_H, CAP_R, make_keycap
from printlib import A1, fit
from style import (
    BASE, CEN_MIN, CRADLE_LIP, CRADLE_WALL, DECK, HOLE_CHAMFER, LEDGE_W, POCKET_CLEAR, WALL,
    base_plate, body_block, boss, cavity, countersunk_hole, interference, label,
    USB_RECEPT_H, round_hole_top, rounded_rect_loft, usb_pcb_edge, usb_port_cut, usb_receptacle,
)

# ---- Parameters (mm) -------------------------------------------------------
PITCH = 19.05              # standard 1u key spacing
MARGIN = 8.0               # body edge -> keycap edge
MODULE_SPAN = 12.85        # width of the sensor strip (grille, light window, charge dot)

# Key well + drop-in switch plate
WELL_DEPTH = 3.0           # deck top -> plate top
WELL_GAP = 0.8             # keycap edge -> well wall
WELL_EDGE = 0.6            # 45 degree bevel round the well opening
PLATE = A1.layers(8)       # 1.6: MX clips take 1.5 +- 0.1 (1.6 = FR4 plates); 1.5 sliced to 1.4
PLATE_CLEAR = fit("slip", "linear") / 2      # per side, plate in the well
LEDGE = 1.0                # 45 degree ledge the plate rests on (and the plate's bottom bevel)
LEDGE_BELOW = 1.0          # collar continues this far below the ledge
COLLAR = A1.wall(3)        # wall of the collar that carries the ledge
PLATE_TOP_EDGE = 0.3       # plate's bed-side edge
SWITCH_HOLE = 14.0         # fit coupon (2026-10-17): 14.0 holds firmly; 14.1 was loose

# Plate snaps. On two opposite edges a slot cuts a beam free from the plate; the beam carries
# a barb that clicks into a pocket under the well wall, so the plate can't lift. The beam bends
# in the plate's own plane (along the printed lines), and the barb's catch face prints on the
# bed. Square: left and right edges; bar: front and back. The switches' clips face the other
# two edges (README).
SNAP_BEAM = 1.0            # beam width in the plate's plane
SNAP_SLOT = 0.8            # slot that frees the beam; it deflects about 0.5 into it
SNAP_SPAN = 28.0           # slot length between its end centres (free beam ~ SNAP_SPAN + SNAP_SLOT)
SNAP_BARB = 0.6            # barb reach past the plate edge (0.5 past the well wall)
SNAP_BARB_L = 6.0          # barb length along the edge
SNAP_LAND = 0.2            # straight band under the barb's catch face, above its 45 degree lead-in
SNAP_GAP = 0.15            # pocket clearance round the barb

# MX-style switch (Cherry datasheet): housing 5.0 below the plate top, pins 3.3 below
# that; top housing 6.6 above the plate; stem 3.6 above that; 4.0 travel.
SW_BELOW, SW_PINS, WIRE_ROOM = 5.0, 3.3, 1.5
SW_ABOVE, SW_STEM, SW_TRAVEL = 6.6, 3.6, 4.0
SW_FLANGE, SW_FLANGE_H = 15.6, 0.8
SW_TOP_BOTTOM, SW_TOP_TOP = 15.0, 11.5  # top-housing taper (estimate, conservatively wide)
SW_SLIDER_D = 6.0
CAP_SEAT = SW_ABOVE        # the cap's stem post rests on the slider, level with the housing top

# Fasteners
BOSS_INSET = 5.0           # insert bosses (and the 8 mm feet over the screws)

# Seeed XIAO ESP32-C3 (Seeed wiki: 21 x 17.8 mm), USB-C at the back wall
BOARD_L, BOARD_W, BOARD_T = 21.0, 17.8, 1.2
USB_OVERHANG = 1.5         # receptacle past the PCB edge (Seeed's KiCad footprint)
CRADLE_SLACK = 0.5         # extra cradle length: push the board back until its USB-C is in the port
XIAO_GAP = 0.14            # receptacle top -> lowest switch wiring (bar: XIAO under keys 3-4)
BOARD_LEDGE = 1.0          # room for the BAT+/BAT- solder joints underneath
BOARD_PARTS_H = 2.6
# 1S LiPo 502540 (450 mAh): 5.0 x 25 x 40 + tape, swelling and protection-PCB allowance
BATT_T, BATT_W, BATT_L = 5.3, 25.0, 43.0
BAY_WALL, BAY_WALL_H = 1.0, 2.5
# BH1750 light sensor (GY-302 module, header removed), chip up, under the light window
BH_L, BH_W, BH_T = 18.5, 13.9, 1.6
BH_CHIP, BH_CHIP_H = 3.0, 0.75   # BH1750FVI, WSOF6I package
BH_TALL = 1.2              # tallest part on the chip side (regulator)
BH_ROOM = 0.2              # extra room over the tallest part (also puts the cradle on a 0.2 layer line)
BH_CHIP_DX = 0.0           # chip offset from the board centre along its length
LIGHT_WIN_D = 3.0
# BH1750 snap cradle: the board pushes up between two beams that hang from the deck on corner
# posts. Lips on the beams click under its edges and corner tabs stop it on top. The beams
# bend sideways and print as bridges between the posts, so they flex along the printed lines.
BH_BEAM = A1.wall(2)       # 0.84
BH_LIP = 0.4               # how far each lip reaches under the board
BH_LIP_L = 8.0             # lip length along the board
BH_LIP_GAP = 0.05          # lip -> board underside
BH_POST = A1.wall(3)       # post length past the board's end
BH_TAB = 0.6               # corner tab over the board (PCB corners are free of parts)
# Passive buzzer 12 x 8.5 mm ("12085") standing in a seat on the base
BUZ_D, BUZ_H = 12.0, 8.5
BUZ_SEAT_WALL, BUZ_SEAT_H = 0.8, 2.5
BUZ_PIN_POCKET_D, BUZ_PIN_POCKET = 9.0, 1.2  # trimmed pins + solder joints
GRILLE_HOLE, GRILLE_PITCH = 1.2, 2.4          # 19 holes on a hex grid, in the end wall
GRILLE_Z = 6.5                                # grille centre above the base
WIRE_GROOVE_W, WIRE_GROOVE_D = 2.4, 1.0       # base groove: buzzer leads -> XIAO
# Micro LEDs (pre-wired 0603 or 1.8 mm) in light tubes under 1.2 mm dots in the deck
DOT_D = 1.2
LED_BORE = 2.4
LED_TUBE = A1.wall(2)
LED_TUBE_L = 3.0
LED_SMD = (1.6, 0.8, 0.6)
# XIAO's stick-on 2.4 GHz FPC antenna, flat on the inside of a wall, away from the battery
ANT_L, ANT_W, ANT_T = 40.0, 7.5, 0.4   # slim 2.4 GHz FPC with U.FL (Seeed's new one is 40 x 20: too wide)

LAYOUTS = {"bar": ("HK-4", "hk4"), "square": ("HK-22", "hk22")}


# ---- Layout ----------------------------------------------------------------
def layout(kind: str) -> SimpleNamespace:
    """All positions for one layout. Keys are in reading order; the last is the accent key."""
    name, slug = LAYOUTS[kind]
    cols, rows = (4, 1) if kind == "bar" else (2, 2)
    keys_w, keys_d = (cols - 1) * PITCH + CAP, (rows - 1) * PITCH + CAP
    if kind == "bar":
        W, D = MARGIN + keys_w + MARGIN + MODULE_SPAN + MARGIN, 2 * MARGIN + keys_d
    else:
        W, D = 2 * MARGIN + keys_w, MARGIN + keys_d + MARGIN + MODULE_SPAN + MARGIN
    xs = [MARGIN + CAP / 2 + c * PITCH for c in range(cols)]
    ys = [MARGIN + CAP / 2 + r * PITCH for r in range(rows)]
    keys = [(x, y) for y in reversed(ys) for x in xs]

    sw_stack = SW_BELOW + SW_PINS + WIRE_ROOM  # plate top -> lowest switch wiring
    stacks = [BASE + BATT_T + 0.3 + sw_stack + WELL_DEPTH,                       # battery under keys
              BASE + BUZ_H + 0.5 + bh_lip_drop() + BH_T + BH_TALL + BH_ROOM + DECK]  # buzzer under BH1750
    if kind == "bar":                                                            # XIAO under keys
        stacks.append(BASE + BOARD_LEDGE + BOARD_T + USB_RECEPT_H + XIAO_GAP + sw_stack + WELL_DEPTH)
    H = BASE + ceil(round((max(stacks) - BASE) / A1.layer_height, 6)) * A1.layer_height
    H = round(H, 2)
    P = H - WELL_DEPTH  # plate top

    well = SimpleNamespace(x0=MARGIN - WELL_GAP, y0=MARGIN - WELL_GAP,
                           w=keys_w + 2 * WELL_GAP, d=keys_d + 2 * WELL_GAP, r=CAP_R + WELL_GAP)
    well.cx, well.cy = well.x0 + well.w / 2, well.y0 + well.d / 2
    well.seat = P - PLATE  # plate bottom
    well.bottom = well.seat - LEDGE_BELOW

    bay_pw, bay_pl = BATT_W + POCKET_CLEAR, BATT_L + POCKET_CLEAR  # bay: (y, x) inside
    bay_x0 = BOSS_INSET + 3.2 + 0.4  # clear of the corner boss
    buz_off = WALL + BUZ_D / 2 + fit("slip") / 2 + BUZ_SEAT_WALL + 0.4  # buzzer centre from its end wall
    if kind == "bar":
        # Status column right of the keys: light window, charge dot in line with the key dots.
        # Buzzer at the right end, under the BH1750, sounding through a grille in the end wall.
        mx = (MARGIN + keys_w + MARGIN + W - MARGIN) / 2
        buz, grille_side = (W - buz_off, D / 2), 1
        light, bh_rot = (mx, D / 2), False
        dot_y = (well.y0 + well.d + D) / 2
        dots = [(x, dot_y) for x, _ in keys]
        charge = (mx, dot_y)
        board_xc = 68.0
        bay_c = (bay_x0 + BAY_WALL + bay_pl / 2, D / 2)
        ant_top = H - DECK - 0.2
        ant = Pos(board_xc - ANT_L / 2, WALL, ant_top - ANT_W) * Box(ANT_L, ANT_T, ANT_W, align=(Align.MIN, Align.MIN, Align.MIN))
    else:
        # Status row behind the keys: light window and charge dot either side of the middle.
        # Buzzer at the left end of the row, grille in the left wall.
        my = D - MARGIN - MODULE_SPAN / 2
        light, charge, bh_rot = (W / 2 - 6.5, my), (W / 2 + 6.5, my), True
        buz, grille_side = (buz_off, my - 1.0), -1
        side = [well.x0 / 2, (well.x0 + well.w + W) / 2]
        dots = [(side[0] if x < W / 2 else side[1], y) for x, y in keys]
        board_xc = W - 18.5
        bay_c = (W / 2, bay_x0 + BAY_WALL + bay_pw / 2)
        ant_top = H - DECK - LED_TUBE_L - 0.3  # under the right-hand dots' light tubes
        ant_y0 = D - BOSS_INSET - 3.7 - ANT_L  # ends clear of the back boss
        ant = Pos(W - WALL - ANT_T, ant_y0, ant_top - ANT_W) * Box(
            ANT_T, ANT_L, ANT_W, align=(Align.MIN, Align.MIN, Align.MIN))

    p = SimpleNamespace(kind=kind, name=name, slug=slug, W=W, D=D, H=H, P=P, keys=keys,
                        well=well, buz=buz, light=light, dots=dots, charge=charge, bh_rot=bh_rot,
                        grille_side=grille_side,
                        board_xc=board_xc, bay_c=bay_c, bay_pw=bay_pw, bay_pl=bay_pl, ant=ant,
                        sw_stack=sw_stack)
    p.bosses = [(BOSS_INSET, BOSS_INSET), (BOSS_INSET, D - BOSS_INSET),
                (W - BOSS_INSET, BOSS_INSET), (W - BOSS_INSET, D - BOSS_INSET)]
    p.back_in = D - WALL
    p.pcb_y1 = usb_pcb_edge(D, USB_OVERHANG)  # PCB's USB edge
    p.board_z = BASE + BOARD_LEDGE
    p.usb_z = p.board_z + BOARD_T + USB_RECEPT_H / 2
    p.grille = hex_grille(buz[1], BASE + GRILLE_Z)  # (y, z) on the end wall
    # BH1750 board footprint (x, y) and chip offset, long side along x unless rotated
    p.bh_size = (BH_W, BH_L) if bh_rot else (BH_L, BH_W)
    p.bh_c = (light[0], light[1] - BH_CHIP_DX) if bh_rot else (light[0] - BH_CHIP_DX, light[1])
    p.bh_top = H - DECK - BH_TALL - BH_ROOM  # board's chip side
    p.bh_bot = p.bh_top - BH_T
    return p


def hex_grille(cu, cv):
    """19 holes on a hexagonal grid round (cu, cv): a round speaker grille."""
    pts = []
    for j in range(-2, 3):
        for i in range(-2, 3):
            if abs(i + j) <= 2:
                pts.append((cu + (i + j / 2) * GRILLE_PITCH, cv + j * GRILLE_PITCH * sqrt(3) / 2))
    return pts


# ---- Snap fits ---------------------------------------------------------------
# Each snap is modelled once in a local frame (u = outwards, v = along the edge, z = up) and
# placed on both sides by these frames.
def snap_frames(L):
    """Frames on the two well edges that carry the plate snaps, origin on the well wall."""
    w = L.well
    if L.kind == "square":  # left and right edges, beside the key columns
        return [Location((w.x0 + w.w, w.cy, 0)), Location((w.x0, w.cy, 0), (0, 0, 180))]
    return [Location((w.cx, w.y0 + w.d, 0), (0, 0, 90)), Location((w.cx, w.y0, 0), (0, 0, -90))]


def bh_frames(L):
    """Frames on the BH1750's two long edges, origin on the board edge."""
    (bx, by), (sx, sy) = L.bh_c, L.bh_size
    if L.bh_rot:  # long side along y
        return [Location((bx + sx / 2, by, 0)), Location((bx - sx / 2, by, 0), (0, 0, 180))]
    return [Location((bx, by + sy / 2, 0), (0, 0, 90)), Location((bx, by - sy / 2, 0), (0, 0, -90))]


def profile_bar(pts, length):
    """A prism along v from a (u, z) outline (points in either winding)."""
    return extrude(Plane.XZ * Polygon(*pts, align=None), amount=length / 2, both=True)


def plate_snap(L):
    """(material to add, material to cut) for the plate's snap beams, in use position."""
    w, u0 = L.well, -PLATE_CLEAR  # plate edge
    fill_l = SNAP_SPAN + SNAP_SLOT + 1.0
    # The beam gets a square bottom (the plate's 45 degree bevel and the well's ledge are both
    # cut back along it), so it is a full rectangle that the ledge can't push on.
    fill = Pos(u0 - SNAP_BEAM / 2, 0, w.seat) * Box(SNAP_BEAM, fill_l, PLATE - PLATE_TOP_EDGE, align=CEN_MIN)
    zt = L.P  # catch face flush with the plate top: it prints on the bed
    barb = profile_bar([(u0 - 0.3, zt), (u0 + SNAP_BARB, zt), (u0 + SNAP_BARB, zt - SNAP_LAND),
                        (u0 - 0.3, zt - SNAP_LAND - SNAP_BARB - 0.3)], SNAP_BARB_L)
    slot = Pos(u0 - SNAP_BEAM - SNAP_SLOT / 2, 0, w.seat - 0.01) * extrude(
        Rot(0, 0, 90) * SlotCenterToCenter(SNAP_SPAN, SNAP_SLOT), amount=PLATE + 0.02)
    frames = snap_frames(L)
    return Compound([f * (fill + barb) for f in frames]), Compound([f * slot for f in frames])


def shell_snap(L):
    """(material to add, material to cut) in the shell for the plate snaps: a pocket under the
    well wall for each barb (open at the bottom, so it needs no support), a pad behind it so
    the collar stays COLLAR thick, and the ledge cut back along the beam."""
    w = L.well
    deep = SNAP_BARB - PLATE_CLEAR + SNAP_GAP  # pocket depth past the well wall
    pocket_l = SNAP_BARB_L + 2 * SNAP_GAP
    pad = Pos(COLLAR + deep / 2 - 0.005, 0, w.bottom) * Box(deep + 0.01, pocket_l + 2 * COLLAR,
                                                            L.H - DECK - w.bottom + 0.01, align=CEN_MIN)
    pocket = Pos((deep - LEDGE) / 2, 0, w.bottom - 0.01) * Box(deep + LEDGE + 0.01, pocket_l, L.P - w.bottom + 0.01,
                                                               align=CEN_MIN)
    ledge = Pos(-(LEDGE + 0.01) / 2, 0, w.bottom - 0.01) * Box(LEDGE + 0.01, SNAP_SPAN + SNAP_SLOT + 1.6,
                                                      w.seat + LEDGE - w.bottom + 0.02, align=CEN_MIN)
    frames = snap_frames(L)
    return Compound([f * pad for f in frames]), Compound([f * (pocket + ledge) for f in frames])


def plate_snap_strain():
    """Peak bending strain of a plate beam as its barb passes the well wall (fixed-fixed beam,
    centre load)."""
    span = SNAP_SPAN + SNAP_SLOT
    return 12 * (SNAP_BARB - PLATE_CLEAR) * SNAP_BEAM / span ** 2


def bh_lip_drop():
    """How far the cradle reaches below the board."""
    return BH_LIP_GAP + BH_LIP + POCKET_CLEAR / 2


def bh_cradle(L):
    """The BH1750's snap cradle, hanging from the deck."""
    (sx, sy), c = L.bh_size, POCKET_CLEAR / 2
    hl = max(sx, sy) / 2  # half the board's length
    deck_under = L.H - DECK
    z_lip = L.bh_bot - BH_LIP_GAP  # lip top
    z0 = L.bh_bot - bh_lip_drop()
    beam = Pos(c + BH_BEAM / 2, 0, z0) * Box(BH_BEAM, 2 * (hl + c) + 0.02, L.bh_top - z0, align=CEN_MIN)
    lip = profile_bar([(c + BH_BEAM / 2, z_lip), (-BH_LIP, z_lip), (c, z0), (c + BH_BEAM / 2, z0)], BH_LIP_L)
    side = beam + lip
    post_u = (c + BH_BEAM + BH_TAB) / 2 - BH_TAB  # posts reach BH_TAB in past the board edge
    for s in (-1, 1):
        post = Pos(post_u, s * (hl + c + BH_POST / 2), z0) * Box(c + BH_BEAM + BH_TAB, BH_POST,
                                                                  deck_under - z0 + 0.01, align=CEN_MIN)
        tab = Pos(post_u, s * (hl + c - BH_TAB / 2), L.bh_top) * Box(c + BH_BEAM + BH_TAB, BH_TAB + 2 * c,
                                                                      deck_under - L.bh_top + 0.01, align=CEN_MIN)
        side += post + tab
    return Compound([f * side for f in bh_frames(L)])


def bh_strain(L):
    """Peak bending strain of a cradle beam as the board pushes its lip out (fixed-fixed, centre load)."""
    span = max(L.bh_size) + POCKET_CLEAR
    return 12 * (BH_LIP + POCKET_CLEAR / 2) * BH_BEAM / span ** 2


def wall_grille(L):
    """The speaker grille: horizontal holes through the end wall next to the buzzer, with a
    small chamfer on the outside."""
    s = L.grille_side
    x_out = L.W if s > 0 else 0.0
    cut = None
    for y, z in L.grille:
        hole = Pos(x_out - s * (WALL + 0.5), y, z) * Rot(0, 90 * s, 0) * Cylinder(
            GRILLE_HOLE / 2, WALL + 1.0, align=CEN_MIN)
        edge = Pos(x_out - s * HOLE_CHAMFER, y, z) * Rot(0, 90 * s, 0) * Cone(
            GRILLE_HOLE / 2, GRILLE_HOLE / 2 + HOLE_CHAMFER + 0.01, HOLE_CHAMFER + 0.01, align=CEN_MIN)
        cut = hole + edge if cut is None else cut + hole + edge
    return cut


# ---- Shell -----------------------------------------------------------------
def well_outline(L, grow, z0, z1):
    """The well's rounded rectangle grown by `grow`, as a prism from z0 to z1."""
    w = L.well
    return Pos(w.cx, w.cy, z0) * extrude(RectangleRounded(w.w + 2 * grow, w.d + 2 * grow, w.r + grow),
                                         amount=z1 - z0)


def make_shell(L):
    W, D, H, w = L.W, L.D, L.H, L.well
    deck_under = H - DECK
    body = body_block(W, D, H)
    body -= cavity(W, D, BASE - 0.01, deck_under)

    # Collar under the well carries the plate ledge
    body += well_outline(L, COLLAR, w.bottom, deck_under + 0.01)
    for x, y in L.bosses:
        body += boss(x, y, BASE, deck_under + 0.01)
    # Light tubes for the micro LEDs (keep the light in its own dot)
    for x, y in L.dots + [L.charge]:
        tube = Pos(x, y, deck_under - LED_TUBE_L) * Cylinder(LED_BORE / 2 + LED_TUBE, LED_TUBE_L + 0.01,
                                                             align=CEN_MIN)
        body += tube - Pos(x, y, deck_under - LED_TUBE_L - 0.01) * Cylinder(LED_BORE / 2, LED_TUBE_L + 0.02,
                                                                            align=CEN_MIN)
    # BH1750 snap cradle (chip under the window) and the pads behind the plate snap pockets
    body += bh_cradle(L)
    snap_add, snap_cut = shell_snap(L)
    body += snap_add

    # Key well: straight walls, 45 degree ledge, bevelled opening
    body -= well_outline(L, 0, w.seat + LEDGE, H + 1)
    body -= rounded_rect_loft(w.cx, w.cy, w.seat, w.w - 2 * LEDGE, w.d - 2 * LEDGE, w.r - LEDGE,
                              w.seat + LEDGE + 0.001, w.w, w.d, w.r)
    body -= well_outline(L, -LEDGE, w.bottom - 0.01, w.seat + 0.01)
    body -= snap_cut
    body -= rounded_rect_loft(w.cx, w.cy, H - WELL_EDGE, w.w, w.d, w.r,
                              H + 0.01, w.w + 2 * WELL_EDGE + 0.02, w.d + 2 * WELL_EDGE + 0.02, w.r + WELL_EDGE)

    body -= wall_grille(L)
    body -= round_hole_top(*L.light, H, LIGHT_WIN_D, DECK, edge=0.4)
    for x, y in L.dots + [L.charge]:
        body -= round_hole_top(x, y, H, DOT_D, DECK)

    return body - usb_port_cut(L.board_xc, L.usb_z, D, USB_OVERHANG, BOARD_W, L.board_z, BOARD_T)


def make_plate(L):
    """Switch plate in its use position (top at L.P)."""
    w = L.well
    pw, pd, pr = w.w - 2 * PLATE_CLEAR, w.d - 2 * PLATE_CLEAR, w.r - PLATE_CLEAR
    plate = Pos(w.cx, w.cy, w.seat) * extrude(RectangleRounded(pw, pd, pr), amount=PLATE)
    plate = chamfer(plate.edges().group_by()[0], length=LEDGE)
    plate = chamfer(plate.edges().group_by()[-1], length=PLATE_TOP_EDGE)
    snap_add, snap_cut = plate_snap(L)
    plate = plate + snap_add - snap_cut
    for x, y in L.keys:
        hole = Pos(x, y, w.seat - 0.01) * Box(SWITCH_HOLE, SWITCH_HOLE, PLATE + 0.02, align=CEN_MIN)
        edge = loft([Pos(x, y, L.P - PLATE_TOP_EDGE) * RectangleRounded(SWITCH_HOLE, SWITCH_HOLE, 0.01),
                     Pos(x, y, L.P + 0.01) * RectangleRounded(SWITCH_HOLE + 2 * PLATE_TOP_EDGE + 0.02,
                                                              SWITCH_HOLE + 2 * PLATE_TOP_EDGE + 0.02, 0.3)],
                    ruled=True)
        plate -= hole + edge
    return plate


# ---- Base ------------------------------------------------------------------
def cradle(L, wire_notch=8.0):
    """PCB cradle on the base: walls + edge ledge, open at the back wall (USB end)."""
    xc, pw, pl = L.board_xc, BOARD_W + POCKET_CLEAR, BOARD_L + POCKET_CLEAR
    h = BOARD_LEDGE + BOARD_T + CRADLE_LIP
    y0 = L.pcb_y1 - pl - CRADLE_SLACK  # pocket runs from y0 to the PCB's USB edge
    yc = (y0 + L.pcb_y1) / 2
    outer0 = y0 - CRADLE_WALL
    c = Pos(xc, (outer0 + L.back_in) / 2, BASE) * Box(pw + 2 * CRADLE_WALL, L.back_in - outer0, h, align=CEN_MIN)
    y1 = L.back_in + 0.01  # open at the back wall
    c -= Pos(xc, (y0 + y1) / 2, BASE + BOARD_LEDGE) * Box(pw, y1 - y0, h, align=CEN_MIN)
    c -= Pos(xc, (y0 + LEDGE_W + y1) / 2, BASE - 0.01) * Box(pw - 2 * LEDGE_W, y1 - y0 - LEDGE_W, h + 0.02,
                                                            align=CEN_MIN)
    c -= Pos(xc - pw / 2, yc, BASE - 0.01) * Box(2 * CRADLE_WALL + 0.02, wire_notch, BOARD_LEDGE + 0.01,
                                                 align=CEN_MIN)
    return c


def wire_groove(L, extra_h=0.0):
    """Groove in the base top from the buzzer pocket, under the seat ring, to beside the XIAO.
    With extra_h it becomes the keep-out above the groove that the wires need."""
    bx, by = L.buz
    half = (BOARD_W + POCKET_CLEAR) / 2 + CRADLE_WALL + 1.0
    x0, x1 = (L.board_xc + half, bx) if bx > L.board_xc else (bx, L.board_xc - half)
    return Pos((x0 + x1) / 2, by, BASE - WIRE_GROOVE_D) * Box(
        x1 - x0, WIRE_GROOVE_W, WIRE_GROOVE_D + 0.01 + extra_h, align=CEN_MIN)


def make_base(L):
    W, D = L.W, L.D
    lid = base_plate(W, D)
    for x, y in L.bosses:
        lid -= countersunk_hole(x, y, BASE)
    lid += cradle(L)

    bc, pw, pl = L.bay_c, L.bay_pw, L.bay_pl
    bay = Pos(*bc, BASE) * Box(pl + 2 * BAY_WALL, pw + 2 * BAY_WALL, BAY_WALL_H, align=CEN_MIN)
    bay -= Pos(*bc, BASE - 0.01) * Box(pl, pw, BAY_WALL_H + 0.02, align=CEN_MIN)
    bay -= Pos(bc[0] + pl / 2 + BAY_WALL / 2, bc[1], BASE - 0.01) * Box(BAY_WALL + 0.02, 10.0, BAY_WALL_H + 0.02,
                                                                        align=CEN_MIN)  # lead exit
    lid += bay

    seat_r = BUZ_D / 2 + fit("slip") / 2
    seat = Pos(*L.buz, BASE) * Cylinder(seat_r + BUZ_SEAT_WALL, BUZ_SEAT_H, align=CEN_MIN)
    lid += seat - Pos(*L.buz, BASE - 0.01) * Cylinder(seat_r, BUZ_SEAT_H + 0.02, align=CEN_MIN)
    lid -= Pos(*L.buz, BASE - BUZ_PIN_POCKET) * Cylinder(BUZ_PIN_POCKET_D / 2, BUZ_PIN_POCKET + 0.01, align=CEN_MIN)
    lid -= wire_groove(L, extra_h=BUZ_SEAT_H + 0.1)  # also notches the seat ring
    return lid - label(L.name, W / 2, D / 2, extra=0.01)


def make_label_inlay(L):
    """The name as its own body, flush in the engraving: give it a contrast filament (AMS)."""
    return label(L.name, L.W / 2, L.D / 2)


def make_dot_inlays(L):
    """Optional clear/white plugs for the LED dots and the light window (AMS, shell colour swap)."""
    plugs = [Pos(x, y, L.H - DECK) * Cylinder(DOT_D / 2, DECK, align=CEN_MIN) for x, y in L.dots + [L.charge]]
    plugs.append(Pos(*L.light, L.H - DECK) * Cylinder(LIGHT_WIN_D / 2, DECK, align=CEN_MIN))
    return Compound(plugs)


# ---- Bought parts (for the fit check and the preview) ------------------------
def mx_switch(x, y, P):
    """MX switch with its plate top at P: (top housing, stem at rest, body + pins, wiring room)."""
    top = Pos(x, y, P) * Box(SW_FLANGE, SW_FLANGE, SW_FLANGE_H, align=CEN_MIN)
    top += loft([Pos(x, y, P + SW_FLANGE_H) * RectangleRounded(SW_TOP_BOTTOM, SW_TOP_BOTTOM, 1.0),
                 Pos(x, y, P + SW_ABOVE) * RectangleRounded(SW_TOP_TOP, SW_TOP_TOP, 1.0)])
    top -= Pos(x, y, P - 0.01) * Cylinder(SW_SLIDER_D / 2, SW_ABOVE + 0.02, align=CEN_MIN)
    stem = (Pos(x, y, P + SW_ABOVE) * Box(4.0, 1.32, SW_STEM, align=CEN_MIN)  # thick / thin arm
            + Pos(x, y, P + SW_ABOVE) * Box(1.1, 4.0, SW_STEM, align=CEN_MIN))
    below = Pos(x, y, P - SW_BELOW) * Box(13.9, 13.9, SW_BELOW - PLATE, align=CEN_MIN)
    z_pins = P - SW_BELOW - SW_PINS
    below += Pos(x, y, z_pins) * Cylinder(2.0, SW_PINS, align=CEN_MIN)
    for dx, dy, d in ((-3.81, 2.54, 1.5), (2.54, 5.08, 1.5), (-5.08, 0, 1.7), (5.08, 0, 1.7)):
        below += Pos(x + dx, y + dy, z_pins) * Cylinder(d / 2, SW_PINS, align=CEN_MIN)
    wiring = Pos(x, y, z_pins - WIRE_ROOM) * Box(13.9, 13.9, SW_PINS + WIRE_ROOM, align=CEN_MIN)
    return top, stem, below, wiring - below


def bought_parts(L):
    parts = {}
    for i, (x, y) in enumerate(L.keys):
        top, _, below, wiring = mx_switch(x, y, L.P)
        parts[f"switch {i + 1} top"] = top
        parts[f"switch {i + 1} body"] = below
        parts[f"switch {i + 1} wiring"] = wiring
    z = L.board_z
    usb_l = 7.5
    y1 = L.pcb_y1
    parts["xiao"] = (Pos(L.board_xc, y1 - BOARD_L / 2, z) * Box(BOARD_W, BOARD_L, BOARD_T, align=CEN_MIN)
                     + Pos(L.board_xc, y1 - BOARD_L / 2 - usb_l / 2, z + BOARD_T) * Box(
                         BOARD_W - 1.0, BOARD_L - usb_l, BOARD_PARTS_H, align=CEN_MIN)
                     + usb_receptacle(L.board_xc, L.usb_z, y1 + USB_OVERHANG))
    parts["lipo"] = Pos(*L.bay_c, BASE) * Box(BATT_L, BATT_W, BATT_T, align=CEN_MIN)
    deck_under = L.H - DECK
    parts["bh1750"] = (Pos(*L.bh_c, L.bh_bot) * Box(*L.bh_size, BH_T, align=CEN_MIN)
                       + Pos(*L.light, L.bh_top) * Box(BH_CHIP, BH_CHIP, BH_CHIP_H, align=CEN_MIN)
                       + Pos(*L.bh_c, L.bh_top) * Box(L.bh_size[0] - 2 * BH_TAB - 0.2, L.bh_size[1] - 2 * BH_TAB - 0.2,
                                                       BH_TALL, align=CEN_MIN))  # parts on the chip side
    parts["buzzer"] = Pos(*L.buz, BASE) * Cylinder(BUZ_D / 2, BUZ_H, align=CEN_MIN)
    for i, (x, y) in enumerate(L.dots + [L.charge]):
        n = f"led {i + 1}" if i < len(L.dots) else "charge led"
        parts[n] = (Pos(x, y, deck_under - LED_SMD[2]) * Box(*LED_SMD, align=CEN_MIN)
                    + Pos(x, y, deck_under - LED_TUBE_L - 2.0) * Cylinder(0.5, LED_TUBE_L + 2.0 - LED_SMD[2],
                                                                          align=CEN_MIN))
    parts["antenna"] = L.ant
    parts["buzzer wires"] = wire_groove(L, extra_h=2.0) - Pos(*L.buz, 0) * Cylinder(BUZ_D / 2 + 0.01, L.H,
                                                                                     align=CEN_MIN)
    return parts


# ---- Assembly ----------------------------------------------------------------
def build(kind: str) -> SimpleNamespace:
    L = layout(kind)
    cap = make_keycap()
    return SimpleNamespace(L=L, shell=make_shell(L), plate=make_plate(L), base=make_base(L),
                           label=make_label_inlay(L), dots=make_dot_inlays(L), cap=cap,
                           caps=[Pos(x, y, L.P + CAP_SEAT) * cap for x, y in L.keys])


def fit_check(a: SimpleNamespace) -> list[str]:
    printed = {"shell": a.shell, "plate": a.plate, "base": a.base}
    for i, (x, y) in enumerate(a.L.keys):
        printed[f"keycap {i + 1} (rest)"] = Pos(x, y, a.L.P + CAP_SEAT) * a.cap
        printed[f"keycap {i + 1} (pressed)"] = Pos(x, y, a.L.P + CAP_SEAT - SW_TRAVEL) * a.cap
    return interference(printed, bought_parts(a.L))


def print_poses(a: SimpleNamespace) -> dict:
    """Every printed part moved to its print orientation, on the bed at z = 0."""
    L = a.L
    # Turned over left-to-right (about y), so the back stays at the back of the bed and a
    # "Back" seam lands on the USB-C wall, not the front.
    flip = Pos(L.W, 0, L.H) * Rot(0, 180, 0)        # deck on the bed
    plate_flip = Pos(L.W, 0, L.P) * Rot(0, 180, 0)  # plate top on the bed
    return {
        "shell": flip * a.shell,
        "shell-ams": {"shell": flip * a.shell, "dots": flip * a.dots},
        "plate": plate_flip * a.plate,
        "base": {"base": a.base, "label": a.label},
        "keycap": Pos(0, 0, CAP_H) * Rot(180, 0, 0) * a.cap,  # top on the bed
    }
