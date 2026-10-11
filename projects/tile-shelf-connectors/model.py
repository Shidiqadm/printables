"""Tile shelf hubs in two styles: plain grooved cube and Art Deco "skyscraper corner".

Spec:    docs/superpowers/specs/2026-10-11-tile-shelf-connectors-design.md
Run:     uv run projects/tile-shelf-connectors/model.py [cube|deco]   (default: both)
Test:    uv run projects/tile-shelf-connectors/test_fit.py
Outputs (print orientation):
  output/thickness_gauge.3mf   comb to find tile thickness without calipers (shared)
  output/cube/  hub, plug, fit_test
  output/deco/  hub, plug, trim, medallion, fit_test   (hub/trim/medallion: body + gold relief)

Files are split by job: core.py = tile channels and grip (shared, tested), cube.py and
deco.py = the outside of each style, this file = parts, assembly preview and export.
"""

import sys
from pathlib import Path
from types import ModuleType

sys.path.insert(0, str(Path(__file__).parent))

from build123d import *  # noqa: E402

import cube  # noqa: E402
import deco  # noqa: E402
from core import (  # noqa: E402
    COLUMN, FRONT, T_SHELF, T_SIDE, X1, ZTOP, hub_body, print_pose, thickness_gauge,
)
from printlib import check, export, preview  # noqa: E402

STYLES: dict[str, ModuleType] = {"cube": cube, "deco": deco}

# Assembly preview only (does not change the hubs; sets the trim length)
TILE_W = 300.0            # top/bottom tile length along the row
TILE_D = 300.0            # shelf depth (tile size front to back)
SIDE_H = 300.0            # side tile height
CUBES = 3
ROWS = 2                  # rows stacked with middle hubs (styles that have them)

PITCH = TILE_W + COLUMN   # hub spacing along the row
TRIM_LEN = deco.trim_half_length(PITCH)

COLORS = {
    "cube": {"body": "#c8642d", "relief": "#c8642d"},     # terracotta, like the reference
    "deco": {"body": "#1d1d1f", "relief": "#c9a227"},     # matte black + silk gold
}
TILE_COLOR = "#ece8df"

Rz, Rx, Ry = Rot(0, 0, 180), Rot(180, 0, 0), Rot(0, 180, 0)
POSES = {"FT": (0.0, None), "BT": (TILE_D, Rz), "FB": (0.0, Ry), "BB": (TILE_D, Rx)}


def fit_test(style: ModuleType) -> Part:
    """Right half of a hub (column + one channel), 10 mm deep: tests both slots."""
    body, ribs = hub_body(style.DIMS, style.silhouette(), depth=10.0)
    keep = Pos(-X1, -FRONT - 1, -100) * Box(style.DIMS.h2 + X1 + 1, 30, 200, align=(Align.MIN,) * 3)
    return (body + ribs) & keep


def assembly(name: str, rows: int | None = None) -> tuple[dict[str, Part], dict[str, Part], dict[str, Part]]:
    """(plastic bodies, relief bodies, tiles) of a CUBES-wide shelf in the shelf frame.

    rows > 1 stacks rows: middle hubs join them and each row's top tile is the next row's
    floor. Styles without a middle hub are always one row.
    """
    style = STYLES[name]
    rows = (ROWS if rows is None else rows) if getattr(style, "HAS_MID", False) else 1
    hb, hr, hrel = style.hub()
    hub_solid = hb + hr
    pl = style.plug()
    pl_left = mirror(pl, about=Plane.YZ)
    z0 = ZTOP + style.CROWN       # bottom tile top face (hub foot below it)
    floors = [z0]                 # top face of each row's floor tile
    for _ in range(rows - 1):
        floors.append(floors[-1] + SIDE_H + T_SHELF)
    zt = floors[-1] + SIDE_H      # top row's side tile top edge
    if rows > 1:
        mb_, mr_, _ = style.mid_hub()
        mid_solid = mb_ + mr_
        mpl = style.mid_plug()
        mpl_left = mirror(mpl, about=Plane.YZ)

    bodies: dict[str, Part] = {}
    relief: dict[str, Part] = {}
    for i in range(CUBES + 1):
        x = i * PITCH
        for tag, (y, rot) in POSES.items():
            z = zt if tag.endswith("T") else z0
            place = Pos(x, y, z) * rot if rot else Pos(x, y, z)
            bodies[f"hub{i}{tag}"] = place * hub_solid
            if hrel is not None:
                relief[f"hub{i}{tag}"] = place * hrel
            if i == 0:
                bodies[f"plug{i}{tag}"] = place * (pl_left if tag in ("FT", "BB") else pl)
            elif i == CUBES:
                bodies[f"plug{i}{tag}"] = place * (pl if tag in ("FT", "BB") else pl_left)
        for r in range(rows - 1):
            z = floors[r] + SIDE_H        # shelf tile between row r and r+1 rests here
            for tag, (y, rot) in (("F", (0.0, None)), ("B", (TILE_D, Rz))):
                place = Pos(x, y, z) * rot if rot else Pos(x, y, z)
                bodies[f"mid{i}{r}{tag}"] = place * mid_solid
                if i == 0:
                    bodies[f"mplug{i}{r}{tag}"] = place * (mpl_left if tag == "F" else mpl)
                elif i == CUBES:
                    bodies[f"mplug{i}{r}{tag}"] = place * (mpl if tag == "F" else mpl_left)

    if style.HAS_TRIMS:
        tb, tr, trel = style.trim(TRIM_LEN)
        mb, mr, mrel = style.medallion()
        pieces = {"trimL": (tb + tr, trel, -1), "medal": (mb + mr, mrel, 0), "trimR": (tb + tr, trel, 1)}
        offset = style.MEDALLION_W / 2 + style.TRIM_GAP + TRIM_LEN / 2
        for c in range(CUBES):
            cx = (c + 0.5) * PITCH
            for pname, (b, r, side) in pieces.items():
                x = cx + side * offset
                for level, place in (("top", Pos(x, 0, zt)), ("bot", Pos(x, 0, z0) * Ry)):
                    bodies[f"{pname}{c}{level}"] = place * b
                    relief[f"{pname}{c}{level}"] = place * r

    tiles: dict[str, Part] = {}
    for c in range(CUBES):
        xl, xr = c * PITCH + X1, (c + 1) * PITCH - X1
        cx, length = (xl + xr) / 2, xr - xl - 0.1        # a hair short so faces don't coincide

        def slab(z: float, align_z: Align) -> Part:
            return Pos(cx, 0, z) * Box(length, TILE_D, T_SHELF, align=(Align.CENTER, Align.MIN, align_z))

        tiles[f"bottom{c}"] = slab(z0, Align.MAX)
        for r in range(rows - 1):
            tiles[f"shelf{c}{r}"] = slab(floors[r] + SIDE_H, Align.MIN)
        tiles[f"top{c}"] = slab(zt, Align.MIN)
        for r, zf in enumerate(floors):
            for side, xs in (("L", xl), ("R", xr - T_SIDE)):
                tiles[f"side{c}{r}{side}"] = Pos(xs, 0, zf) * Box(
                    T_SIDE, TILE_D, SIDE_H, align=(Align.MIN, Align.MIN, Align.MIN))
    return bodies, relief, tiles


def build_parts(name: str) -> dict[str, dict[str, Part]]:
    """Every printable file of one style, as {file: {part: shape}} in print orientation."""
    style = STYLES[name]

    def two_tone(body: Part, relief: Part | None) -> dict[str, Part]:
        return {"body": body} if relief is None else {"body": body, "relief": relief}

    hb, hr, hrel = style.hub()
    files = {
        "hub": print_pose(two_tone(hb + hr, hrel), face_up=style.HUB_FACE_UP),
        "plug": print_pose({"plug": style.plug()}, on_side=True),
        "fit_test": print_pose({"fit_test": fit_test(style)}, face_up=False),
    }
    if getattr(style, "HAS_MID", False):
        mb, mr, _ = style.mid_hub()
        files["mid_hub"] = print_pose({"body": mb + mr}, face_up=style.HUB_FACE_UP)
        files["mid_plug"] = print_pose({"mid_plug": style.mid_plug()}, on_side=True)
    if style.HAS_TRIMS:
        tb, tr, trel = style.trim(TRIM_LEN)
        mb, mr, mrel = style.medallion()
        files["trim"] = print_pose(two_tone(tb + tr, trel), face_up=True)
        files["medallion"] = print_pose(two_tone(mb + mr, mrel), face_up=True)
    return files


def export_style(name: str, out_root: Path) -> None:
    for fname, pieces in build_parts(name).items():
        for pname, p in pieces.items():
            if pname != "relief":          # relief floats on the body's top face by design
                check(p, f"{name}/{fname}/{pname}")
        export(pieces if len(pieces) > 1 else next(iter(pieces.values())), fname,
               out_dir=out_root / name)


def show(name: str) -> None:
    bodies, relief, tiles = assembly(name)
    c = COLORS[name]
    preview(*bodies.values(), *relief.values(), *tiles.values(),
            names=list(bodies) + [f"{k}_relief" for k in relief] + list(tiles),
            colors=[c["body"]] * len(bodies) + [c["relief"]] * len(relief) + [TILE_COLOR] * len(tiles))


if __name__ == "__main__":
    out_root = Path(__file__).parent / "output"
    chosen = [a for a in sys.argv[1:] if a in STYLES] or list(STYLES)
    export(thickness_gauge(), "thickness_gauge", out_dir=out_root)
    for name in chosen:
        export_style(name, out_root)
    print(f"[info] trim length for {TILE_W:g} mm tiles: {TRIM_LEN:.1f} mm")
    show(chosen[-1])
