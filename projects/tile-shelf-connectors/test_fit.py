"""Geometric fit tests for the tile shelf hubs, plugs and trims.

Run: uv run projects/tile-shelf-connectors/test_fit.py

1. Slot tests: tile slabs pushed against the solid side of each slot must not overlap the
   part body; they may only overlap the crush ribs, by 0 .. 2*CRUSH depending on thickness.
   Covers both hub channels, the plug, the trim and the medallion.
2. Assembly test: in a full CUBES-wide row, every overlap is a thin crush-rib sliver (never
   a body clash), middle hubs grip 4 tiles, end hubs 2 tiles + a plug, every trim piece
   grips its tile, plugs and relief never touch tiles, and no two parts clash.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from build123d import Align, Box, Pos  # noqa: E402

import deco  # noqa: E402
from core import (  # noqa: E402
    CLEAR, CRUSH, DEPTH, PROTRUDE, T_SHELF, T_SIDE, THICK_TOL, TS, X1,
)
from model import CUBES, TRIM_LEN, assembly  # noqa: E402

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


def slot_case(tag: str, body, ribs, tile, delta: float) -> None:
    vb, _ = overlap(body, tile)
    expect(vb < EPS, f"{tag} vs body: overlap {vb:.4f} mm3")
    vr, dr = overlap(ribs, tile)
    want = CRUSH + delta
    expect(abs(dr - want) < 0.02 or (want <= 0 and vr < EPS),
           f"{tag} crush depth {dr:.3f} (expected {max(want, 0):.2f})")


LONG = 100.0
body, ribs, relief = deco.hub()
tb, tr, _ = deco.trim(TRIM_LEN)
mb, mr, _ = deco.medallion()
print("slots:")
for delta in (-THICK_TOL, 0.0, THICK_TOL):
    t_shelf, t_side = T_SHELF + delta, T_SIDE + delta
    for sign in (1, -1):
        x_top = X1 if sign > 0 else -X1 - LONG
        x_side = X1 if sign > 0 else -X1 - t_side
        top = Pos(x_top, 0, 0) * Box(LONG, DEPTH + 10, t_shelf, align=(Align.MIN,) * 3)
        side = Pos(x_side, 0, 0) * Box(t_side, DEPTH + 10, LONG,
                                       align=(Align.MIN, Align.MIN, Align.MAX))
        side_name = "right" if sign > 0 else "left "
        slot_case(f"t{delta:+.1f} hub {side_name} top ", body, ribs, top, delta)
        slot_case(f"t{delta:+.1f} hub {side_name} side", body, ribs, side, delta)
    edge = Box(400, 40, t_shelf, align=(Align.CENTER, Align.MIN, Align.MIN))   # tile front edge
    slot_case(f"t{delta:+.1f} trim          ", tb, tr, edge, delta)
    slot_case(f"t{delta:+.1f} medallion     ", mb, mr, edge, delta)
expect(CLEAR > THICK_TOL and abs(TS - T_SHELF - CLEAR) < 1e-9, f"slot {TS:.2f} for {T_SHELF}±{THICK_TOL}")

pl = deco.plug()
vb, _ = overlap(body, pl)
expect(vb < EPS, f"plug vs body: overlap {vb:.4f} mm3")
_, dr = overlap(ribs, pl)
expect(abs(dr - CRUSH) < 0.02, f"plug crush depth {dr:.3f} (expected {CRUSH:.2f})")
expect(overlap(relief, body)[0] < 1.0, "hub relief sits on the front face, not inside the body")

print("assembly:")
bodies, gold, tiles = assembly()
others = list(bodies.items())
for pname, p in bodies.items():
    grips = 0
    for oname, o in list(tiles.items()) + [(k, v) for k, v in others if k != pname]:
        if not boxes_touch(p, o):
            continue
        v, d = overlap(p, o)
        if v < EPS:
            continue
        if pname.startswith("plug") and oname in tiles:
            expect(False, f"{pname} touches tile {oname}")
        if oname not in tiles and not (pname.startswith("hub") and oname.startswith("plug")) \
                and not (pname.startswith("plug") and oname.startswith("hub")):
            expect(False, f"{pname} clashes with {oname}")
        if d > PROTRUDE + 0.01:
            expect(False, f"{pname} clashes with {oname}: depth {d:.2f} mm, {v:.1f} mm3")
        grips += 1
    if pname.startswith("hub"):
        i = int(pname[3])
        want = 4 if 0 < i < CUBES else 3          # end hubs: 2 tiles + plug
        expect(grips == want, f"{pname} grips {grips} pieces (expected {want})")
    elif not pname.startswith("plug"):
        expect(grips == 1, f"{pname} grips {grips} tile(s) (expected 1)")
for gname, g in gold.items():
    hits = [t for t, tile in tiles.items() if boxes_touch(g, tile) and overlap(g, tile)[0] > EPS]
    if hits:
        expect(False, f"relief {gname} touches tiles {hits}")
expect(True, f"{len(gold)} relief bodies clear of tiles")

print(f"\n{'ALL PASSED' if not failures else f'{len(failures)} FAILED'}")
sys.exit(1 if failures else 0)
