// Everything you might want to change on the HK remote.
#pragma once

#include <stdint.h>

// ---- Identity ----------------------------------------------------------------

// Sent with every message, so Home Assistant can tell two remotes apart.
#define HK_REMOTE_ID 1

// Lock the remote to one gateway: its Wi-Fi MAC, as printed in the gateway's ESPHome log
// ("own address"). Leave it commented out to pair with the first HK gateway that answers.
// #define HK_GATEWAY_MAC {0x00, 0x00, 0x00, 0x00, 0x00, 0x00}

// ---- Pins (XIAO ESP32-C3, see the wiring in ../../README.md) -----------------

#define PIN_KEY_A 2    // D0: key 1, and key 4 through a diode
#define PIN_KEY_B 3    // D1: key 2, and key 4 through a diode
#define PIN_KEY_C 5    // D3: key 3
#define PIN_BATT 4     // D2: battery divider, 470k / 470k
#define PIN_SDA 6      // D4: BH1750
#define PIN_SCL 7      // D5: BH1750
#define PIN_BUZZER 10  // D10: passive buzzer

// LED cathode side of each key dot (D6, D7, D8, D9). The pin sinks the current: LOW = on.
static const uint8_t PIN_DOT[4] = {21, 20, 8, 9};

// ---- Key timing (ms) ---------------------------------------------------------

#define DEBOUNCE_MS 8
#define DOUBLE_GAP_MS 300    // longest gap between the two taps of a double press
#define LONG_PRESS_MS 1000   // counted from wake, so about 0.1 s of boot is included
#define OFF_HOLD_MS 5000     // hold key 4 this long to switch the keys off or on
#define COMBO_SETTLE_MS 50   // the second key of a combo may land this much later
#define STUCK_MS 8000        // a key held longer than this is treated as stuck (bag)
#define LINGER_MS 150        // stay awake this long after the last activity

// ---- Radio -------------------------------------------------------------------

#define ACK_TIMEOUT_MS 120   // wait for the gateway's reply
#define SEND_ATTEMPTS 3
#define SCAN_WAIT_MS 50      // per channel, while looking for the gateway
#define DOTS_WAIT_MS 1500    // listen this long for a scene-state reply from Home Assistant
#define DOTS_SHOW_MS 1000    // default time a scene-state dot stays lit

// ---- Reports -----------------------------------------------------------------

#define REPORT_EVERY_S 300   // timer wake: read light and battery
#define HEARTBEAT_S 1800     // report even if nothing changed
#define OFF_REPORT_S 21600   // while switched off: battery only, every 6 h
#define STUCK_CHECK_S 60     // while a key is stuck: check this often for its release
#define LUX_DELTA_MIN 5      // report a light change of at least this many lx...
#define LUX_DELTA_PCT 15     // ...and at least this many percent
#define BATT_DELTA_MV 40

// ---- Battery (mV at the cell) ------------------------------------------------

#define BATT_DIVIDER 2.0f
#define BATT_CAL 1.000f          // trim against a multimeter: real / reported
#define BATT_ABSENT_MV 2500      // below this there is no cell (or no divider fitted): ignore it.
                                 // A LiPo's protection board cuts out before the cell gets this low.
#define BATT_WARN_MV 3550        // warn on every wake below this
#define BATT_SHUTDOWN_MV 3400    // switch off to protect the cell
#define BATT_RESUME_MV 3700      // charging lifts the cell above this: wake up again
#define SHUTDOWN_CHECK_S 1800

// ---- Feedback ----------------------------------------------------------------

#define DOT_MIN 0.04f        // dot brightness in a dark room (0..1)
#define DOT_MAX 1.00f        // in daylight
#define DOT_FULL_LUX 300.0f  // room light at which the dots reach DOT_MAX
#define BUZZER_ENABLED 1
#define BUZZER_DUTY 0.5f     // 0.5 is loudest for a piezo; lower is quieter

// ---- Debug -------------------------------------------------------------------

// 1 = log over USB serial (115200). Keep 0 for battery use.
#define HK_DEBUG 0

#if HK_DEBUG
#include <Arduino.h>
#define LOG(...) Serial.printf(__VA_ARGS__)
#else
#define LOG(...) \
  do {           \
  } while (0)
#endif
