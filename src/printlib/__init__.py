"""Shared helpers for designing 3D-printable parts with build123d.

Typical model script:

    from build123d import *
    from printlib import A1, fit, holes, export, check, preview

    part = Box(40, 20, 10)
    check(part)
    preview(part)
    export(part, "bracket")
"""

from printlib.printer import A1, PLA, Printer, Material
from printlib.tolerances import fit, holes, magnet, tol
from printlib.check import check
from printlib.export import export
from printlib.viewer import preview

__all__ = [
    "A1",
    "PLA",
    "Printer",
    "Material",
    "fit",
    "holes",
    "magnet",
    "tol",
    "check",
    "export",
    "preview",
]
