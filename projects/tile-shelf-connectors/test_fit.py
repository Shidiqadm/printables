"""Geometric fit tests for the tile shelf hubs.

Run: uv run projects/tile-shelf-connectors/test_fit.py

1. Slot test: tile slabs pushed against the solid side of each slot (column face, block top)
   must not overlap the hub body; they may only overlap the crush ribs, by 0 .. 2*CRUSH
   depending on thickness. Same for the plug.
2. Assembly test: in a full CUBES-wide row, every overlap must be a thin crush-rib sliver
   (never a body clash), every middle hub grips 4 tiles, every end hub 2 tiles + a plug,
   and plugs never touch tiles.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from build123d import Align, Box, Pos  # noqa: E402

from model import (  # noqa: E402
    CLEAR, CRUSH, CUBES, DEPTH, PROTRUDE, T_SHELF, T_SIDE, THICK_TOL, TS, X1,
    assembly, hub, plug,
)

EPS = 1e-3
failures: list[str] = []


def expect(ok: bool, msg: str) -> None:
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        failures.append(msg)


def overlap(a, b) -> tuple[float, float]:
    """(volume, depth) of a ∩ b; depth = deepest overlap piece, measured as the smallest
    bounding-box dimension of each separate piece."""
    common = a & b
    vol = common.volume if common else 0.0
    if vol < EPS:
        return 0.0, 0.0
    depths = []
    for piece in common.solids():
        s = piece.bounding_box().size
        depths.append(min(s.X, s.Y, s.Z))
    return vol, max(depths)


def boxes_touch(a, b) -> bool:
    ba, bb = a.bounding_box(), b.bounding_box()
    return all(
        getattr(ba.min, k) <= getattr(bb.max, k) + EPS and getattr(bb.min, k) <= getattr(ba.max, k) + EPS
        for k in "XYZ"
    )


LONG = 100.0
body, ribs = hub()
print("slots:")
for delta in (-THICK_TOL, 0.0, THICK_TOL):
    t_shelf, t_side = T_SHELF + delta, T_SIDE + delta
    for sign in (1, -1):
        x_top = X1 if sign > 0 else -X1 - LONG
        x_side = X1 if sign > 0 else -X1 - t_side
        top = Pos(x_top, 0, 0) * Box(LONG, DEPTH + 10, t_shelf, align=(Align.MIN,) * 3)
        side = Pos(x_side, 0, 0) * Box(t_side, DEPTH + 10, LONG,
                                       align=(Align.MIN, Align.MIN, Align.MAX))
        tag = f"t{delta:+.1f} {'right' if sign > 0 else 'left '}"
        for name, tile in (("top ", top), ("side", side)):
            vb, _ = overlap(body, tile)
            expect(vb < EPS, f"{tag} {name} tile vs body: overlap {vb:.4f} mm3")
            vr, dr = overlap(ribs, tile)
            want = CRUSH + delta
            expect(abs(dr - want) < 0.02 or (want <= 0 and vr < EPS),
                   f"{tag} {name} tile crush depth {dr:.3f} (expected {max(want, 0):.2f})")
expect(CLEAR > THICK_TOL and abs(TS - T_SHELF - CLEAR) < 1e-9, f"slot {TS:.2f} for {T_SHELF}±{THICK_TOL}")

pl = plug()
vb, _ = overlap(body, pl)
expect(vb < EPS, f"plug vs body: overlap {vb:.4f} mm3")
_, dr = overlap(ribs, pl)
expect(abs(dr - CRUSH) < 0.02, f"plug crush depth {dr:.3f} (expected {CRUSH:.2f})")

print("assembly:")
parts, tiles = assembly()
for pname, p in parts.items():
    grips = 0
    for oname, o in list(tiles.items()) + [(k, v) for k, v in parts.items() if k != pname]:
        if not boxes_touch(p, o):
            continue
        v, d = overlap(p, o)
        if v < EPS:
            continue
        if pname.startswith("plug") and oname in tiles:
            expect(False, f"{pname} touches tile {oname}")
        if pname.startswith("hub") and oname.startswith("hub"):
            expect(False, f"{pname} clashes with {oname}")
        if d > PROTRUDE + 0.01:
            expect(False, f"{pname} clashes with {oname}: depth {d:.2f} mm, {v:.1f} mm3")
        grips += 1
    if pname.startswith("hub"):
        i = int(pname[3])
        want = 4 if 0 < i < CUBES else 3          # end hubs: 2 tiles + plug
        expect(grips == want, f"{pname} grips {grips} pieces (expected {want})")

print(f"\n{'ALL PASSED' if not failures else f'{len(failures)} FAILED'}")
sys.exit(1 if failures else 0)
