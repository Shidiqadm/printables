"""Geometric fit tests for the tile shelf connectors.

Run: uv run projects/tile-shelf-connectors/test_fit.py

1. Slot test: a tile slab pushed against the solid side of each slot must not overlap the
   connector body; it may only overlap the crush ribs, by 0 .. 2*CRUSH depending on thickness.
2. Assembly test: in a full CUBES-wide row, every tile/connector overlap must be a thin
   crush-rib sliver (never a body clash), and every connector must touch its tiles.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from build123d import Align, Box, Pos  # noqa: E402

from model import (  # noqa: E402
    CLEAR, CRUSH, DEPTH, PROTRUDE, RIB, T_SHELF, T_SIDE, THICK_TOL, TS, U, XW, assembly, connector,
)

EPS = 1e-3
failures: list[str] = []


def expect(ok: bool, msg: str) -> None:
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        failures.append(msg)


def overlap(a, b) -> tuple[float, float]:
    """(volume, depth) of a ∩ b; depth = smallest bounding-box dimension of the overlap."""
    common = a & b
    vol = common.volume if common else 0.0
    if vol < EPS:
        return 0.0, 0.0
    s = common.bounding_box().size
    return vol, min(s.X, s.Y, s.Z)


LONG = 100.0
for kind in ("middle", "end"):
    body, ribs = connector(kind)
    for delta in (-THICK_TOL, 0.0, THICK_TOL):
        t_shelf, t_side = T_SHELF + delta, T_SIDE + delta
        x0 = RIB / 2 if kind == "middle" else -XW
        # shelf tile resting on the jaw (Z=0), ribs press it down from the cap
        shelf = Pos(x0, 0, 0) * Box(LONG, DEPTH + 10, t_shelf, align=(Align.MIN, Align.MIN, Align.MIN))
        # side tile pushed against the -X jaw, ribs on the +X jaw
        side = Pos(-XW, 0, 0) * Box(t_side, DEPTH + 10, LONG, align=(Align.MIN, Align.MIN, Align.MAX))
        tag = f"{kind:6s} t{delta:+.1f}"
        for name, tile in (("shelf", shelf), ("side", side)):
            vb, _ = overlap(body, tile)
            expect(vb < EPS, f"{tag} {name} tile vs body: overlap {vb:.4f} mm3")
            vr, dr = overlap(ribs, tile)
            want = CRUSH + delta
            expect(abs(dr - want) < 0.02 or (want <= 0 and vr < EPS),
                   f"{tag} {name} tile crush depth {dr:.3f} (expected {max(want, 0):.2f})")
    # sanity: slot and wing sizes
    expect(abs(TS - (T_SHELF + CLEAR)) < 1e-6 and CLEAR > THICK_TOL, f"{kind} shelf slot {TS:.2f} for {T_SHELF}±{THICK_TOL} tile")
    expect(U > 30, f"{kind} wing reach {U:.1f} mm")

print("assembly:")
conns, tiles = assembly()
for cname, c in conns.items():
    touching = 0
    for tname, t in tiles.items():
        if not c.bounding_box().overlaps(t.bounding_box()):
            continue
        v, d = overlap(c, t)
        if v > EPS:
            touching += 1
            if d > PROTRUDE + 0.01:
                expect(False, f"{cname} clashes with {tname}: depth {d:.2f} mm, {v:.1f} mm3")
    expect(touching >= 2, f"{cname} grips {touching} tiles")

print(f"\n{'ALL PASSED' if not failures else f'{len(failures)} FAILED'}")
sys.exit(1 if failures else 0)
