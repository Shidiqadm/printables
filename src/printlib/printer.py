"""Printer and material constants. Design rules derive from these."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Printer:
    name: str
    bed_x: float
    bed_y: float
    max_z: float
    nozzle: float
    line_width: float
    layer_height: float
    first_layer_height: float
    ams_slots: int

    @property
    def min_wall(self) -> float:
        """Thinnest wall worth modelling: two perimeters."""
        return round(2 * self.line_width, 2)

    def wall(self, perimeters: int) -> float:
        """Wall thickness that is an exact multiple of the extrusion width."""
        return round(perimeters * self.line_width, 2)

    def layers(self, n: int) -> float:
        """Height of n layers (use for floors, tops, text depth)."""
        return round(n * self.layer_height, 2)


@dataclass(frozen=True)
class Material:
    name: str
    density: float  # g/cm^3
    max_overhang_deg: float
    max_bridge_mm: float


# Bambu Lab A1 with AMS lite (4 slots), stock 0.4 mm hardened nozzle.
A1 = Printer(
    name="Bambu Lab A1",
    bed_x=256.0,
    bed_y=256.0,
    max_z=256.0,
    nozzle=0.4,
    line_width=0.42,
    layer_height=0.20,
    first_layer_height=0.20,
    ams_slots=4,
)

PLA = Material(name="PLA", density=1.24, max_overhang_deg=45.0, max_bridge_mm=25.0)
