"""Fit tolerances, loaded from tolerances.toml at the repo root.

    fit("slip")              -> diametral clearance for round fits
    fit("snug", "linear")    -> clearance for flat/rectangular fits
    holes("M3").clearance    -> modelled hole Ø for an M3 screw to pass
    holes("M3").insert       -> heat-set insert hole Ø
    magnet().hole_d          -> 6x2 magnet pocket Ø
"""

import tomllib
from functools import cache
from pathlib import Path
from types import SimpleNamespace

TOML_PATH = Path(__file__).resolve().parents[2] / "tolerances.toml"


@cache
def tol() -> dict:
    with TOML_PATH.open("rb") as f:
        return tomllib.load(f)


def fit(kind: str = "slip", axis: str = "round") -> float:
    """Total diametral clearance for a fit class ('press'|'snug'|'slip'|'loose')."""
    return tol()["fit"][axis][kind]


def holes(size: str) -> SimpleNamespace:
    """Hole sizes for a metric fastener, e.g. holes('M3') or holes('M2.5')."""
    return SimpleNamespace(**tol()["holes"][size.replace(".", "_")])


def magnet(size: str = "d6x2") -> SimpleNamespace:
    return SimpleNamespace(**tol()["magnet"][size])
