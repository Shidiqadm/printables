"""Export parts next to the calling model script, in <model dir>/output/.

    export(part, "bracket")                          # one body
    export({"body": body, "inlay": text}, "sign")    # multi-body / multi-color (AMS)

Formats:
  3mf  - what you open in Bambu Studio. Dict input becomes one object per key,
         so each body can get its own AMS filament.
  step - exact CAD geometry (for Fusion/FreeCAD/remixing).
  stl  - one per body (for Printables uploads / other slicers).
"""

import inspect
from pathlib import Path

from build123d import Compound, Mesher, Shape, export_step, export_stl

# Mesh resolution: 0.01 mm chord error is far below what a 0.4 nozzle can resolve.
LINEAR_TOL = 0.01
ANGULAR_TOL = 0.2


def _caller_dir() -> Path:
    for frame in inspect.stack()[1:]:
        path = Path(frame.filename).resolve()
        if path.parent != Path(__file__).resolve().parent:
            return path.parent
    return Path.cwd()


def export(
    parts: Shape | dict[str, Shape],
    name: str,
    formats: tuple[str, ...] = ("3mf", "step", "stl"),
    out_dir: str | Path | None = None,
) -> list[Path]:
    bodies = parts if isinstance(parts, dict) else {name: parts}
    out = Path(out_dir) if out_dir else _caller_dir() / "output"
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    if "3mf" in formats:
        mesher = Mesher()
        for label, shape in bodies.items():
            mesher.add_shape(
                shape,
                linear_deflection=LINEAR_TOL,
                angular_deflection=ANGULAR_TOL,
                part_number=label,
            )
        path = out / f"{name}.3mf"
        mesher.write(path)
        written.append(path)

    if "step" in formats:
        labelled = []
        for label, shape in bodies.items():
            shape.label = label
            labelled.append(shape)
        step_obj = labelled[0] if len(labelled) == 1 else Compound(label=name, children=labelled)
        path = out / f"{name}.step"
        export_step(step_obj, path)
        written.append(path)

    if "stl" in formats:
        for label, shape in bodies.items():
            fname = f"{name}.stl" if len(bodies) == 1 else f"{name}-{label}.stl"
            path = out / fname
            export_stl(shape, path, tolerance=LINEAR_TOL, angular_tolerance=ANGULAR_TOL)
            written.append(path)

    for p in written:
        print(f"[export] {p.relative_to(Path.cwd()) if p.is_relative_to(Path.cwd()) else p}")
    return written
