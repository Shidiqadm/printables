"""HK design language, shared by the remote, the hub and the radar pods.

A soft rounded block with a crisp 45 degree chamfer round the top, standing on a thin
accent-colour base plate. The base's top chamfer and the body's bottom chamfer meet in a
V seam, so the base reads as a deliberate stripe. The name is engraved underneath.

Also here: the USB-C port cut (thin skin in front of the receptacle, so the plug seats
fully) and the interference check used by every assembly.
"""

from build123d import (
    Align,
    Axis,
    Box,
    Cone,
    Cylinder,
    FontStyle,
    Location,
    Plane,
    Pos,
    RectangleRounded,
    SlotCenterToCenter,
    Text,
    chamfer,
    extrude,
    fillet,
    loft,
    mirror,
)

from printlib import A1, fit, holes

# ---- Shared parameters (mm) ------------------------------------------------
WALL = A1.wall(4)          # 1.68 = 4 perimeters
DECK = A1.layers(10)       # 2.0 top deck
BASE = A1.layers(10)       # 2.0 base plate = the visible accent stripe
R_CORNER = 5.0             # plan-view corner radius of every body
TOP_CHAMFER = 0.8          # 45 degree edge round the top (on the bed when printing)
SEAM_CHAMFER = 0.5         # body bottom + base top: together they form the V seam
BOTTOM_CHAMFER = 0.6       # base bottom edge on the bed (elephant's foot)
HOLE_CHAMFER = 0.3         # bed-side edge of small holes in the deck

POCKET_CLEAR = fit("slip", "linear")   # 0.2 total round bought boards in cradles
CRADLE_WALL = A1.wall(3)   # 1.26
CRADLE_LIP = 1.2           # cradle wall height above the PCB top
LEDGE_W = 1.0              # PCB edge ledge in a cradle

# M2 heat-set inserts in the body, M2 countersunk screws through the base
INSERT_D = holes("M2").insert          # 3.2
INSERT_DEPTH = 5.0                     # M2 x 3 or x 4 insert (Ruthex M2 is 4 long) + melt room
SCREW_CLEAR = holes("M2").clearance    # 2.4
CSK_D = 4.2                            # M2 countersunk head: 3.8 (ISO 7046) to 4.0 (DIN 7991)
BOSS_R = 3.2                           # 1.6 mm of plastic round the insert hole

# USB-C (USB-IF Type-C spec R1.0): the plug's shell sticks out 6.65 mm in front of its grip
# and is fully seated when it is 6.2 mm into the receptacle, so the receptacle face may sit at
# most 0.45 mm behind the outside of the wall. It goes into the port opening, 0.3 mm short.
USB_SKIN = 0.3             # receptacle face -> outside face of the wall
USB_PORT_W, USB_PORT_H = 9.6, 3.8      # stadium opening round the 8.94 x 3.26 receptacle
USB_RECEPT_W, USB_RECEPT_H = 8.94, 3.26
PCB_EDGE_PARTS = 1.0       # height of small parts on top of a PCB near its USB edge

FONT = "Helvetica Neue"
LABEL_SIZE = 8.0
LABEL_DEPTH = A1.layers(2)  # 0.4
NOZZLE_LINE = A1.line_width

MIN3 = (Align.MIN, Align.MIN, Align.MIN)
CEN_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def rounded_block(w, d, h, r):
    """Box with rounded vertical edges, front-left-bottom corner at the origin."""
    return fillet(Box(w, d, h, align=MIN3).edges().filter_by(Axis.Z), radius=r)


def body_block(w, d, h):
    """The body above the base: rounded block from z = BASE, top chamfer, seam chamfer."""
    body = Pos(0, 0, BASE) * rounded_block(w, d, h - BASE, R_CORNER)
    body = chamfer(body.edges().group_by(Axis.Z)[-1], length=TOP_CHAMFER)
    return chamfer(body.edges().group_by(Axis.Z)[0], length=SEAM_CHAMFER)


def cavity(w, d, z0, z1, wall=WALL):
    """The inside of a body: its outline shrunk by `wall`, from z0 to z1."""
    return Pos(wall, wall, z0) * rounded_block(w - 2 * wall, d - 2 * wall, z1 - z0, R_CORNER - wall)


def base_plate(w, d):
    """The accent base plate, z = 0 .. BASE."""
    lid = rounded_block(w, d, BASE, R_CORNER)
    lid = chamfer(lid.edges().group_by(Axis.Z)[-1], length=SEAM_CHAMFER)
    return chamfer(lid.edges().group_by(Axis.Z)[0], length=BOTTOM_CHAMFER)


def round_hole_top(x, y, z_top, d, depth, edge=HOLE_CHAMFER):
    """Round hole down from a top face at z_top, with a 45 degree chamfer on its top edge
    (that edge is on the bed when the part prints deck-down)."""
    hole = Pos(x, y, z_top - depth - 0.01) * Cylinder(d / 2, depth + 0.02, align=CEN_MIN)
    return hole + Pos(x, y, z_top - edge) * Cone(d / 2, d / 2 + edge + 0.01, edge + 0.01, align=CEN_MIN)


def countersunk_hole(x, y, thickness):
    """M2 clearance hole with a 90 degree countersink opening at the bottom face (z = 0)."""
    hole = Pos(x, y, -0.01) * Cylinder(SCREW_CLEAR / 2, thickness + 0.02, align=CEN_MIN)
    csk_h = (CSK_D - SCREW_CLEAR) / 2
    return hole + Pos(x, y, -0.01) * Cone(CSK_D / 2, SCREW_CLEAR / 2, csk_h + 0.01, align=CEN_MIN)


def boss(x, y, z0, z1):
    """Insert boss from z0 up to z1, insert hole opening at the bottom."""
    b = Pos(x, y, z0) * Cylinder(BOSS_R, z1 - z0, align=CEN_MIN)
    return b - Pos(x, y, z0 - 0.01) * Cylinder(INSERT_D / 2, INSERT_DEPTH + 0.01, align=CEN_MIN)


def usb_pcb_edge(y_out, overhang):
    """Where the PCB's USB edge sits for a wall whose outside face is y = y_out: wherever puts
    the receptacle face USB_SKIN behind the outside (overhang = receptacle past the PCB)."""
    return y_out - USB_SKIN - overhang


def usb_receptacle(xc, z, y_face, inward=-1, length=7.35):
    """USB-C receptacle shell as a solid (stadium section), face at y_face, reaching `length`
    into the device along y (inward = -1: the device is at lower y)."""
    shell = extrude(SlotCenterToCenter(USB_RECEPT_W - USB_RECEPT_H, USB_RECEPT_H), amount=length)
    return Location((xc, y_face, z), (90 if inward < 0 else -90, 0, 0)) * shell


def usb_port_cut(xc, z, y_out, overhang, pcb_w, pcb_z, pcb_t, wall=WALL):
    """Cut for a USB-C port in a back wall whose outside face is the plane y = y_out, for a
    board whose receptacle (centre height z) sticks `overhang` past its PCB. The receptacle
    goes into the stadium opening; if it is short, the PCB end goes into a notch in the wall."""
    port = extrude(SlotCenterToCenter(USB_PORT_W - USB_PORT_H, USB_PORT_H), amount=wall + 2)
    cut = Location((xc, y_out + 1, z), (90, 0, 0)) * port
    y_in, edge = y_out - wall, usb_pcb_edge(y_out, overhang)
    if edge > y_in:
        cut += Pos(xc, y_in - 0.01, pcb_z - 0.1) * Box(pcb_w + POCKET_CLEAR, edge - y_in + 0.11,
                                                       pcb_t + 0.2 + PCB_EDGE_PARTS,
                                                       align=(Align.CENTER, Align.MIN, Align.MIN))
    return cut


def label_sketch(name):
    """Underside name, mirrored so it reads when the device is turned over."""
    return mirror(Text(name, font_size=LABEL_SIZE, font=FONT, font_style=FontStyle.BOLD), about=Plane.YZ)


def label(name, x, y, extra=0.0):
    """The name as a solid from z = -extra to LABEL_DEPTH, centred on (x, y).
    extra > 0 for the engraving cut; extra = 0 for the flush AMS inlay."""
    sketch = label_sketch(name)
    c = sketch.bounding_box().center()  # the font's own origin is a little off the letters' middle
    return Pos(x - c.X, y - c.Y, -extra) * extrude(sketch, amount=LABEL_DEPTH + extra)


def label_stroke_ok(name):
    """True if no stroke or counter is narrower than two nozzle lines: every outline must
    survive an offset of one line width (inwards for strokes, outwards for holes)."""
    for f in label_sketch(name).faces():
        try:
            f.outer_wire().offset_2d(-NOZZLE_LINE)
            for hole in f.inner_wires():
                hole.offset_2d(NOZZLE_LINE)
        except Exception:  # the outline pinched off: something is too thin
            return False
    return True


def rounded_rect_loft(cx, cy, z0, w0, d0, r0, z1, w1, d1, r1):
    """Ruled loft between two rounded rectangles centred on (cx, cy): 45 degree bevels."""
    return loft([Plane.XY.offset(z0) * Pos(cx, cy) * RectangleRounded(w0, d0, r0),
                 Plane.XY.offset(z1) * Pos(cx, cy) * RectangleRounded(w1, d1, r1)], ruled=True)


def interference(printed: dict, bought: dict, tol=0.01) -> list[str]:
    """Printed parts must not overlap each other; no bought part may overlap anything.
    Keys "name (variant)" with the same name (a keycap at rest and pressed) are not
    compared with each other. Returns the clashes as text."""
    clashes = []

    def vol(a, b):
        inter = a & b
        return sum(s.volume for s in inter.solids()) if inter else 0.0

    def report(na, nb, a, b):
        v = vol(a, b)
        if v > tol:
            clashes.append(f"{na} vs {nb}: {v:.2f} mm3")

    pn, bn = list(printed), list(bought)
    for i, a in enumerate(pn):
        for b in pn[i + 1:]:
            if a.split(" (")[0] != b.split(" (")[0]:
                report(a, b, printed[a], printed[b])
    for n in bn:
        for p in pn:
            report(n, p, bought[n], printed[p])
    for i, a in enumerate(bn):
        for b in bn[i + 1:]:
            report(a, b, bought[a], bought[b])
    return clashes
