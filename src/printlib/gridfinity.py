"""Gridfinity bins and baseplates (Zack Freedman's spec), built from scratch on build123d.

    from printlib.gridfinity import bin, baseplate
    part = bin(2, 1, 3)                         # 2x1 grid, 3 units (21 mm) tall
    part = bin(3, 2, 6, divisions=(3, 1), magnets=True)
    plate = baseplate(5, 4)

Reference dimensions (mm):
  grid pitch 42, height unit 7, bin footprint = pitch*n - 0.5, outer radius 3.75
  bin foot profile (bottom up):  0.8 @45deg, 1.8 vertical, 2.15 @45deg  (4.75 tall)
  baseplate profile (bottom up): 0.7 @45deg, 1.8 vertical, 2.15 @45deg  (4.65 tall)
  stacking lip (bottom up):      0.7 @45deg, 1.8 vertical, 1.9 @45deg   (4.4 tall)
  magnet pockets 6.5 x 2.4 at +-13 mm from each cell centre
  bin height (u units) = 7*u, measured to the wall top, excluding the stacking lip
"""

import warnings

from build123d import (
    Align,
    Box,
    Cylinder,
    Part,
    Plane,
    Pos,
    RectangleRounded,
    Sketch,
    extrude,
    loft,
)

PITCH = 42.0
UNIT = 7.0
BIN_CLEARANCE = 0.5  # total, so 0.25 per side against the baseplate
R_BIN = 3.75
R_PLATE = 4.0

FOOT_H = 4.75
LIP_H = 4.4
LIP_INSET = 2.6  # how far the lip's narrowest point sits inside the outer wall
PLATE_H = 4.65

MAGNET_OFFSET = 13.0
MAGNET_D = 6.5
MAGNET_DEPTH = 2.4
SCREW_D = 3.0
SCREW_DEPTH = 6.0


def _section(z: float, w: float, h: float, r: float) -> Sketch:
    r = max(min(r, w / 2 - 0.01, h / 2 - 0.01), 0.05)
    return Plane.XY.offset(z) * RectangleRounded(w, h, r)


def _stack(sections: list[tuple[float, float, float, float]]) -> Part:
    """Ruled loft through rounded-rectangle sections given as (z, width, depth, radius)."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Unable to clean")
        return loft([_section(*s) for s in sections], ruled=True)


def _inset(z: float, w: float, h: float, r: float, d: float) -> tuple[float, float, float, float]:
    """Section at height z, shrunk by d on every side (negative d grows it)."""
    return (z, w - 2 * d, h - 2 * d, r - d)


def _cell_centres(gx: int, gy: int) -> list[tuple[float, float]]:
    return [
        ((i - (gx - 1) / 2) * PITCH, (j - (gy - 1) / 2) * PITCH)
        for i in range(gx)
        for j in range(gy)
    ]


def _foot() -> Part:
    top = PITCH - BIN_CLEARANCE
    return _stack(
        [
            _inset(0.0, top, top, R_BIN, 0.8 + 2.15),
            _inset(0.8, top, top, R_BIN, 2.15),
            _inset(0.8 + 1.8, top, top, R_BIN, 2.15),
            _inset(FOOT_H, top, top, R_BIN, 0.0),
        ]
    )


def bin(
    grid_x: int = 1,
    grid_y: int = 1,
    height_units: int = 3,
    *,
    divisions: tuple[int, int] = (1, 1),
    lip: bool = True,
    magnets: bool = False,
    screws: bool = False,
    wall: float = 1.2,
    floor: float = 1.2,
    divider: float = 1.2,
    solid: bool = False,
) -> Part:
    """A Gridfinity bin. `divisions=(nx, ny)` splits the interior into compartments."""
    W = grid_x * PITCH - BIN_CLEARANCE
    D = grid_y * PITCH - BIN_CLEARANCE
    H = height_units * UNIT
    floor_z = FOOT_H + floor
    if H <= floor_z + 1:
        raise ValueError(f"height_units={height_units} too small for floor at {floor_z} mm")

    feet = [Pos(x, y, 0) * _foot() for x, y in _cell_centres(grid_x, grid_y)]
    top_z = H + LIP_H if lip else H
    body = Pos(0, 0, FOOT_H) * extrude(RectangleRounded(W, D, R_BIN), amount=top_z - FOOT_H)
    part = body + feet

    if not solid:
        if lip:
            pocket = _stack(
                [
                    _inset(floor_z, W, D, R_BIN, wall),
                    _inset(H - (LIP_INSET - wall), W, D, R_BIN, wall),  # 45deg support under lip
                    _inset(H, W, D, R_BIN, LIP_INSET),
                    _inset(H + 0.7, W, D, R_BIN, LIP_INSET - 0.7),
                    _inset(H + 0.7 + 1.8, W, D, R_BIN, LIP_INSET - 0.7),
                    _inset(top_z, W, D, R_BIN, 0.0),
                    _inset(top_z + 1.0, W, D, R_BIN, -1.0),
                ]
            )
        else:
            pocket = _stack(
                [
                    _inset(floor_z, W, D, R_BIN, wall),
                    _inset(top_z + 1.0, W, D, R_BIN, wall),
                ]
            )
        part -= pocket

        nx, ny = divisions
        inner_w, inner_d = W - 2 * wall, D - 2 * wall
        div_top = H - (LIP_INSET - wall) if lip else H
        div_h = div_top - floor_z
        for i in range(1, nx):
            x = -inner_w / 2 + i * inner_w / nx
            part += Pos(x, 0, floor_z) * Box(
                divider, inner_d + 0.2, div_h, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
        for j in range(1, ny):
            y = -inner_d / 2 + j * inner_d / ny
            part += Pos(0, y, floor_z) * Box(
                inner_w + 0.2, divider, div_h, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )

    if magnets or screws:
        for cx, cy in _cell_centres(grid_x, grid_y):
            for sx in (-1, 1):
                for sy in (-1, 1):
                    at = Pos(cx + sx * MAGNET_OFFSET, cy + sy * MAGNET_OFFSET, 0)
                    if magnets:
                        part -= at * Cylinder(
                            MAGNET_D / 2, MAGNET_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN)
                        )
                    if screws:
                        part -= at * Cylinder(
                            SCREW_D / 2, SCREW_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN)
                        )
    return part


def baseplate(grid_x: int = 1, grid_y: int = 1) -> Part:
    """Plain (open-bottom) Gridfinity baseplate. Max 6x6 on the A1 bed."""
    W, D = grid_x * PITCH, grid_y * PITCH
    plate = extrude(RectangleRounded(W, D, R_PLATE), amount=PLATE_H)
    cell = _stack(
        [
            _inset(-1.0, PITCH, PITCH, R_PLATE, 0.7 + 2.15),
            _inset(0.0, PITCH, PITCH, R_PLATE, 0.7 + 2.15),
            _inset(0.7, PITCH, PITCH, R_PLATE, 2.15),
            _inset(0.7 + 1.8, PITCH, PITCH, R_PLATE, 2.15),
            _inset(PLATE_H, PITCH, PITCH, R_PLATE, 0.0),
            _inset(PLATE_H + 1.0, PITCH, PITCH, R_PLATE, -1.0),
        ]
    )
    for x, y in _cell_centres(grid_x, grid_y):
        plate -= Pos(x, y, 0) * cell
    return plate
