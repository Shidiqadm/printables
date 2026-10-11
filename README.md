# printables

Parametric, code-first 3D-printable designs for a Bambu Lab A1 (0.4 mm nozzle, AMS lite, PLA), written in [build123d](https://github.com/gumyr/build123d).

## Quick start

```bash
uv sync                                   # install Python deps
uv run python -m ocp_viewer --port 3939   # optional live 3D viewer
uv run new-project "My part"              # scaffold projects/my-part/
uv run projects/my-part/model.py          # build, check, export
```

Outputs land in `projects/<name>/output/`: `.3mf` for Bambu Studio, `.step` for CAD, `.stl` for sharing.

## Layout

- `projects/`: one folder per design (`model.py` + `README.md`)
- `calibration/`: test prints; start with `tolerance_coupon`
- `src/printlib/`: shared helpers (printer constants, tolerances, checks, export, Gridfinity)
- `tolerances.toml`: measured fit clearances and fastener hole sizes
