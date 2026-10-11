# Tolerance coupon

Finds the real fit clearances for this printer + filament, so every later design fits on the first try.
No calipers needed: you only push pegs into holes.

## Print

1. `uv run calibration/tolerance_coupon/model.py`
2. Open `output/tolerance_coupon.3mf` in Bambu Studio. Say **No** if it asks to load as a single object with multiple parts (keep 3 objects).
3. Settings: PLA, 0.20 mm Standard, 3 walls, 15% infill, no supports, no brim. Print as-is (about 25 minutes).
4. Let it cool fully before testing; warm PLA is soft and the readings will be off.

## Test

The plate has a row of **round** holes and a row of **square** holes. The number above each pair is the extra clearance in hundredths of a mm (`20` = hole is 0.20 mm larger than the peg).

Push the pegs in from the **top** (the side that faced up while printing), straight, without twisting first. For each row, write down:

| Fit | What it feels like | Round row | Square row |
|-----|--------------------|-----------|------------|
| press | Smallest hole the peg goes into at all, needs firm force, stays put | | |
| snug | Goes in by hand with light force, no wobble | | |
| slip | Slides in and turns/moves freely, barely any play | | |
| loose | Drops in, wobbles | | |

Tell Claude the numbers (for example: "round: press 10, snug 15, slip 25, loose 40; square: press 0, snug 10, slip 15, loose 30"). Claude updates `tolerances.toml` and marks it calibrated.

## Optional extras

If you have M3 screws or heat-set inserts, say so: Claude can make a second coupon for screw clearance, self-tapping and insert holes.
