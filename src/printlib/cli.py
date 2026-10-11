"""Command-line helpers, exposed as `uv run new-project` and `uv run export-all`."""

import datetime
import re
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = Path(__file__).resolve().parent / "templates" / "project"


def new_project() -> None:
    """uv run new-project "Desk cable clip"  -> projects/desk-cable-clip/"""
    if len(sys.argv) < 2:
        sys.exit('usage: uv run new-project "Project title"')
    title = " ".join(sys.argv[1:]).strip()
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    dest = ROOT / "projects" / slug
    if dest.exists():
        sys.exit(f"{dest.relative_to(ROOT)} already exists")
    dest.mkdir(parents=True)
    today = datetime.date.today().isoformat()
    for src in TEMPLATE.iterdir():
        text = src.read_text()
        text = text.replace("__TITLE__", title).replace("__SLUG__", slug).replace("__DATE__", today)
        (dest / src.name).write_text(text)
    print(f"created {dest.relative_to(ROOT)}/  (model.py, README.md)")
    print(f"run:    uv run {dest.relative_to(ROOT)}/model.py")


def export_all() -> None:
    """Re-run every model.py under projects/ and calibration/ (regenerates outputs)."""
    scripts = sorted(ROOT.glob("projects/*/model.py")) + sorted(ROOT.glob("calibration/*/model.py"))
    failed = []
    for script in scripts:
        print(f"== {script.relative_to(ROOT)}")
        try:
            runpy.run_path(str(script), run_name="__main__")
        except Exception as exc:  # keep going, report at the end
            failed.append((script, exc))
            print(f"   FAILED: {exc}")
    if failed:
        sys.exit(f"{len(failed)} model(s) failed")
