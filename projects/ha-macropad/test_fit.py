"""Interference and fit checks for every HK assembly (assembly coordinates).

Run: uv run projects/ha-macropad/test_fit.py [keycap hk4 hk22 hub ld2410c ld2450]   (default: all)

  - no printed part overlaps another, and no bought part (switches with their wiring room,
    XIAO, LiPo, BH1750, buzzer, LEDs, antenna, radar boards) overlaps anything
  - keycaps clear the switch housing and the well, at rest and fully pressed, and the deck
    hides the switch housings
  - the keycap socket's crush ribs squeeze the stem arm ends, and the cross fits either way round
  - the plate rests on the well's ledge, below the deck, and its snap beams hold it down
  - the light sensor sits in its snap cradle: it can't drop out or push into the deck
  - each USB-C plug can reach full insertion through the wall in front of its receptacle
  - the hub's snap clips stay under ~1.5 % bending strain
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import hub  # noqa: E402
import keycap  # noqa: E402
import radar  # noqa: E402
import remote  # noqa: E402
from build123d import Align, Box, Pos  # noqa: E402

from style import USB_SKIN, interference  # noqa: E402

PLUG_SHELL = 6.65          # USB-C plug: metal shell in front of the moulded grip (USB-IF spec)
PLUG_MATED = 6.2           # shell depth into the receptacle when fully seated (USB-IF spec)


def check(ok: bool, what: str, failures: list) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {what}")
    if not ok:
        failures.append(what)


def test_remote(kind: str, failures: list) -> None:
    a = remote.build(kind)
    L = a.L
    print(f"{L.name} ({kind}): {L.W:.2f} x {L.D:.2f} x {L.H:.1f} mm")
    clashes = remote.fit_check(a)
    for c in clashes:
        print(f"       clash: {c}")
    check(not clashes, "no interference (parts, switches, keycaps at rest and pressed)", failures)
    rest = L.P + remote.CAP_SEAT - L.H
    pressed = rest - remote.SW_TRAVEL
    check(L.P + remote.CAP_SEAT - remote.SW_TRAVEL > L.P + 1.0,
          f"keycap skirt {rest:+.1f} mm from the deck at rest, {pressed:+.1f} mm pressed, clear of the plate",
          failures)
    floor = remote.BASE - remote.BATT_POCKET
    pocket = Pos(*L.bay_c, 0) * Box(L.bay_pl, L.bay_pw, remote.BASE, align=(Align.CENTER, Align.CENTER, Align.MIN))
    under = a.label & pocket
    check(floor >= 0.8 and not (under and under.solids()),
          f"battery pocket {remote.BATT_POCKET} mm deep, {floor:.1f} mm floor under it, clear of the engraved name",
          failures)
    hidden = L.H - (L.P + remote.SW_ABOVE)
    check(hidden >= 0, f"switch housings {hidden:.1f} mm below the deck: hidden in the well", failures)
    # The plate's bevel is modelled PLATE_CLEAR inside the ledge; it settles that far down
    check(remote.PLATE_CLEAR < remote.LEDGE,
          f"plate settles {remote.PLATE_CLEAR:.2f} mm onto its {remote.LEDGE} mm ledge, "
          f"top {remote.WELL_DEPTH + remote.PLATE_CLEAR:.2f} mm below the deck", failures)
    for name, shape in (("shell", a.shell), ("plate", a.plate), ("base", a.base), ("keycap", a.cap)):
        check(shape.is_valid and len(shape.solids()) == 1, f"{name} is one valid solid", failures)

    # Plate snaps: the barb must reach past the wall, the beam must have room to bend away,
    # the web left between slot and switch hole must print as 2 lines, and a lifted plate
    # must hit the catch.
    reach = remote.SNAP_BARB - remote.PLATE_CLEAR
    web = (remote.WELL_GAP + (remote.CAP - remote.SWITCH_HOLE) / 2 - remote.PLATE_CLEAR
           - remote.SNAP_BEAM - remote.SNAP_SLOT)
    check(0.3 <= reach < remote.SNAP_SLOT - 0.2 and web >= 0.84,
          f"plate snap: barb {reach:.2f} mm past the wall, slot {remote.SNAP_SLOT} mm, web to the switch hole "
          f"{web:.2f} mm", failures)
    strain = remote.plate_snap_strain()
    check(strain <= 0.016, f"plate snap beam strain {strain * 100:.2f} % (PLA: keep under ~1.6 %)", failures)
    lifted = interference({"shell": a.shell, "plate": Pos(0, 0, 0.2) * a.plate}, {})
    check(bool(lifted), "plate lifted 0.2 mm hits the snap catches", failures)

    # BH1750 cradle: the board can't fall out or push up into the deck
    board = remote.bought_parts(L)["bh1750"]
    strain = remote.bh_strain(L)
    check(strain <= 0.016, f"light sensor cradle beam strain {strain * 100:.2f} %", failures)
    held = (interference({"shell": a.shell}, {"bh1750": Pos(0, 0, -0.2) * board})
            and interference({"shell": a.shell}, {"bh1750": Pos(0, 0, 0.2) * board}))
    check(bool(held), "light sensor held: 0.2 mm down hits the lips, 0.2 mm up hits the corner tabs", failures)

    # ADXL345 cradle (HK-22): the same snap cradle, lips on the board's short edges
    if L.adxl:
        board = remote.bought_parts(L)["adxl345"]
        strain = remote.adxl_strain()
        check(strain <= 0.016, f"accelerometer cradle beam strain {strain * 100:.2f} %", failures)
        held = (interference({"shell": a.shell}, {"adxl345": Pos(0, 0, -0.2) * board})
                and interference({"shell": a.shell}, {"adxl345": Pos(0, 0, 0.2) * board}))
        check(bool(held), "accelerometer held: 0.2 mm down hits the lips, 0.2 mm up hits the corner tabs",
              failures)
    check(PLUG_SHELL - USB_SKIN >= PLUG_MATED,
          f"USB-C: receptacle {USB_SKIN} mm inside the port, plug seats {PLUG_SHELL - USB_SKIN:.2f} mm "
          f"(needs {PLUG_MATED})", failures)


def test_hub(failures: list) -> None:
    a = hub.build()
    print(f"hub: {hub.W:.0f} x {hub.D:.0f} x {hub.H:.1f} mm")
    clashes = hub.fit_check(a)
    for c in clashes:
        print(f"       clash: {c}")
    check(not clashes, "no interference", failures)
    check(hub.clip_strain() <= 0.016, f"clip strain {hub.clip_strain() * 100:.2f} % (PLA: keep under ~1.6 %)", failures)
    for name, shape in (("shell", a.shell), ("base", a.base)):
        check(shape.is_valid and len(shape.solids()) == 1, f"{name} is one valid solid", failures)


def test_radar(kind: str, failures: list) -> None:
    a = radar.build(kind)
    c = a.c
    print(f"{kind}: pod {c.POD_W:.1f} x {radar.POD_H:.0f} x {c.POD_D:.1f} mm")
    clashes = radar.fit_check(a)
    for x in clashes:
        print(f"       clash: {x}")
    check(not clashes, "no interference (pod, bracket rails, boards, wiring)", failures)
    skin = radar.POD_WALL - radar.SEAT_DEPTH - radar.SM_USB_OVERHANG
    check(PLUG_SHELL - skin >= PLUG_MATED and radar.SEAT_DEPTH > 0.5,
          f"USB-C: receptacle {skin:.2f} mm inside the floor, board {radar.SEAT_DEPTH:.2f} mm into its channel",
          failures)
    for name, shape in (("pod", a.pod), ("bracket", a.bracket)):
        check(shape.is_valid and len(shape.solids()) == 1, f"{name} is one valid solid", failures)


def free_run(shape, z, along_x, offset=0.0):
    """Length of the empty run through the socket axis at height z, along x or y (offset
    sideways from the axis)."""
    probe = Box(12, 0.02, 0.02) if along_x else Box(0.02, 12, 0.02)
    gap = (Pos(0, offset, z) if along_x else Pos(offset, 0, z)) * probe - shape
    for s in gap.solids():
        bb = s.bounding_box()
        lo, hi = (bb.min.X, bb.max.X) if along_x else (bb.min.Y, bb.max.Y)
        if lo < 0 < hi or (offset and lo < 1.4 < hi):
            return hi - lo
    return 0.0


def test_keycap(failures: list) -> None:
    """The socket takes the cross either way round, and its crush ribs squeeze the arm ends."""
    cap = keycap.make_keycap()
    print("keycap socket")
    mid = (keycap.RIB_START + keycap.RIB_LEAD + keycap.STEM_DEPTH) / 2
    want = keycap.STEM_ARM - 2 * keycap.RIB_GRIP
    for along_x in (True, False):
        arm = "x" if along_x else "y"
        length = free_run(cap, mid, along_x)
        check(abs(length - want) < 0.02,
              f"{arm} arm: ribs leave {length:.2f} mm for the {keycap.STEM_ARM} mm stem arm "
              f"(squeeze {keycap.RIB_GRIP:.2f} mm per end)", failures)
        width = free_run(cap, mid, not along_x, offset=1.4)
        check(abs(width - (keycap.CROSS_W + keycap.STEM_SLOP)) < 0.02,
              f"{arm} arm slot {width:.2f} mm wide, so the cap goes on either way round", failures)
    mouth = free_run(cap, keycap.RIB_START - 0.05, True)
    check(mouth > keycap.STEM_ARM, f"mouth {mouth:.2f} mm long: the stem starts in before it meets the ribs",
          failures)
    check(cap.is_valid and len(cap.solids()) == 1, "keycap is one valid solid", failures)


TESTS = {"keycap": test_keycap, "hk4": lambda f: test_remote("bar", f), "hk22": lambda f: test_remote("square", f),
         "hub": test_hub,
         "ld2410c": lambda f: test_radar("ld2410c", f), "ld2450": lambda f: test_radar("ld2450", f)}


def main() -> int:
    chosen = [a for a in sys.argv[1:] if a in TESTS] or list(TESTS)
    failures: list[str] = []
    for name in chosen:
        TESTS[name](failures)
    print("ALL OK" if not failures else f"{len(failures)} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
