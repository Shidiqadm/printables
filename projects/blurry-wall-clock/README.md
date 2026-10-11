# Blurry wall clock

**Status:** design  <!-- design | test-print | done -->
**Created:** 2026-10-11

## Purpose

A 212 mm wall clock whose orange hands sit 9-11 mm behind a translucent PLA window, so they
show only as soft, blurred bars. This is our own parametric take on
[Blurry - The Fading Time Wall Clock](https://thangs.com/designer/LayerLoft.Studio/3d-model/Blurry%20-The%20Fading%20Time%20Wall%20Clock-1565141)
by LayerLoft.Studio. It is rebuilt from that listing's photos and assembly video, not from its
(paid) files. Keep it for personal use and don't upload it to Printables as a design of ours.

How it works (same idea as the original):

- The white **bowl** hides everything. The movement bolts to its back, and its centre pocket holds the hour disk.
- The **hour disk** is a white cup on the hour tube. The orange **hour hand** plugs into it with a peg.
- The **minute dome** is a white dome on the minute shaft. The orange **minute hand** slides into a slot in its side.
- White parts on a white bowl disappear behind the frosted **window**. Only the orange bars read, and they start
  about 35 mm from the centre, like in the original.
- The **ring** clamps the window, bowl and housing together with a 3-lug bayonet: drop it in, then turn it clockwise
  about 25 degrees. A ramp in the grooves pulls it tight. No screws or glue.

Files: `model.py` (all parts), `test_fit.py` (interference checks).

## Key dimensions / constraints

| What | Value | Source |
|------|-------|--------|
| Outer size | 212 mm diameter x 48 mm deep | original listing |
| Movement | 56 x 56 x 16 mm body, M8 thread, 16 mm shaft | original listing ("Clock Components 16mm, M8"); body size common, **guess** |
| Threaded length | 8 mm from the movement face | supplier listing, **guess** |
| Hour tube tip / minute shaft tip | 12 / 15 mm from the movement face | **guess**: measure with a ruler |
| Hour hand hole | 5.0 mm round | common size; **pick with the hand fit test** |
| Minute hand hole | 3.1 mm round (press-fit type) | common size; **pick with the hand fit test** |
| Bowl centre thickness (clamped by the nut) | 3.0 mm | design (16 mm shafts take panels up to about 5 mm) |
| Window | 1.6 mm, 207 mm diameter | design; thicker = blurrier |
| Hand gap to window | hour 11.0 mm, minute 8.6 mm | model |
| Wall screw | head up to 9 mm, shank up to 4.5 mm | design |

If your movement's shaft heights differ, change `HOUR_TUBE_TIP`, `MINUTE_TIP`, `THREAD_LEN` at the top of
`model.py` and rerun. The hour disk top sits flush with the hour tube tip, and the minute dome sits 0.5 mm
above it.

## Parts and print settings (Bambu Studio)

All files are in `output/`, already in print orientation. No supports are needed. Sliced on the A1 with
0.20 mm Standard, PLA, 15% infill:

| Part | Filament | Time | Grams | Notes |
|------|----------|------|-------|-------|
| `hand_fit_test` | any | 10 min | 4 | **print first** |
| `housing` | color (teal/lavender/mint) | 2h49 | 113 | back on the bed |
| `ring` | same color | 0h51 | 40 | front face on the bed |
| `bowl` | white | 3h27 | 144 | flat back on the bed |
| `hour_disk` | white (same spool as bowl) | 0h20 | 16 | face down |
| `minute_dome` | white | 0h20 | 11 | |
| `window` | translucent / natural PLA | 1h02 | 67 | see below |
| `hour_hand`, `minute_hand` | translucent orange | 0h04 | 1 | |
| **Total** | | **about 9h40** | **about 396** | |

Window: for the frosted-glass look, use concentric or Archimedean-chords top and bottom surface patterns and
turn on ironing (top surfaces). A smooth PEI plate gives a glossy front face, and textured PEI gives a grainy one.
Use one solid fill pattern throughout so it diffuses evenly.

Ready-sliced `.gcode.3mf` files are next to the models, sliced with plain defaults (no ironing).

## Assembly

1. Push the hand fit test onto the movement's hour tube and minute shaft. Note which column (1-5 notches)
   grips firmly by hand, then set `HOUR_BORE` / `MINUTE_BORE` (column 3 = the current value, each column = 0.1 mm)
   and rerun `model.py` before printing the hour disk and minute dome.
2. Put the movement on the bowl's back with its hanger loop toward the bowl's key (12 o'clock). Add the
   washer and nut from the front and tighten them.
3. Turn the set knob on the movement's back until both shafts are at "12" (the usual trick is to turn until the
   hour tube just clicks forward). Push the hour disk on with its square hole at 12, then plug in the hour hand's peg.
4. Slide the minute hand into the minute dome's slot and press the dome on with the hand at 12.
5. Set the real time with the knob on the back. You can reach it through the opening in the housing later.
6. Drop the bowl into the housing with its key in the 12 o'clock notch. Lay the window on the bowl rim.
7. Line up the ring's lugs with the three entry slots, press it down and turn it clockwise until it stops.
8. Hang it on one screw through the keyhole (above the centre). To change the battery, take it off the wall
   and use the square opening in the back.

## Notes / risks

- `tolerances.toml` is not calibrated yet, so the bayonet uses generic slip clearances. If the ring is too
  tight to turn, lower `PRELOAD` (currently 0.1 mm). If it rattles, raise it.
- The hour disk (16 g) and minute dome (11 g) are heavier than metal hands, but they are balanced. Each hand
  adds under 1 g of imbalance. If the minute hand lags at "quarter past", print the dome at 10% infill.
- PLA softens around 55 C. Keep the clock out of direct sun.

## Print log

| Date | Version | Result | Change for next |
|------|---------|--------|-----------------|
