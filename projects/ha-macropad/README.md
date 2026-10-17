# HK — Home Keys

**Status:** test-print (v0.8: clips and print settings after the first HK-22 print)
**Created:** 2026-10-08 · **Redesigned:** 2026-10-16 · **Updated:** 2026-10-17
**Inspiration:** [Hot-Swappable, Multi-Layer Macropad](https://makerworld.com/en/models/2495365-hot-swappable-multi-layer-macropad) by Aaron Broom. We kept the idea of keys sunk into a case with front status lights. We use normal MX switches (Outemu), because Gateron low-profile switches are hard to get in India.

## Purpose

HK is a battery-powered Home Assistant remote for scenes and lights. It has four mechanical keys, with a micro-LED status dot for every key. It sleeps until a key is pressed, sends the press (single, double or long) over ESP-NOW, and goes back to sleep. A gateway on Wi-Fi turns the press into a Home Assistant event, and your automations decide what each key does.

The look is clean, minimal and modern: a soft graphite block with a crisp chamfer round the top and a thin orange base stripe that meets the body in a V seam. The four keys sit in a recessed well, so the switch housings hide below the deck. The top shows only the keys, a row of light dots, the light-sensor window and the charging dot. The speaker grille is on the end wall and the USB-C port is on the back. The screws hide under the rubber feet.

There are two layouts, plus two gateways in the same design language:

| Part | Size (mm) | What |
|------|-----------|------|
| **HK-4** bar | 112 × 34 × 20.4 (+ keys) | Desk bar. One row of keys with a status column on the right. Key 4 (right) is orange. |
| **HK-22** square | 53 × 74 × 20.4 (+ keys) | Handheld. 2 × 2 keys with a status row at the back. Key 4 (front right) is orange. |
| **Hub** | 38 × 32 × 12 | ESP-NOW gateway: an ESP32-C3 SuperMini on USB power. The board's blue LED shows through a single dot. Snap-fit, no screws. |
| **LD2410C pod** | 26.4 × 28 × 12.4 | Corner presence sensor that is also the gateway. HLK-LD2410C + SuperMini sandwich behind a 0.8 mm radar window, on an orange corner bracket. |
| **LD2450 pod** | 48.7 × 28 × 13.6 | The same idea for the HLK-LD2450 tracking radar. |

You need either the hub or one of the radar pods as the gateway, not both.

## Files

Source (one folder, split by job):

| File | What |
|------|------|
| `model.py` | Builds, checks, previews and exports everything: `uv run projects/ha-macropad/model.py [hk4 hk22 hub ld2410c ld2450 coupon]` (default: all) |
| `test_fit.py` | Interference and fit checks for every assembly: `uv run projects/ha-macropad/test_fit.py` (must print ALL OK) |
| `print_plan.py` | Slices ready-to-print plates with the quality settings baked in: `uv run projects/ha-macropad/print_plan.py [hk22 hk4]` |
| `style.py` | Shared look and parts: body, base, V seam, USB-C port, insert bosses, label, interference check |
| `remote.py` | The remote in both layouts: shell, switch plate, base, the plate snaps and light-sensor cradle, and bought-part models for the fit check |
| `keycap.py` | Keycap |
| `hub.py`, `radar.py` | Hub; both radar pods and their bracket |

Output (`output/<part>/`, rebuilt by `model.py`; every part is already in print orientation):

| File | Print | Colour |
|------|-------|--------|
| `hk22/print/1_shell.gcode.3mf`, `2_plate_base…`, `3_keycaps…` | **print these** (from `print_plan.py`) | sliced, with the settings below; same for `hk4/print/` |
| `hk4/hk4-shell.3mf` | 1 | body colour (Graphite / Charcoal matte PLA) |
| `hk4/hk4-shell-ams.3mf` | instead of the above, if you want diffused dots | shell + clear or white "dots" (AMS) |
| `hk4/hk4-plate.3mf` | 1 | body colour, or black so the gaps round the keys look deeper |
| `hk4/hk4-base.3mf` | 1 | orange base + label (white or black on the AMS; same filament if you have no AMS) |
| `hk4/hk4-keycap.3mf` | 4 | 3 × body colour or dark grey, 1 × orange |
| `hk22/…` | same set for the square layout | |
| `hub/hub-shell(-ams).3mf`, `hub/hub-base.3mf` | 1 each | |
| `ld2410c/` or `ld2450/` `-pod.3mf`, `-bracket.3mf` | 1 each | pod in body colour, bracket orange |
| `coupon/fit-coupon.3mf` | 1, first | any |
| `coupon/stem-test.gcode.3mf` | 1, if you already printed the coupon | the coupon's stem half only (10 min) |
| `*-assembly.step` | | for Fusion / FreeCAD |

## Key dimensions

| What | Value | Source |
|------|-------|--------|
| Key spacing / keycap | 19.05 / 18.0 mm | MX standard (ai03 switch spec) |
| Switch plate hole / plate | 14.0 / 1.6 mm | Cherry MX datasheet: 14.00 ±0.05, plate 1.5 ±0.1. 1.6 is 8 whole layers (a 1.5 mm plate slices to 1.4) and the usual FR4 plate thickness |
| Plate snaps | 1.0 mm beam, 0.8 mm slot, 28.8 mm free length; barb 0.5 mm past the well wall | design: 0.72 % bending strain when it clicks in |
| Switch below plate / pins / above / stem / travel | 5.0 / 3.3 / 6.6 / 3.6 / 4.0 mm | Cherry MX datasheet |
| Stem socket | cross 4.1 × 1.32 + 0.10 slop (both arms), 4.0 deep, in a Ø5.5 post with a 0.2 mm chamfered tip | Box stems have one thick arm (Kailh spec 1.32, measured 1.30–1.42) and one thin arm (1.10–1.24); Cherry MX 1.31. Keebtalk / Deskthority measurements; slop set by the fit coupon |
| Switch stem | box stem: the cross stands inside a square rim; the cap's round post goes down inside the rim | the user's Outemu switches (photo, 2026-10-17); box switches take MX caps |
| Key well | plate 3.0 mm below the deck, 0.8 mm gap round the caps | design |
| Keycap height above the deck | 3.6 mm at rest, 0.4 mm below the deck when pressed | design (from the MX numbers) |
| XIAO ESP32-C3 PCB | 21.0 × 17.8 × 1.2 mm | Seeed wiki; thickness community-measured |
| XIAO USB-C past the PCB edge | 1.5 mm | Seeed KiCad footprint (not printed as a number) |
| USB-C receptacle face | 0.3 mm inside the port | USB-IF Type-C spec: the plug shell is 6.65 mm and seats fully at 6.2 mm, so the receptacle face may sit at most 0.45 mm in |
| ESP32-C3 SuperMini PCB | 22.52 × 18.0 mm | vendor drawing |
| SuperMini USB-C past the PCB edge | 1.0 mm | **guess: measure yours** (`SM_USB_OVERHANG` in `hub.py` and `radar.py`) |
| LiPo 502540 | 5.3 × 25 × 43 mm modelled (bay 25.2 × 43.2) | name gives the bare cell; the folded protection board adds 2–3 mm |
| BH1750 module (GY-302) | 18.5 × 13.9 × 1.6 mm; chip 3.0 × 1.6 × 0.75 | seller listing; BH1750FVI datasheet. Chip offset and regulator height are not published |
| Light-sensor cradle | 0.84 mm beams, 0.4 mm lips, 1.4 mm room over the board (1.2 mm tallest part + 0.2) | design: 1.44 % bending strain when the board clicks in |
| Buzzer 12085 | Ø12 × 8.5 mm, pins 6.5 mm apart | CEM-1203(42) datasheet |
| FPC antenna | 40 × 7.5 mm slim type | see note below |
| M2 heat-set insert | 3.2 mm hole, 5 mm deep | Ruthex M2: Ø3.6 × 4 mm, hole 3.1–3.2, ≥1.3 mm wall (bosses have 1.6) |
| M2 countersunk screw | head Ø3.8–4.0, countersink 4.2 | ISO 7046 / DIN 7991 |
| HLK-LD2410C / LD2450 | 22 × 16 / 44 × 15 mm | Hi-Link manuals |
| Radar window | 0.8 mm solid PLA | Hi-Link radome guidance: ≤ 1/8 λ thin, or half-wave thick |

**Antenna:** Seeed's current antenna for the XIAO ESP32-C3 (drawing dated 2024-10-08) is a 40 × 20 mm FPC. It is too wide to stand inside the 20 mm-tall body. The model reserves space for a slim 2.4 GHz FPC antenna with a U.FL (IPEX) plug, about 40 × 7.5 mm, stuck to the inside of the front wall (bar) or the right wall (square). Older XIAO antennas, or a slim one from Robu or Amazon.in, fit there. Measure yours; if it differs, change `ANT_L` / `ANT_W` in `remote.py` and run `test_fit.py`.

**Tolerances:** `tolerances.toml` still holds the uncalibrated defaults. Print `calibration/tolerance_coupon` and this project's `fit-coupon` before the full set.

## What changed in v0.8

The first HK-22 print (2026-10-17) showed three problems. v0.8 fixes them:

- **The plate was loose.** It only rested on its ledge, so it lifted when a keycap was pulled.
  It now clicks in. A slot along two opposite edges frees a 1.0 mm beam in the plate. A barb
  on each beam snaps into a pocket under the well wall. The beam bends in the plate's own
  plane, along the printed lines, so it is strong, and the barb's catch face prints on the
  bed. The pockets are open at the bottom, so the shell still needs no supports.
- **The light sensor was loose.** Nothing held the BH1750 up. It now snaps into a cradle that
  hangs from the deck: two beams on corner posts, with lips that click under the board's long
  edges. Corner tabs stop it on top. The beams print as short bridges between the posts and
  bend sideways, along the printed lines.
- **Gaps in the print.** Every layer of the sliced G-code was compared with the model's
  cross-section. With Bambu's default (classic) walls, small voids were left round the speaker
  grille holes, round the LED dots on the deck face, and in the plate's corners: in these
  places a wall is not a whole number of lines wide. Arachne walls fill them (the shell's
  unfilled area dropped from 46 to 8 mm², and the plate's to nearly zero). `print_plan.py`
  now ships sliced files with Arachne, slow outer walls and a slow first layer (see
  *Print settings*).
- **The keycaps didn't suit the switches.** The Outemu switches have a box stem: the "+"
  stands inside a square rim. The cap's post goes down inside that rim, as an MX cap's does,
  and its tip is now chamfered so a squashed first layer can't stop it. Box stems have one
  arm thicker than 1.17 mm (up to about 1.4), so both slots are now cut for the thick arm.
  The old coupon's stem sockets were wide blocks that the rim kept off the cross. The coupon
  now has real keycap posts, mouth up.
- **The keycaps failed to print.** Their 0.5 mm finger dish meant that, top-down, the middle
  of the top floated off the bed. The top is now flat with a 0.6 mm chamfer, and the caps
  print top-down: the top takes the bed's texture like the deck, and the socket prints
  mouth-up like the fit coupon's posts (stick 10 fit snugly).
- **Smaller fixes:**
  - The plate is now 1.6 mm (8 whole layers); 1.5 mm sliced to 1.4.
  - The shell is turned over left-to-right for printing, so a "Back" seam lands on the USB-C
    wall instead of the front.
  - The light sensor has 0.2 mm more room over its tallest part.
  - The switch holes are 14.0 mm, as the fit coupon showed. They were 14.0 + 0.1 clearance,
    and the switches sat loose in the printed plate.

## What changed in v0.7

The audit of v0.6 found these problems, and v0.7 fixes them:

- **USB-C:** the old port had a 2.2 mm wall in front of the receptacle, so most cables could not seat. The receptacle now sits 0.3 mm inside a stadium-shaped port, and the plug seats a full 6.35 mm. The radar pods' floor port follows the same rule.
- **Switch holes:** they printed on the bed with no chamfer, so the squashed first layer made them tight. The plate is now a separate part with chamfered bed edges, printed top-down.
- **Walls:** 1.68 mm (4 lines) everywhere instead of 2.2 mm. Hub clips are 1.26 mm (3 lines).
- **Insert bosses:** 1.6 mm of plastic round the insert instead of 1.2, and 5 mm deep for 3 or 4 mm inserts.
- **Clearances** now come from `tolerances.toml` (`fit()`, `holes()`) instead of being typed in.
- **Light sensor:** its board and rails no longer cover the speaker grille, which moved to the end wall. The board now hangs on its tallest part, so the chip offset is easy to adjust (`BH_CHIP_DX`).
- **Feet:** the foot recesses left 0.2 mm of plastic at the corners. The 8 mm feet now stick on flat, over the screw heads.
- **Looks:** a recessed key well hides the switches. There are per-key micro-LED dots, a 5 mm corner radius and an 0.8 mm top chamfer, and the grille-free top makes it calmer.
- **Repo layout:** the project now follows this repo's structure (`model.py`, `test_fit.py`, `output/`), with 3MF, STEP and STL exports and `check()` on every part.

## Bill of materials (remote)

Bought in India; prices are rough, in INR.

| Qty | Part | Notes | ≈ ₹ |
|-----|------|-------|-----|
| 1 | Seeed XIAO ESP32-C3 | already bought | — |
| 1 | slim 2.4 GHz FPC antenna, U.FL / IPEX (≈ 40 × 7.5 mm) | if yours is the 40 × 20 mm one (see above) | 50–100 |
| 5 | micro LEDs: pre-wired 0603 SMD, or 1.8 mm through-hole, warm white | 4 key dots + charging dot. The pre-wired "model railway" ones often have a 12 V resistor on the lead: cut it off | 150–300 |
| 5 | resistors: 4 × 470 Ω (white LEDs; 1 kΩ for red or green), 1 × 1 kΩ | LED current, 1–3 mA | 5 |
| 1 | LiPo 502540, 450 mAh, with protection PCB | measure it: the bay is 25.2 × 43.2 mm. The XIAO charges at 380 mA, so pick a cell rated for 1C | 150–250 |
| 4 | MX-style switches, e.g. Outemu (Cosmic Byte 20-pack) | 3- or 5-pin. Blue = clicky, brown = tactile, red = linear | ≈ 145 / 20 |
| 1 | passive buzzer 12 × 8.5 mm ("12085") | a magnetic type needs an S8050 NPN + 1 kΩ | 10–20 |
| 1 | BH1750 light sensor (GY-302), header removed | already have | — |
| 2 | BAT43 or 1N5819 Schottky diodes | key 4 shares two wake pins | 2–5 |
| 2 + 1 | 470 kΩ resistors + 100 nF capacitor | battery voltage divider (about 4 µA) | 2–5 |
| 4 | M2 heat-set inserts, M2 × 3 or M2 × 4 (Ø3.5–3.6) | | 20–40 |
| 4 | M2 × 5 (or × 6) countersunk screws | | 10–20 |
| 4 | 8 mm round rubber bumpers | stick them over the screws | 20–40 |
| — | thin silicone wire (28–30 AWG), double-sided foam tape, a little CA glue | | — |

Gateway: one ESP32-C3 SuperMini (already bought) and any USB charger, plus the radar module if you build a pod.

## Wiring (hand-wired, no PCB)

```
Keys       key 1 -> D0 (GPIO2)      key 2 -> D1 (GPIO3)      key 3 -> D3 (GPIO5)
           key 4 -> two diodes: one to D0, one to D1 (striped end towards key 4)
           other pin of every key -> GND (one wire chained through all 4)

Key LEDs   3V3 -> LED anode; LED cathode -> 470 R -> pin (the LED lights when the pin is LOW)
           key 1 -> D6 (GPIO21)   key 2 -> D7 (GPIO20)   key 3 -> D8 (GPIO8)   key 4 -> D9 (GPIO9)

Charging   XIAO 5V -> 1k -> LED anode; LED cathode -> cathode pad of the XIAO's own charge LED
LED        (the charger pulls it low while charging: lights while charging, goes out when full)

Power      LiPo + (red) -> XIAO BAT+ pad, LiPo - (black) -> BAT- pad (both underneath; BAT- is nearer the USB end)

Battery    XIAO BAT+ -> 470k -> D2 (GPIO4) -> 470k -> GND, 100 nF from D2 to GND

Light      BH1750 VCC -> 3V3, GND -> GND, SDA -> D4 (GPIO6), SCL -> D5 (GPIO7), ADDR -> GND

Buzzer     piezo type:    D10 (GPIO10) -> buzzer + ; buzzer - -> GND
           magnetic type: D10 -> 1k -> S8050 base; emitter -> GND; collector -> buzzer - ; buzzer + -> 3V3
```

Notes on the wiring:

- Only D0–D3 (GPIO2–5) can wake the C3 from deep sleep, and D2 reads the battery. So key 4 is encoded as "D0 and D1 both low", and the firmware decodes it.
- GPIO2 (D0) is a strapping pin and must be high at reset. Don't hold key 1 or key 4 while plugging in or connecting the battery.
- GPIO8 and GPIO9 are strapping pins too. With the LEDs wired from 3V3 into the pin (above), they stay high at reset, so boot is not affected.
- D6 is the UART TX pin, so key 1's dot flickers for a moment at boot. That's normal.
- The LEDs only light while the remote is awake: a short flash for "press sent", and the scene's dot for a second if your firmware reports state. In deep sleep the pins float and the LEDs are off, so battery life doesn't change.
- Cut the battery plug off and solder the leads to the pads one at a time, so the bare ends never touch. Check the polarity: the XIAO has no reverse protection.
- Solder wires to the switch pins with the wire running sideways, not straight down. There is 1.5 mm of wiring room under the pins, and 0.3 mm more above the battery.

## How it works

| Action | Result |
|--------|--------|
| Tap, double-tap or hold (about 1 s) a key | Whatever you mapped in Home Assistant. That key's dot flashes and the buzzer chirps when the gateway confirms |
| Hold the orange key (4) for 5 s | Off: presses are ignored, for carrying it in a bag. Hold 5 s again to turn it on |
| Plug in USB-C | Charges at 380 mA (a 450 mAh cell takes about 1.5 h). The charging dot is lit until it's full. Works while on or off |
| Battery below about 3.4 V | Shuts itself off to protect the cell. Charge it to wake it |

Battery life is an estimate: about 4–5 months per charge with normal use.

## Print settings (Bambu Studio, A1, PLA)

**Print the sliced files.** Run `uv run projects/ha-macropad/print_plan.py hk22` (or `hk4`)
after `model.py`, then open the files in `output/hk22/print/` in Bambu Studio and print them
as they are:

| File | Process | Time | PLA |
|------|---------|------|-----|
| `hk22-all-parts.gcode.3mf` (`print_plan.py hk22 all`) | **every part on one plate**: shell, plate, base, 4 keycaps | 1 h 31 min | 32.0 g |
| `0_test_plate_keycap.gcode.3mf` (`print_plan.py hk22 test`) | the plate + 1 keycap, to test before the full set | 9 min | 2.5 g |
| `1_shell.gcode.3mf` | the shell | 49 min | 16.8 g |
| `2_plate_base.gcode.3mf` | the plate and the plain base | 23 min | 10.5 g |
| `3_keycaps.gcode.3mf` (× 4) | the keycaps. Set one cap to the orange filament | 18 min | 4.8 g |

All of them use 0.20 mm Standard with the changes below. Every height in the model (plate
seat, snap catches, sensor cradle, keycap socket) sits on a 0.2 mm layer line.

The changes from Bambu's presets, and why:

- **Plate type: Textured PEI, bed at 65 °C.** Files sliced before 2026-10-17 were set for
  the Cool Plate by mistake, so the bed only heated to 35 °C. That gives a weak first layer
  with gaps. Re-run `print_plan.py` and use the new files.

- **Wall generator: Arachne.** The classic generator leaves small voids where a wall is not a
  whole number of 0.42 mm lines wide: round the speaker grille, round the LED dots on the
  deck face, and in the plate. Arachne varies the line width to fill them.
- **Wall loops: 3.**
- **First layer at 30 mm/s, first-layer solid infill at 60 mm/s.** The shell's deck (the face
  you see) and the base's underside are the first layer. Slower lines fuse without gaps.
- **Seam: Back.** It lands on the USB-C wall.
- **Avoid crossing walls: on.** Travel moves go round the walls, not across the visible ones.
- **Nozzle 210 °C (215 °C first layer), flow capped at 12 mm³/s.** At that flow 210 °C is
  hot enough for any PLA, so walls and infill stay full (no gaps), and cooler PLA strings
  less than the preset's 220 °C.
- **Outer walls 60 mm/s at 2000 mm/s², inner walls 150 mm/s** (Bambu's High Quality values):
  no ringing on the walls.
- **Keycaps top-down.** The flat top prints on the bed and takes its texture, like the shell's
  deck; the socket opens upwards, exactly as on the fit coupon. Don't flip them.
- **Print sequence: by layer** (the preset). "By object" stops strings between parts, but
  Bambu Studio then keeps a wide clearance round every part and won't let you arrange them
  closely.

If the print strings (fine hairs between parts), or the deck face still shows gaps between
lines, the slicer is not the cause. Check these:

- Wash the plate with dish soap and water.
- Make sure you use the textured PEI side.
- Run the printer's bed levelling.
- **Dry the filament.** Wet PLA strings, pops or crackles at the nozzle, and under-extrudes,
  which leaves gaps. PLA takes up water in humid air within days. Dry it at 50–55 °C for
  6–8 hours in a filament dryer, then store it in a sealed box with silica gel.
- **Pick the filament profile for your brand** in Bambu Studio. If it isn't Bambu PLA, use
  Generic PLA or the maker's profile. Then run *Calibration → Temperature* and
  *Calibration → Retraction test* once for that spool.

Times for the other parts, from a headless slice (`uv run slice`), Bambu PLA Basic, 0.20 mm
Standard unless noted:

| Part | Orientation (as exported) | Time | PLA | Notes |
|------|--------------------------|------|-----|-------|
| fit coupon | flat | 14 min | 5.3 g | print first |
| HK-4 shell | deck on the bed | 36 min at 0.16 mm (32 min at 0.20) | 17.6 g | textured PEI gives the top its matte finish. 0.16 mm layers show fewer lines on the walls. Seam: back |
| HK-4 plate | top on the bed | 3 min | 1.1 g | |
| HK-4 base | flat | 16 min | 9.0 g | AMS: label in white or black (the first 2 layers swap) |
| keycap × 4 | top on the bed, open side up | 4–5 min each | 1.2 g each | flat top: nothing special to set |
| HK-22 shell / base | as above | 30 / 16 min | 16.3 / 9.3 g | |
| hub shell / base | deck down / flat | 9 / 10 min | 4.6 / 3.4 g | the clips stand upright: print the base about 220 °C for good layer bonding |
| LD2410C pod / bracket | window down / flat bottom | 10 / 18 min | 3.6 / 6.5 g | |
| LD2450 pod / bracket | window down / flat bottom | 13 / 22 min | 6.2 / 10.9 g | |

A full HK-4 from `print_plan.py` is about 1 h 40 min and 33 g. Elsewhere, use 3 Arachne walls and 15% infill, with no supports and no brim. The bed edges of the shells, plates, bases, keycaps and radar pods are chamfered, so leave elephant-foot compensation at the preset.

### Fit coupon first

- **Switch holes (14.0 / 14.1 / 14.2):** pick the one where a switch clicks in firmly without wobbling. Set `SWITCH_HOLE` in `remote.py`. Result on this A1 (2026-10-17): 14.0 fits firmly, so `SWITCH_HOLE = 14.0`. The next coupon prints 13.9 / 14.0 / 14.1.
- **Keycap posts (labelled 00–20 = slop 0.00–0.20 mm):** turn the bar over and push each
  post onto a switch. It goes down inside the square rim round the cross. Pick the snuggest
  one that goes on fully without forcing, and set `STEM_SLOP` in `keycap.py`. Result on
  the Outemu box stems (2026-10-17): 10 fits snugly, so `STEM_SLOP = 0.10`. If no post
  goes into the rim, the rim is smaller than 5.5 mm: lower `STEM_D` to 5.3. If you have
  already printed the coupon, print only `coupon/stem-test.gcode.3mf`.

## Assembly (remote)

1. **Measure, then re-export if anything differs.** You'll need your battery, antenna and BH1750 board (chip position: `BH_CHIP_DX`, tallest part: `BH_TALL`). Run `model.py` and `test_fit.py`.
2. Press the 4 heat-set inserts into the corner bosses (iron at about 220 °C).
3. Push each micro LED up into its light tube from inside, so it shines through the dot. Fix it with a drop of glue, and run its leads along the deck.
4. Clip the 4 switches into the plate, outside the shell, and wire them (see *Wiring*).
   - Turn each switch so its two clips face the plate edges **without** slots: front and back
     on the HK-22, left and right on the HK-4. The slotted edges are the snap beams.
   - Feed the wires down through the well. Push the plate straight down until both sides
     click. It rests on the 45° ledge and the barbs hold it down.
   - To take it out, open the base. From inside, press each barb inwards through the pocket
     under the well wall, and push the plate up.
5. Push the BH1750, chip up, straight up into its cradle under the light window until both lips click under it. The wires leave from the short end. Stick the antenna to the inside of the front wall (bar) or right wall (square), and plug it into the XIAO's U.FL socket.
6. In the base:
   - Stick the battery in its bay with foam tape, leads towards the XIAO.
   - Push the XIAO back in its cradle until its USB-C sits in the port, 0.3 mm short of the outside, and fix it with a dab of hot glue.
   - Trim the buzzer pins to about 1.5 mm, solder its wires and set it in its seat. The wires run along the groove to the XIAO.
7. Flash the firmware over USB-C. Put the base on, fit the 4 screws, and stick the feet over them.
8. Push the keycaps on, with the orange one at position 4. The post goes inside the square rim round the cross, either way round.

## Hub and radar pods

- **Hub:**
  - The status dot is carried up from the SuperMini's blue LED (GPIO8, active-low) by a light tube. Where that LED sits varies between SuperMini makers, so measure yours and set `SM_LED_DX` / `SM_LED_DY` in `hub.py`. The tube follows.
  - Measure how far the USB-C sticks out past the PCB, and set `SM_USB_OVERHANG` (default 1.0 mm, a guess).
  - The base has 4 snap clips sized for 1.5% bending strain. Firm pull to open.
  - `hub-shell-ams.3mf` adds a clear or white plug that diffuses the dot.
- **Radar pods:**
  - The pod slides down onto the bracket's rails; gravity keeps it seated.
  - The bracket sticks into a room corner with 3M VHB tape on its two back faces.
  - Tilt: `TILT` is 20° (LD2410C) or 10° (LD2450) in `radar.py`.
  - The SuperMini stands USB-C end down in a floor channel. A ceiling stop takes the push when the cable goes in.
  - Measure your sandwich or boards (`STACK_T`, `STACK_USB_FROM_BACK`, `SM_T`, `WIRE_GAP`, `SM_USB_OVERHANG`); the pod follows.
  - Hi-Link prefers 12.4 mm between antenna and window. If you see misses at the edge of the range, set `RADOME_GAP = 12.4`; the pod gets deeper.

## Tuning

All of these are parameters at the top of `remote.py` (or `style.py` for the shared look):

- `WELL_DEPTH`, `WELL_GAP`: how deep the keys sit and the gap round them. The body height follows.
- `SWITCH_HOLE`, `PLATE_CLEAR`: switch fit, plate fit.
- `BATT_*`, `BOARD_*`, `BH_*`, `BUZ_*`, `ANT_*`: bought-part sizes. `test_fit.py` re-checks them.
- `SNAP_BARB`: how far the plate's barbs reach. If the plate is hard to push in, lower it by 0.1. If it still lifts, raise it by 0.1.
- `BH_LIP`, `BH_ROOM`: the light-sensor cradle. If the board won't go up far enough to click, its tallest part is taller than 1.2 mm: raise `BH_ROOM`.
- `R_CORNER`, `TOP_CHAMFER`, `SEAM_CHAMFER`, `BASE` (stripe thickness) in `style.py`.

## Print log

| Date | Version | Result | Change for next |
|------|---------|--------|-----------------|
| 2026-10-17 | v0.7 (HK-22) | Printed. Poor surface quality, with small gaps here and there. The plate had nothing holding it in the shell, and nothing held the light sensor | v0.8: plate snaps, sensor cradle, 1.6 mm plate, 14.0 mm switch holes (coupon), sliced files with Arachne walls and a slow first layer |
| | v0.8 | not printed yet | |
