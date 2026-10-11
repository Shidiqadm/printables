"""Slice models with the installed Bambu Studio (headless) to get real print time and filament.

    uv run slice projects/x/output/part.3mf                       # A1, 0.20mm Standard, PLA Basic
    uv run slice part.3mf --process "0.24mm Draft @BBL A1" --set wall_loops=3 --copies 8

Bambu's system profiles inherit from parent profiles; Bambu Studio's CLI wants complete
ones, so `profile()` flattens the inheritance chain from the app bundle first.
Results come from the sliced project's slice_info (the same numbers the GUI shows).
"""

import argparse
import json
import re
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

APP = Path("/Applications/BambuStudio.app")
BINARY = APP / "Contents/MacOS/BambuStudio"
PROFILES = APP / "Contents/Resources/profiles/BBL"

MACHINE = "Bambu Lab A1 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL A1"
FILAMENT = "Bambu PLA Basic @BBL A1"


def profile(category: str, name: str) -> dict:
    """Fully resolved system profile (category: machine | process | filament)."""
    data = json.loads((PROFILES / category / f"{name}.json").read_text())
    parent = data.pop("inherits", None)
    if parent:
        merged = profile(category, parent)
        merged.update(data)
        data = merged
    return data


def _write_profile(category: str, name: str, overrides: dict, folder: Path) -> Path:
    data = profile(category, name)
    data.update({k: v for k, v in overrides.items()})
    data["name"] = name
    data["from"] = "system"
    data.setdefault("type", category)
    path = folder / f"{category}.json"
    path.write_text(json.dumps(data, indent=1))
    return path


@dataclass
class SliceResult:
    minutes: float
    grams: float
    plates: int
    output: Path

    def __str__(self) -> str:
        h, m = divmod(round(self.minutes), 60)
        return f"{h}h{m:02d}m, {self.grams:.1f} g over {self.plates} plate(s) -> {self.output}"


# Keys the Bambu Studio GUI writes from its device/UI state but the headless CLI leaves empty
# or omits. Without them the GUI rejects the project config ("invalid config, load geometry
# data only"). Values match projects saved by the GUI for an A1 with AMS lite.
GUI_STATE = {
    "extruder_ams_count": ["1#0|4#0", "1#0|4#0"],
    "extruder_nozzle_stats": ["Standard#1"],
    "host_type": "octoprint",
    "printhost_authorization_type": "key",
    "printhost_ssl_ignore_revoke": "0",
}


def _make_gui_loadable(path: Path, process: str, overrides: dict) -> None:
    """Patch the sliced project's settings so the GUI loads them, not just the geometry."""
    with zipfile.ZipFile(path) as z:
        entries = {i.filename: z.read(i.filename) for i in z.infolist()}
    name = "Metadata/project_settings.config"
    cfg = json.loads(entries[name])
    for key, value in GUI_STATE.items():
        if not cfg.get(key):
            cfg[key] = value
    colours = cfg.get("filament_colour", ["#FFFFFF"])
    cfg.setdefault("filament_colour_type", ["0"] * len(colours))
    cfg.setdefault("filament_multi_colour", list(colours))
    # record which process values differ from the system preset, as the GUI does
    system = profile("process", process)
    changed = sorted(k for k, v in overrides.items() if str(system.get(k)) != str(v))
    diff = list(cfg.get("different_settings_to_system", ["", "", ""]))
    if diff:
        diff[0] = ";".join(changed)
        cfg["different_settings_to_system"] = diff
    entries[name] = json.dumps(cfg, indent=4).encode()
    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for fname, data in entries.items():
            z.writestr(fname, data)
    tmp.replace(path)


def slice_model(
    model: Path | list[tuple[Path, int]],
    process: str = PROCESS,
    overrides: dict | None = None,
    copies: int = 1,
    out_dir: Path | None = None,
    arrange: bool = True,
    name: str | None = None,
) -> SliceResult:
    """Slice one model, or a plate of several: model=[(stl, copies), ...].

    Cloning only works for STL inputs; a 3MF is sliced as-is.
    """
    plate = [(Path(model), copies)] if not isinstance(model, list) else [(Path(m), n) for m, n in model]
    plate = [(m.resolve(), n) for m, n in plate]
    first = plate[0][0]
    out_dir = Path(out_dir or first.parent).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    overrides = overrides or {}
    proc_over = {k: v for k, v in overrides.items()}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        machine = _write_profile("machine", MACHINE, {}, tmp)
        proc = _write_profile("process", process, proc_over, tmp)
        fil = _write_profile("filament", FILAMENT, {}, tmp)
        out = out_dir / f"{name or first.stem}.gcode.3mf"
        cmd = [
            str(BINARY),
            "--load-settings", f"{machine};{proc}",
            "--load-filaments", str(fil),
            "--arrange", "1" if arrange else "0",
            "--slice", "0",
            "--outputdir", str(out_dir),
            "--export-3mf", out.name,
        ]
        if any(n > 1 for _, n in plate):
            cmd += ["--clone-objects", ",".join(str(n) for _, n in plate)]
        cmd += [str(m) for m, _ in plate]
        run = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp)  # CLI drops files in cwd
        if run.returncode != 0 or not out.exists():
            tail = "\n".join((run.stdout + run.stderr).splitlines()[-25:])
            raise RuntimeError(f"Bambu Studio slicing failed ({run.returncode}):\n{tail}")
    for stray in [out_dir / "result.json", *out_dir.glob("plate_*.gcode")]:
        stray.unlink(missing_ok=True)        # CLI side files; everything is inside the 3MF
    _make_gui_loadable(out, process, proc_over)
    with zipfile.ZipFile(out) as z:
        info = z.read("Metadata/slice_info.config").decode()
    seconds = sum(float(x) for x in re.findall(r'key="prediction" value="([\d.]+)"', info))
    grams = sum(float(x) for x in re.findall(r'key="weight" value="([\d.]+)"', info))
    plates = len(re.findall(r"<plate>", info))
    return SliceResult(seconds / 60, grams, plates, out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model", type=Path)
    ap.add_argument("--process", default=PROCESS, help=f"process preset (default: {PROCESS})")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="override a process setting, e.g. wall_loops=3 (repeatable)")
    ap.add_argument("--copies", type=int, default=1)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    overrides = dict(s.split("=", 1) for s in args.set)
    print(slice_model(args.model, args.process, overrides, args.copies, args.out))


if __name__ == "__main__":
    main()
