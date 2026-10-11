"""Tile shelf, Art Deco edition: cube hubs, end plugs and cornice trims for a tile shelf.

Spec:    docs/superpowers/specs/2026-10-11-tile-shelf-connectors-design.md
Run:     uv run projects/tile-shelf-connectors/model.py
Test:    uv run projects/tile-shelf-connectors/test_fit.py
Outputs: projects/tile-shelf-connectors/output/   (all in print orientation)
           hub.3mf             universal hub, body + gold relief (2 parts)
           plug.3mf            fills the unused channel of the end hubs
           trim.3mf            cornice clip for a tile front edge, body + gold lines
           medallion.3mf       mid-span keystone clip with sunburst, body + gold relief
           fit_test.3mf        10 mm slice of half a hub, to try on real tiles
           thickness_gauge.3mf comb to find tile thickness without calipers

Files are split by job: core.py = tile channels and grip (tested), deco.py = the Art Deco
outside, this file = parts, assembly preview and export.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from build123d import *  # noqa: E402

import deco  # noqa: E402
from core import (  # noqa: E402
    COLUMN, DEPTH, FRONT, H2, T_SHELF, T_SIDE, X1, hub_body, print_pose, thickness_gauge,
)
from printlib import check, export, preview  # noqa: E402

# Assembly preview only (does not change the hubs; sets the trim length)
TILE_W = 300.0            # top/bottom tile length along the row
TILE_D = 300.0            # shelf depth (tile size front to back)
SIDE_H = 300.0            # side tile height
CUBES = 3
TRIMS = True              # cornice trims + medallions on top and bottom tile edges

PITCH = TILE_W + COLUMN   # hub spacing along the row
TRIM_LEN = deco.trim_half_length(PITCH)

BODY_COLOR, GOLD, TILE_COLOR = "#1d1d1f", "#c9a227", "#ece8df"

Rz, Rx, Ry = Rot(0, 0, 180), Rot(180, 0, 0), Rot(0, 180, 0)
POSES = {"FT": (0.0, None), "BT": (TILE_D, Rz), "FB": (0.0, Ry), "BB": (TILE_D, Rx)}


def fit_test() -> Part:
    """Right half of a plain hub (column + one channel), 10 mm deep: tests both slots."""
    body, ribs = hub_body(deco.silhouette(), depth=10.0)
    keep = Pos(-X1, -FRONT - 1, -100) * Box(H2 + X1 + 1, 30, 200, align=(Align.MIN,) * 3)
    return (body + ribs) & keep


def assembly() -> tuple[dict[str, Part], dict[str, Part], dict[str, Part]]:
    """(plastic bodies, gold relief, tiles) of a CUBES-wide row in the shelf frame."""
    hb, hr, hrel = deco.hub()
    hub_solid = hb + hr
    pl = deco.plug()
    pl_left = mirror(pl, about=Plane.YZ)
    z0 = deco.ZTOP + deco.CROWN   # bottom tile top face (hub foot below it)
    zt = z0 + SIDE_H              # side tile top edge
    bodies: dict[str, Part] = {}
    gold: dict[str, Part] = {}
    for i in range(CUBES + 1):
        x = i * PITCH
        for tag, (y, rot) in POSES.items():
            z = zt if tag.endswith("T") else z0
            place = Pos(x, y, z) * rot if rot else Pos(x, y, z)
            bodies[f"hub{i}{tag}"] = place * hub_solid
            gold[f"hub{i}{tag}"] = place * hrel
            if i == 0:
                bodies[f"plug{i}{tag}"] = place * (pl_left if tag in ("FT", "BB") else pl)
            elif i == CUBES:
                bodies[f"plug{i}{tag}"] = place * (pl if tag in ("FT", "BB") else pl_left)

    if TRIMS:
        tb, tr, trel = deco.trim(TRIM_LEN)
        mb, mr, mrel = deco.medallion()
        pieces = {"trimL": (tb + tr, trel, -1), "medal": (mb + mr, mrel, 0), "trimR": (tb + tr, trel, 1)}
        offset = deco.MEDALLION_W / 2 + deco.TRIM_GAP + TRIM_LEN / 2
        for c in range(CUBES):
            cx = (c + 0.5) * PITCH
            for name, (b, r, side) in pieces.items():
                x = cx + side * offset
                for level, place in (("top", Pos(x, 0, zt)), ("bot", Pos(x, 0, z0) * Ry)):
                    bodies[f"{name}{c}{level}"] = place * b
                    gold[f"{name}{c}{level}"] = place * r

    tiles: dict[str, Part] = {}
    for c in range(CUBES):
        xl, xr = c * PITCH + X1, (c + 1) * PITCH - X1
        cx, length = (xl + xr) / 2, xr - xl - 0.1        # a hair short so faces don't coincide
        tiles[f"top{c}"] = Pos(cx, 0, zt) * Box(length, TILE_D, T_SHELF,
                                               align=(Align.CENTER, Align.MIN, Align.MIN))
        tiles[f"bottom{c}"] = Pos(cx, 0, z0) * Box(length, TILE_D, T_SHELF,
                                                  align=(Align.CENTER, Align.MIN, Align.MAX))
        for name, xs in (("L", xl), ("R", xr - T_SIDE)):
            tiles[f"side{c}{name}"] = Pos(xs, 0, z0) * Box(
                T_SIDE, TILE_D, SIDE_H, align=(Align.MIN, Align.MIN, Align.MIN))
    return bodies, gold, tiles


def build_parts() -> dict[str, dict[str, Part]]:
    """Every printable file, as {file: {part: shape}} in print orientation."""
    hb, hr, hrel = deco.hub()
    tb, tr, trel = deco.trim(TRIM_LEN)
    mb, mr, mrel = deco.medallion()
    return {
        "hub": print_pose({"body": hb + hr, "relief": hrel}, face_up=True),
        "plug": print_pose({"plug": deco.plug()}, face_up=False),
        "trim": print_pose({"body": tb + tr, "relief": trel}, face_up=True),
        "medallion": print_pose({"body": mb + mr, "relief": mrel}, face_up=True),
        "fit_test": print_pose({"fit_test": fit_test()}, face_up=False),
        "thickness_gauge": {"thickness_gauge": thickness_gauge()},
    }


if __name__ == "__main__":
    for fname, pieces in build_parts().items():
        for pname, p in pieces.items():
            if pname != "relief":          # relief floats on the body's top face by design
                check(p, f"{fname}/{pname}")
        export(pieces if len(pieces) > 1 else next(iter(pieces.values())), fname)
    print(f"[info] trim length for {TILE_W:g} mm tiles: {TRIM_LEN:.1f} mm")
    bodies, gold, tiles = assembly()
    preview(*bodies.values(), *gold.values(), *tiles.values(),
            names=[f"{k}" for k in bodies] + [f"{k}_gold" for k in gold] + list(tiles),
            colors=[BODY_COLOR] * len(bodies) + [GOLD] * len(gold) + [TILE_COLOR] * len(tiles))
