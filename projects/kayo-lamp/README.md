# Kayo lamp

**Status:** design  <!-- design | test-print | done -->
**Created:** 2026-10-11

## Purpose

A replica of the Makeyo **KAYO** toyetic desk lamp, for personal use: a tilting "robot head" with two
white eyes on a bent-sheet stand. It was rebuilt from the product photos and the Makeyo assembly video
([product](https://makeyo.fr/products/kayo-3d-printed-toyetic-lamp),
[video](https://www.youtube.com/shorts/DPzgkipscrE)).
**Do not publish or sell these files.** The design belongs to Makeyo.

Our change: a **B22** bayonet holder instead of E14.

## Parts

| Part | Colour | Qty | Print pose | Sliced (0.20 Standard) |
|------|--------|-----|-----------|------------------------|
| `stand` | orange | 1 | foot down | 2h08, 74 g |
| `shell_top` (cover) | orange | 1 | top face down | 2h02, 87 g |
| `shell_bottom` (tray with ears) | orange | 1 | bottom face down | 1h39, 63 g |
| `box` (reflector box, holds the holder) | black | 1 | back wall down | 1h55, 81 g |
| `face_plate` | black | 1 | front face down | 0h19, 12 g |
| `eye` | white | 2 | flange down, X up | 0h07, 4 g each |
| `screw` (white button + M12 shank) | white | 2 | button face down | 0h14, 3 g each |
| `nut` (M12, captive in the ear) | any | 2 | flat | 0h05, 1 g each |

The total is about 9 h and 330 g. No supports are needed: sideways holes and bosses are teardrops, and ledges and pads are chamfered at 45°.

## Bought parts

- B22 lamp holder with a **threaded skirt and shade ring** (barrel about 26 mm, ring about 32 mm). The hole in the box is 29 mm (`HOLDER_HOLE`).
- **B22 G45 LED globe bulb**, 45 mm diameter, at most about 80 mm long, **LED only** (4 to 6 W). A standard A60 bulb does not fit, and incandescent or halogen bulbs will soften PLA.
- 8 x 10 x 2 mm disc magnets.
- 2-core cable with a plug and an in-line switch (fabric cable for the look).

## Key dimensions / constraints

| What | Value | Source |
|------|-------|--------|
| Overall | 177 W x 181 L x 169 H | listing: 180 x 196 x 170 (foot shortened on request) |
| Head | 150 x 65, 184 long on top, R15 corners | photo ratios |
| Shell ends | both shells share one angled front cut (21°, vertical at the shown tilt, top overhangs like a visor) and one angled back cut (23° the other way), open at the back for the cable; the black face plate stays square to the axis, 4 mm behind the lower lip | side photo, render |
| Slit (mouth line) | 3 mm, 38 mm below the head top | side photo |
| Pivot | 59 mm from the top back corner, 89 mm above the table, at the slit | side photo |
| Head tilt shown | 21° (adjustable from -30° to 90° without touching the stand) | side photo, interference check |
| Foot | 10 to 113 mm ahead of the pivot (about 10 mm past the head front) | side photo ~7 to 128, shortened on request |
| Arm top | R22 round tab around the pivot | side photo |
| Eyes | Ø42 at 54 mm pitch | front photo ratios |
| B22 holder hole | 29 mm | holder datasheets (barrel 26, ring 32) |
| Balance | CG 34 mm ahead of the pivot at 21° tilt, so it stays on the foot until about 60° tilt | `balance_report()` estimate |

## Assembly (same order as the video)

1. Glue the magnets: 2 in the cover, 2 in the tray (flush pockets, so they stick out about 0.7 mm), and 4 in the box (deep pockets, top and bottom). Check the polarity so that each shell pulls onto the box.
2. Push a nut into the hex pocket inside each ear of the tray.
3. Put the tray between the stand arms and screw a white button through each arm into its nut. Tighten until the head holds its tilt.
4. Wire the B22 holder (fabric cable, in-line switch, strain relief knot). Pass the threaded skirt through the box's back wall, screw the shade ring on inside, then fit the bulb.
5. Snap the face plate onto the front of the box. Set the box in the front of the tray, where the magnets locate it.
6. Drop the cover on. Its notches clear the ears, and the cable leaves through the open back.
7. Press the two eyes into the face plate.

## Print settings (Bambu Studio)

- Material: PLA (orange, black, white).
- Layer height: 0.20 mm. Walls: 3. Infill: 15% gyroid. The thin sheet parts print nearly solid anyway.
- Supports: none.
- Threads: `THREAD_COMP` = 0.15 mm radial per part. If the screw is tight in the nut, raise it to 0.2.

## Safety

This is a mains-voltage lamp. Use a properly rated B22 holder with an earth or insulated shell and a strain relief on the cable. Use LED bulbs only. Keep the lamp out of hot cars and sunny windows, because PLA softens at about 55 °C. If you are not confident wiring mains, have an electrician do it.

## Print log

| Date | Version | Result | Change for next |
|------|---------|--------|-----------------|
