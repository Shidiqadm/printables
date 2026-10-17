# HK firmware

Firmware for the HK remote and its gateway. The hardware and wiring are in [../README.md](../README.md).

```
HK remote (XIAO ESP32-C3, battery)  --ESP-NOW-->  HK Hub (SuperMini, USB)  --Wi-Fi-->  Home Assistant
                                    <--ack, scene dot--                    <--show_dot--
```

| Folder | What | Built with |
|--------|------|------------|
| `remote/` | Deep-sleeping remote: keys, dots, buzzer, BH1750, battery | PlatformIO (Arduino, `espressif32 @ 7.1.3`) |
| `gateway/hk-hub.yaml` | The hub device | ESPHome 2026.9 or newer (ESP-NOW component) |
| `gateway/hk/hk-gateway.yaml` | Everything HK-specific, as a package (reusable in a radar pod) | ESPHome |

## What it does

| On the remote | Result |
|---------------|--------|
| Tap, double-tap or hold (1 s) any key | `esphome.hk_press` event: key `1`–`4`, press `single` / `double` / `long` |
| Press 1+3, 2+3 or 3+4 together | Same event with key `1+3`, `2+3` or `3+4` (1+2 reads as key 4 because of the diodes) |
| Hold key 4 for 5 s | Keys off: presses are ignored. Its dot glows from 1 s on to show the hold. Hold 5 s again to turn the keys back on |
| Battery below 3.55 V | Warns after each press. Below 3.40 V it shuts down until it's charged above 3.70 V |
| Every 5 min | Reads light and battery, and sends them when they change (or every 30 min anyway). If the hub doesn't answer, the remote tries again only every 30 min |

What the remote shows:

| Dots and sound | Meaning |
|----------------|---------|
| The key's dot flashes, chirp | Home Assistant got the press |
| Dot blinks twice fast, one beep | The hub got it, but it isn't connected to Home Assistant |
| Dot blinks twice slowly, low buzz | No hub answered |
| One dot glows for about 1 s | Scene state: your automation called `show_dot` |
| Dots sweep 4→1, falling tones | Keys off |
| Dots sweep 1→4, rising tones | Keys on, or just booted |
| Dot 4 blinks dimly | The keys are off (hold key 4 for 5 s) |
| All dots blink twice, two low beeps | Battery low, charge it soon |
| All dots, long low tone | Battery empty, shutting down |

The dots dim themselves in a dark room using the BH1750 reading (`DOT_MIN` / `DOT_MAX` in `config.h`).

The hub's blue dot pulses slowly while it connects, glows dimly once Home Assistant is connected, and flashes when it relays a press. The **Status dot brightness** entity sets the dim level, and 0 turns it off.

## 1. Flash the hub (Home Assistant OS)

1. Install the **ESPHome Device Builder** add-on (Settings → Add-ons) and open it.
2. Copy `gateway/hk-hub.yaml` to `/config/esphome/`, and `gateway/hk/hk-gateway.yaml` to `/config/esphome/hk/`. Use the File editor or Samba add-on. The dashboard ignores sub-folders, so the package doesn't show up as a device.
3. In the dashboard, open **Secrets** (top right) and add the lines below. `wifi_ssid` and `wifi_password` are usually there already.
   ```yaml
   hk_hub_api_key: "paste a key generated with: openssl rand -base64 32"
   hk_hub_ota_password: "any password"
   hk_hub_fallback_password: "any password, 8+ characters"
   ```
4. First flash, over USB:
   1. Click **hk-hub → Install → Manual download → Factory format**.
   2. Open <https://web.esphome.io> in Chrome or Edge, plug the SuperMini into that computer, then **Connect → Install** and pick the file.
   3. If it won't connect, hold the SuperMini's BOOT button while you plug it in.

   Later updates go over Wi-Fi: **Install → Wirelessly**.
5. Plug the hub into one of the Pi's USB ports (or any USB charger). Home Assistant finds it under Settings → Devices & services. Add it and paste the `hk_hub_api_key`.

**Flashing from a Mac instead:** put the secrets above in `gateway/secrets.yaml` (git ignores it), plug the SuperMini in and run `esphome run hk-hub.yaml` from `gateway/`. Pick the USB port the first time.

**If the log shows `Auth Expired` and it never joins Wi-Fi:** that is the SuperMini's badly matched antenna. `hk-hub.yaml` already sets `output_power: 8.5dB`, which fixed it here (2026-10-17). If it still fails, move it closer to the router for the first connection.

Give your router's 2.4 GHz band a fixed channel (1, 6 or 11) if you can. ESP-NOW has to use the same channel as the hub's Wi-Fi. The remote finds a new channel by itself, but the first press after a change is slower.

## 2. Flash the remote

You need PlatformIO: the VS Code extension, or `uv tool install platformio`.

1. Optional: open `remote/src/config.h` and change the settings: `HK_REMOTE_ID` for a second remote, `BATT_CAL`, timings, dot brightness, `BUZZER_ENABLED`.
2. Connect the XIAO to the computer with USB-C, then run:
   ```bash
   sh projects/ha-macropad/firmware/remote/flash.sh
   ```
   It waits for the XIAO on any USB port, flashes it and opens its log. If the XIAO is asleep (no port), unplug it, hold BOOT, plug it in and release BOOT.
   After a flash started from the BOOT button, the XIAO may stay in the bootloader: tap RESET once.
3. It boots with a 1→4 sweep and rising tones, then looks for the hub. A low buzz straight after means no hub answered: start the hub first, then press a key.

There is no pairing. The remote broadcasts on each channel until a hub answers, then remembers the hub and its channel until the battery is disconnected. To tie it to one hub, set `HK_GATEWAY_MAC`.

**Bench test before wiring:** set `HK_DEBUG 1`, flash, and run `sh projects/ha-macropad/firmware/remote/monitor.sh` (it reconnects by itself after a reset or a sleep). Touch D0 to GND with a wire: the log shows `gesture key=1 kind=1` (1 = single, 2 = double, 3 = long) and `gateway on channel …`, and Home Assistant gets an `esphome.hk_press` event. With no LiPo or divider fitted, the battery reads 0 (no cell) and is ignored. Set `HK_DEBUG 0` and flash again before running on the battery: logging keeps it awake longer.

**Re-flashing inside the case:** plug the USB-C into a computer and press any key. While a computer (not a charger) is connected, the remote stays awake, so `pio run -t upload` works. Set `HK_DEBUG 1` for logs (`pio device monitor`).

## 3. Home Assistant

The hub device gets these entities:

- **Events** `Key 1` … `Key 4`, `Keys 1+3`, `Keys 2+3`, `Keys 3+4`, each with the types `single`, `double`, `long`.
- **Sensors:** `Remote light level` (lx), `Remote battery` (%), `Remote battery voltage`, `Remote signal`.
- **Binary sensors:** `Remote keys off`, `Remote battery low`.

It also fires bus events, which are the easiest thing to automate on:

- `esphome.hk_press` with `key`, `press` and `remote`
- `esphome.hk_status` with `status`: `boot`, `on`, `off` or `shutdown`

**Scene-state dots:** call `esphome.hk_hub_show_dot` with `key: 1`–`4` (or `0` for none). The remote lights that dot for about a second. It only listens for 1.5 s after a press, so call it first, before the scene. Once you've used it, the remote waits for the reply after every press. A press without one costs an extra 1.5 s awake. After 20 presses with no `show_dot`, the hub tells the remote to stop waiting, until the next call.

Example automation (Settings → Automations → ⋮ → Edit in YAML). Change the scene and light names to yours:

Compare `key` as text (`key | string == '1'`): Home Assistant turns template variables into native types, so a plain `key == '1'` never matches (the key arrives as the number 1).

```yaml
alias: HK remote
mode: queued
triggers:
  - trigger: event
    event_type: esphome.hk_press
variables:
  key: "{{ trigger.event.data.key }}"
  press: "{{ trigger.event.data.press }}"
actions:
  - choose:
      - conditions: "{{ key | string == '1' and press == 'single' }}"
        sequence:
          - action: esphome.hk_hub_show_dot
            data: { key: 1 }
          - action: scene.turn_on
            target: { entity_id: scene.living_room_relax }
      - conditions: "{{ key | string == '2' and press == 'single' }}"
        sequence:
          - action: esphome.hk_hub_show_dot
            data: { key: 2 }
          - action: scene.turn_on
            target: { entity_id: scene.living_room_bright }
      - conditions: "{{ key | string == '3' and press == 'single' }}"
        sequence:
          - action: light.toggle
            target: { entity_id: light.desk_lamp }
      - conditions: "{{ key | string == '3' and press == 'double' }}"
        sequence:
          - action: light.turn_on
            target: { entity_id: light.desk_lamp }
            data: { brightness_pct: 100 }
      - conditions: "{{ key | string == '4' and press == 'long' }}"
        sequence:
          - action: esphome.hk_hub_show_dot
            data: { key: 0 }
          - action: light.turn_off
            target: { area_id: living_room }
      - conditions: "{{ key | string == '1+3' }}"
        sequence:
          - action: scene.turn_on
            target: { entity_id: scene.movie }
```

A low-battery reminder:

```yaml
alias: HK remote battery
triggers:
  - trigger: state
    entity_id: binary_sensor.hk_hub_remote_battery_low
    to: "on"
actions:
  - action: notify.notify
    data: { message: "The HK remote's battery is low. Charge it over USB-C." }
```

## Using a radar pod as the gateway instead

Add the package to the pod's ESPHome config, and use either the pod or the hub, not both:

```yaml
packages:
  hk: !include hk/hk-gateway.yaml
```

The package turns off Wi-Fi power saving, because ESP-NOW only receives while the radio is awake. Service names follow the device name, for example `esphome.radar_pod_show_dot`.

## Not verified yet

Both builds compile, but nothing has run on hardware yet. Check these on the first build:

- **Long press:** `LONG_PRESS_MS` is counted from wake, and boot time adds about 0.1 s. Shorten it if 1 s feels long.
- **Battery reading:** compare it with a multimeter and set `BATT_CAL`.
- **Buzzer:** the chirp frequencies are guesses for a 12085 piezo. Change `CHIRP` in `main.cpp` and `BUZZER_DUTY` for volume.
- **Hub LED:** the SuperMini's LED is on GPIO8 on most boards. If yours differs, change `hk_led_pin` in `hk-gateway.yaml`.
- **Battery life:** not measured. Deep sleep is about 44 µA (Seeed's figure) plus 4 µA for the divider. Each press keeps the radio on for about 0.5 s, or about 2 s with scene dots.
- **Arduino core:** the remote is built and tested on the pinned `espressif32 @ 7.1.3` (Arduino core 2.0.17). Core 3.x has `#if` paths for the changed ESP-NOW callbacks, but they haven't been compiled.
- **Stuck keys:** a key that stays held (in a bag) is ignored until it comes up, which saves the battery. While key 1 is stuck, key 4 reads as key 2, because they share D0.
- **No encryption:** the ESP-NOW link isn't encrypted (ESPHome's ESP-NOW component has none). Someone in radio range with an ESP32 could fake key presses. `HK_GATEWAY_MAC` stops the remote from talking to a different hub, but nothing stops a fake remote. Don't map the keys to locks or alarms.

## Protocol

There are 13-byte messages from the remote and 7-byte replies from the hub, described in [remote/src/hk_protocol.h](remote/src/hk_protocol.h). The gateway lambdas use the same byte offsets, so change both together.
