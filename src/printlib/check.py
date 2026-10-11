"""Printability sanity checks. Run on every part before exporting."""

from build123d import Shape

from printlib.printer import A1, PLA, Material, Printer


def check(
    part: Shape,
    name: str = "part",
    printer: Printer = A1,
    material: Material = PLA,
) -> dict:
    """Print a short report and return it. Warns about common problems.

    Mass is the solid (100% infill) upper bound; thin-walled parts print close to it,
    chunky blocks print much lighter. Bambu Studio gives the real number.
    """
    bb = part.bounding_box()
    size = (bb.size.X, bb.size.Y, bb.size.Z)
    volume_cm3 = part.volume / 1000
    solid_g = volume_cm3 * material.density
    solids = part.solids() if hasattr(part, "solids") else []

    warnings = []
    if not part.is_valid:
        warnings.append("shape is NOT valid (bad booleans / self-intersection)")
    if len(solids) == 0:
        warnings.append("no solids found (is this a sketch/face?)")
    elif len(solids) > 1:
        warnings.append(f"{len(solids)} separate solids (intended? use a dict for multi-body export)")
    fits = size[0] <= printer.bed_x and size[1] <= printer.bed_y and size[2] <= printer.max_z
    fits_rot = sorted(size[:2]) <= sorted((printer.bed_x, printer.bed_y))
    if not fits:
        warnings.append(
            f"does not fit {printer.name} build volume "
            f"{printer.bed_x:.0f}x{printer.bed_y:.0f}x{printer.max_z:.0f}"
            + (" (rotate in XY?)" if fits_rot and size[2] <= printer.max_z else "")
        )
    if abs(bb.min.Z) > 1e-3:
        warnings.append(f"bottom is at Z={bb.min.Z:.2f}, not on the bed (Z=0)")

    report = {
        "name": name,
        "valid": part.is_valid,
        "size_mm": tuple(round(s, 2) for s in size),
        "volume_cm3": round(volume_cm3, 2),
        "max_mass_g": round(solid_g, 1),
        "solids": len(solids),
        "warnings": warnings,
    }
    print(
        f"[check] {name}: {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm, "
        f"{volume_cm3:.1f} cm3, <= {solid_g:.0f} g {material.name}, "
        f"{len(solids)} solid(s)"
    )
    for w in warnings:
        print(f"[check]   WARNING: {w}")
    return report
