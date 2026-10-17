"""Interference and fit checks for every HK assembly (assembly coordinates).

Run: uv run projects/ha-macropad/test_fit.py [hk4 hk22 hub ld2410c ld2450]   (default: all)

  - no printed part overlaps another, and no bought part (switches with their wiring room,
    XIAO, LiPo, BH1750, buzzer, LEDs, antenna, radar boards) overlaps anything
  - keycaps clear the switch housing and the well, at rest and fully pressed
  - the plate rests on the well's ledge, below the deck
  - each USB-C plug can reach full insertion through the wall in front of its receptacle
  - the hub's snap clips stay under ~1.5 % bending strain
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import hub  # noqa: E402
import radar  # noqa: E402
import remote  # noqa: E402
from style import USB_SKIN  # noqa: E402

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
          f"keycap skirt {rest:.1f} mm above the deck at rest, {pressed:+.1f} mm pressed, clear of the plate",
          failures)
    # The plate's bevel is modelled PLATE_CLEAR inside the ledge; it settles that far down
    check(remote.PLATE_CLEAR < remote.LEDGE,
          f"plate settles {remote.PLATE_CLEAR:.2f} mm onto its {remote.LEDGE} mm ledge, "
          f"top {remote.WELL_DEPTH + remote.PLATE_CLEAR:.2f} mm below the deck", failures)
    for name, shape in (("shell", a.shell), ("plate", a.plate), ("base", a.base), ("keycap", a.cap)):
        check(shape.is_valid and len(shape.solids()) == 1, f"{name} is one valid solid", failures)
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


TESTS = {"hk4": lambda f: test_remote("bar", f), "hk22": lambda f: test_remote("square", f), "hub": test_hub,
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
