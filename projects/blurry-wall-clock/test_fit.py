"""Interference checks for the assembled clock (assembly coordinates).

Run: uv run projects/blurry-wall-clock/test_fit.py
"""

import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from build123d import Box, Pos, Rot  # noqa: E402

import model as m  # noqa: E402

TOL = 0.01  # mm3 of overlap counted as touching, not interfering


def overlap(a, b) -> float:
    inter = a & b
    return sum(s.volume for s in inter.solids()) if inter else 0.0


def main() -> int:
    ps = m.parts()
    fails = []

    # Pressing contacts (the ring is meant to preload the window) are reported separately.
    expected = {("window", "ring"), ("bowl", "window"), ("housing", "bowl"), ("housing", "ring")}
    for (na, a), (nb, b) in combinations(ps.items(), 2):
        v = overlap(a, b)
        tag = "ok" if v <= TOL else ("contact" if (na, nb) in expected else "FAIL")
        if v > TOL:
            print(f"{tag:8s} {na} x {nb}: {v:.2f} mm3")
        if tag == "FAIL":
            fails.append((na, nb))

    # Ring twisting from the entry slots (+TRAVEL) to locked (0): lugs run free until the ramp
    # starts to pull them down (the last PRELOAD/RAMP of the travel, plus half a lug).
    free_until = m.TRAVEL_DEG * m.PRELOAD / m.RAMP + m.LUG_W_DEG / 2
    for a in (m.TRAVEL_DEG, 18.0, 10.0, 4.0, 0.0):
        v = overlap(Rot(0, 0, a) * ps["ring"], ps["housing"])
        print(f"ring at +{a:4.1f} deg vs housing: {v:.3f} mm3")
        if a > free_until + 1 and v > TOL:
            fails.append(("ring", f"twist {a}"))

    # Ring must drop straight down through the entry slots: sweep it 6 mm from above.
    for dz in (6.0, 4.0, 2.0):
        v = overlap(Pos(0, 0, dz) * Rot(0, 0, m.TRAVEL_DEG) * ps["ring"], ps["housing"])
        print(f"ring lowered (+{dz} mm) at entry angle vs housing: {v:.3f} mm3")
        if v > TOL:
            fails.append(("ring", f"entry dz {dz}"))

    # Hands sweep a full turn without touching the bowl, each other's disks or the window.
    for ang in range(0, 360, 15):
        hh = [Rot(0, 0, ang) * ps[n] for n in ("hour_disk", "hour_hand")]
        mm = [Rot(0, 0, -ang * 1.7) * ps[n] for n in ("minute_dome", "minute_hand")]
        for p in hh + mm:
            for fixed in ("bowl", "window"):
                if overlap(p, ps[fixed]) > TOL:
                    fails.append(("hands", f"{fixed} at {ang}"))
        for p in hh:
            for q in mm:
                if overlap(p, q) > TOL:
                    fails.append(("hands", f"hour x minute at {ang}"))

    # Movement body fits between the housing floor and the bowl back.
    move = Pos(0, 0, m.FACE_Z) * Box(m.MOVE_W, m.MOVE_W, m.MOVE_D, align=(m.Align.CENTER,) * 2 + (m.Align.MAX,))
    for n in ("housing", "bowl"):
        v = overlap(move, ps[n])
        print(f"movement vs {n}: {v:.2f} mm3")
        if v > TOL:
            fails.append(("movement", n))

    print("FAILURES:" if fails else "all clear", *fails, sep="\n  ")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
