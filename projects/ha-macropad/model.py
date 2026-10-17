"""HK: a Home Assistant remote for scenes and lights, plus its gateway hub and radar pods.

Run:     uv run projects/ha-macropad/model.py [hk4 hk22 hub ld2410c ld2450 coupon]  (default: all)
Test:    uv run projects/ha-macropad/test_fit.py
Outputs: projects/ha-macropad/output/<part>/  every printed part in print orientation
         (3MF for Bambu Studio, STEP, STL), plus <part>-assembly.step

Files are split by job: style.py = the shared look (body, base, seam, USB-C port, label),
remote.py = the remote in both layouts, keycap.py, hub.py, radar.py (both pods), and this
file = the fit coupon, checks, preview and export.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from build123d import Align, Box, FontStyle, Pos, Text, extrude  # noqa: E402

import hub  # noqa: E402
import radar  # noqa: E402
import remote  # noqa: E402
from keycap import STEM_DEPTH, STEM_SLOP, stem_socket_post  # noqa: E402
from printlib import check, export, preview  # noqa: E402
from style import FONT, label_stroke_ok  # noqa: E402

OUT = Path(__file__).parent / "output"
CEN_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def fit_coupon():
    """One piece: a strip of plate as thick as the real one with three switch-hole sizes,
    and a bar with five stem sockets from loose to tight. Both print the same way up as the
    real parts (plate top and socket mouths on the bed). About 10 minutes to print."""
    holes = [round(remote.SWITCH_HOLE - 0.1, 2), remote.SWITCH_HOLE, round(remote.SWITCH_HOLE + 0.1, 2)]
    pitch = 21.0
    width = pitch * len(holes) + 3
    body = Box(width, 26, remote.PLATE, align=(Align.MIN, Align.MIN, Align.MIN))
    for i, s in enumerate(holes):
        x = 3 + pitch * i + 9
        body -= Pos(x, 11.5, -0.01) * Box(s, s, remote.PLATE + 0.02, align=CEN_MIN)
        txt = Text(f"{s:.1f}", font_size=3.5, font=FONT, font_style=FontStyle.BOLD)
        body -= Pos(x, 23.0, remote.PLATE - 0.6) * extrude(txt, amount=0.61)
    body += Pos(0, 26 - 0.01, 0) * Box(width, 20, 1.2, align=(Align.MIN, Align.MIN, Align.MIN))
    slops = [round(STEM_SLOP + d, 2) for d in (-0.10, -0.05, 0.0, 0.05, 0.10)]
    for i, s in enumerate(slops):
        x = 3 + 6 + i * 12.6
        body += Pos(x, 33, 0) * stem_socket_post(s, STEM_DEPTH + 1.0)
        txt = Text(f"{int(round(s * 100)):02d}", font_size=4.0, font=FONT, font_style=FontStyle.BOLD)
        body -= Pos(x, 41.5, 0.6) * extrude(txt, amount=0.61)
    return body


def export_parts(slug, poses, assembly):
    out = OUT / slug
    for name, shape in poses.items():
        if isinstance(shape, dict):  # main body first; the inlays are meant to be many pieces
            n, s = next(iter(shape.items()))
            check(s, f"{slug} {name}/{n}")
        else:
            check(shape, f"{slug} {name}")
        export(shape, f"{slug}-{name}", out_dir=out)
    export(assembly, f"{slug}-assembly", formats=("step",), out_dir=out)


def run_remote(kind):
    a = remote.build(kind)
    L = a.L
    poses = remote.print_poses(a)
    assembly = {"shell": a.shell, "plate": a.plate, "base": a.base, "label": a.label,
                **{f"keycap {i + 1}": c for i, c in enumerate(a.caps)}}
    export_parts(L.slug, poses, assembly)
    print(f"[info] {L.name}: body {L.W:.2f} x {L.D:.2f} x {L.H:.1f} mm, keys {L.P + remote.CAP_SEAT - L.H:.1f} mm "
          f"above the deck at rest, {L.P + remote.CAP_SEAT - remote.SW_TRAVEL - L.H:+.1f} mm pressed; "
          f"label strokes >= 2 lines: {label_stroke_ok(L.name)}")
    bp = remote.bought_parts(L)
    return [a.shell, a.plate, a.base, *a.caps, *[bp[k] for k in ("xiao", "lipo", "buzzer", "bh1750", "antenna")]], \
        ["shell", "plate", "base", *[f"key {i + 1}" for i in range(len(a.caps))], "xiao", "lipo", "buzzer", "bh1750",
         "antenna"]


def run_hub():
    a = hub.build()
    export_parts("hub", hub.print_poses(a), {"shell": a.shell, "base": a.base, "label": a.label})
    print(f"[info] hub {hub.W:.0f} x {hub.D:.0f} x {hub.H:.1f} mm; status dot at {hub.LED}; "
          f"clip bending strain {hub.clip_strain() * 100:.1f} %")
    return [a.shell, a.base, a.board], ["shell", "base", "supermini"]


def run_radar(kind):
    a = radar.build(kind)
    export_parts(kind, radar.print_poses(a), {"pod": a.pod, "bracket": a.bracket})
    print(f"[info] {kind}: pod {a.c.POD_W:.1f} x {radar.POD_H:.0f} x {a.c.POD_D:.1f} mm, tilt {a.c.TILT:.0f} deg")
    return [a.pod, a.bracket, *a.parts.values(), radar.walls(a.c)], ["pod", "bracket", *a.parts, "walls"]


def run_coupon():
    body = fit_coupon()
    check(body, "fit coupon")
    export(body, "fit-coupon", out_dir=OUT / "coupon")
    return [body], ["fit coupon"]


JOBS = {"hk4": lambda: run_remote("bar"), "hk22": lambda: run_remote("square"), "hub": run_hub,
        "ld2410c": lambda: run_radar("ld2410c"), "ld2450": lambda: run_radar("ld2450"), "coupon": run_coupon}

if __name__ == "__main__":
    chosen = [a for a in sys.argv[1:] if a in JOBS] or list(JOBS)
    shown = [JOBS[job]() for job in chosen]
    objs, names = shown[0]  # preview the first one asked for
    preview(*objs, names=names)
