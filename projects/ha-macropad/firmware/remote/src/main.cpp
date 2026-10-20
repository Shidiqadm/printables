// HK remote: 4-key battery remote for Home Assistant (Seeed XIAO ESP32-C3).
//
// The chip deep-sleeps until a key wakes it, works out the gesture (single, double, long,
// a two-key combo, or key 4 held 5 s), sends it over ESP-NOW to the gateway, flashes the
// key's dot and chirps when the gateway confirms, then sleeps again. A timer wake every
// REPORT_EVERY_S checks the battery and reports it when it changes. Every reply from the
// gateway carries the dot brightness set in Home Assistant (dim at night).
//
// With an ADXL345 (HK-22) it also wakes on motion: picked up after lying still, shaken, or
// turned face down and held still. Its interrupt shares D3 with key 3 through a diode, so it
// is read and cleared first thing at every wake, and kept off while we're awake.
// All settings are in config.h; the radio format is in hk_protocol.h.

#include <Arduino.h>
#include <driver/gpio.h>
#include <esp_sleep.h>
#include <soc/usb_serial_jtag_struct.h>
#include <sys/time.h>

#include "accel.h"
#include "config.h"
#include "fx.h"
#include "hk_protocol.h"
#include "keys.h"
#include "radio.h"
#include "sensors.h"
#include "state.h"

RTC_DATA_ATTR RtcState rtc;

namespace {

#define COUNT(a) (sizeof(a) / sizeof((a)[0]))

// ---- Feedback patterns -------------------------------------------------------

const fx::Tone CHIRP[] = {{2700, 35}, {0, 15}, {3400, 45}};
const fx::Tone NO_HA_TONE[] = {{1800, 90}};
const fx::Tone NO_GATEWAY_TONE[] = {{600, 220}};
const fx::Tone ON_TONE[] = {{1500, 60}, {0, 30}, {2200, 60}, {0, 30}, {3000, 90}};
const fx::Tone OFF_TONE[] = {{3000, 60}, {0, 30}, {2200, 60}, {0, 30}, {1500, 90}};
const fx::Tone EMPTY_TONE[] = {{500, 300}};

void show_confirm(uint8_t dots) {
  fx::pulse(dots, 0, 30, 120, 220);
  fx::play(CHIRP, COUNT(CHIRP));
}

void show_no_ha(uint8_t dots) {  // the gateway got it, Home Assistant didn't
  fx::pulse(dots, 0, 20, 60, 60);
  fx::pulse(dots, 180, 20, 60, 60);
  fx::play(NO_HA_TONE, COUNT(NO_HA_TONE));
}

void show_no_gateway(uint8_t dots) {
  fx::pulse(dots, 0, 40, 160, 100);
  fx::pulse(dots, 400, 40, 160, 100);
  fx::play(NO_GATEWAY_TONE, COUNT(NO_GATEWAY_TONE));
}

void show_low_battery() {  // after the press feedback, so it plays after the chirp
  fx::pulse(0b1111, 500, 30, 80, 80, 0.6f);
  fx::pulse(0b1111, 800, 30, 80, 80, 0.6f);
  const fx::Tone t[] = {{0, 400}, {900, 70}, {0, 230}, {700, 90}};
  fx::play(t, COUNT(t), true);
}

void show_sweep(bool up) {  // 1 -> 4 for on, 4 -> 1 for off
  for (int i = 0; i < 4; i++) fx::pulse(1 << (up ? i : 3 - i), i * 90, 60, 60, 200);
  if (up)
    fx::play(ON_TONE, COUNT(ON_TONE));
  else
    fx::play(OFF_TONE, COUNT(OFF_TONE));
}

void show_off_reminder() { fx::pulse(0b1000, 0, 30, 60, 150, 0.4f); }

// ---- Helpers -----------------------------------------------------------------

uint32_t now_s() {  // seconds since cold boot; keeps counting through deep sleep
  struct timeval tv;
  gettimeofday(&tv, nullptr);
  return tv.tv_sec;
}

bool battery_low() { return rtc.batt_mv && rtc.batt_mv < BATT_WARN_MV; }

// A computer (not a charger) on the USB-C port sends a USB frame every millisecond.
bool usb_host_present() {
  const uint32_t a = USB_SERIAL_JTAG.fram_num.sof_frame_index;
  delay(3);
  return USB_SERIAL_JTAG.fram_num.sof_frame_index != a;
}

// Dot brightness from Home Assistant's "Remote dot brightness" (0-100 %), which comes with
// every reply from the gateway. Squared, so the low end of the slider has the fine steps a
// dark room needs: 20 % is a soft night glow.
float dot_scale() {
  const float t = (rtc.dot_level <= 100 ? rtc.dot_level : DOT_DEFAULT_PCT) / 100.0f;
  return t * t;
}

void idle() {  // one 2 ms step of everything that runs in the background
  const uint32_t now = millis();
  keys::tick(now);
  fx::glow(keys::armed() ? 0b1000 : 0, 0.35f);  // key 4 held: its dot shows the 5 s hold
  fx::tick(now);
  delay(2);
}

void wait_fx() {
  while (fx::busy(millis())) idle();
}

hk::Msg make_msg(uint8_t type, uint8_t key = 0, uint8_t value = 0) {
  hk::Msg m = {};
  m.magic[0] = 'H';
  m.magic[1] = 'K';
  m.version = hk::VERSION;
  m.type = type;
  m.seq = ++rtc.seq;
  m.remote = HK_REMOTE_ID;
  m.key = key;
  m.value = value;
  m.batt_mv = rtc.batt_mv;
  m.lux = hk::LUX_UNKNOWN;  // no light sensor since v0.9
  m.flags = (rtc.off ? hk::F_OFF : 0) | (battery_low() ? hk::F_BATT_LOW : 0);
  return m;
}

radio::Result transmit(const hk::Msg &m, bool scan_allowed = true) {
  const radio::Result r = radio::send(m, idle, scan_allowed);
  // Every message carries the battery. NO_HA counts too: the hub keeps the value and Home
  // Assistant gets it when it reconnects.
  if (r != radio::FAIL) {
    rtc.sent_mv = rtc.batt_mv;
    rtc.sent_s = now_s();
  }
  fx::set_scale(dot_scale());  // the reply may have brought a new brightness
  return r;
}

// ---- Sleep -------------------------------------------------------------------

[[noreturn]] void sleep_now() {
  fx::end();
  uint8_t wake = 0;
  uint32_t timer_s;
  if (rtc.shutdown) {
    rtc.stuck = 0;
    timer_s = SHUTDOWN_CHECK_S;
  } else {
    // A key that is still down would wake us at once: leave it out until it comes up.
    rtc.stuck = keys::raw();
    // Off: only D0 wakes us (key 1 or key 4), to look for the 5 s hold.
    wake = (rtc.off ? keys::PIN_A : keys::ALL) & ~rtc.stuck;
    timer_s = rtc.stuck ? STUCK_CHECK_S : rtc.off ? OFF_REPORT_S : REPORT_EVERY_S;
  }
  // The accelerometer can only wake us through D3: standby whenever D3 isn't a wake pin.
  accel::sleep(!(wake & keys::PIN_C) || rtc.off ? accel::OFF : rtc.watch_move ? accel::MOVE : accel::STILL);
  // Wake pins keep their pull-up. The rest get a pull-down, which draws nothing whether
  // the key is up or held down (keys switch to GND).
  const uint8_t bits[] = {keys::PIN_A, keys::PIN_B, keys::PIN_C};
  const gpio_num_t pins[] = {(gpio_num_t)PIN_KEY_A, (gpio_num_t)PIN_KEY_B, (gpio_num_t)PIN_KEY_C};
  for (int i = 0; i < 3; i++) {
    if (wake & bits[i]) {
      gpio_pulldown_dis(pins[i]);
      gpio_pullup_en(pins[i]);
    } else {
      gpio_pullup_dis(pins[i]);
      gpio_pulldown_en(pins[i]);
    }
    gpio_hold_en(pins[i]);
  }
  if (wake) esp_deep_sleep_enable_gpio_wakeup(keys::gpio_mask(wake), ESP_GPIO_WAKEUP_GPIO_LOW);
  esp_sleep_enable_timer_wakeup((uint64_t)timer_s * 1000000ULL);
  esp_deep_sleep_disable_rom_logging();  // the ROM's boot text would flicker key 1's dot (D6 = TX)
#if !SOC_GPIO_SUPPORT_HOLD_SINGLE_IO_IN_DSLP
  gpio_deep_sleep_hold_en();
#endif
  LOG("sleep: wake=%u stuck=%u timer=%lus off=%d\n", wake, rtc.stuck, timer_s, rtc.off);
  esp_deep_sleep_start();
}

[[noreturn]] void shut_down(bool user_here) {
  rtc.shutdown = true;
  if (user_here) {
    fx::pulse(0b1111, 0, 50, 200, 300, 0.5f);
    fx::play(EMPTY_TONE, COUNT(EMPTY_TONE));
  }
  transmit(make_msg(hk::T_STATUS, 0, hk::S_SHUTDOWN));
  wait_fx();
  sleep_now();
}

// ---- Wakes -------------------------------------------------------------------

bool battery_changed() { return abs((int)rtc.batt_mv - (int)rtc.sent_mv) >= BATT_DELTA_MV; }

void report() {
  const uint32_t now = now_s();
  // Nobody answered last time (hub unplugged?): try again only every HEARTBEAT_S, and
  // only on the known channel, instead of a full radio search every wake.
  if (rtc.report_failed_s && now - rtc.report_failed_s + 30 < HEARTBEAT_S) return;
  const bool ok = transmit(make_msg(hk::T_REPORT), false) != radio::FAIL;
  rtc.report_failed_s = ok ? 0 : max<uint32_t>(now, 1);
}

void timer_wake() {
  const uint32_t now = now_s();
  if (rtc.off) {  // battery only, rarely
    if (now - rtc.sent_s + 60 >= OFF_REPORT_S) report();
    return;
  }
  if (battery_changed() || now - rtc.sent_s + 30 >= HEARTBEAT_S) report();
}

uint32_t dots_until = 0;  // listening for scene-state dots until then
bool warned = false;      // low-battery warning given on this wake

void handle(const keys::Gesture &g) {
  if (rtc.off) {
    if (g.kind == keys::TOGGLE) {
      rtc.off = false;
      show_sweep(true);
      transmit(make_msg(hk::T_STATUS, 0, hk::S_ON));
    } else {
      show_off_reminder();
    }
    return;
  }
  if (g.kind == keys::TOGGLE) {
    rtc.off = true;
    show_sweep(false);
    transmit(make_msg(hk::T_STATUS, 0, hk::S_OFF));
    return;
  }

  const uint8_t dots = keys::dots(g.key);
  switch (transmit(make_msg(hk::T_PRESS, g.key, g.kind))) {
    case radio::OK:
      show_confirm(dots);
      if (rtc.dots_feature) dots_until = millis() + DOTS_WAIT_MS;
      break;
    case radio::NO_HA:
      show_no_ha(dots);
      break;
    case radio::FAIL:
      show_no_gateway(dots);
      break;
  }
  if (battery_low() && !warned) {
    show_low_battery();
    warned = true;
  }
}

// ---- Motion (ADXL345) ----------------------------------------------------------

void send_motion(uint8_t kind) {
  // A pickup happens on every lift: no sound, and no radio search if the hub is away.
  const bool quiet = kind == hk::M_PICKUP;
  switch (transmit(make_msg(hk::T_MOTION, 0, kind), !quiet)) {
    case radio::OK:
      if (!quiet) show_confirm(0b1111);
      if (rtc.dots_feature) dots_until = millis() + DOTS_WAIT_MS;
      break;
    case radio::NO_HA:
      if (!quiet) show_no_ha(0b1111);
      break;
    case radio::FAIL:
      if (!quiet) show_no_gateway(0b1111);
      break;
  }
}

// Watch for SHAKE_WINDOW_MS at 100 Hz. A key press ends it: the key wins.
bool shaken() {
  accel::Shake shake;
  accel::fast();
  const uint32_t t0 = millis();
  uint32_t last = 0;
  while (millis() - t0 < SHAKE_WINDOW_MS) {
    idle();
    if (!keys::idle()) return false;
    const uint32_t now = millis();
    if (now - last < 10) continue;
    last = now;
    accel::G g;
    if (accel::read(g)) shake.add(g);
    if (shake.reversals() >= SHAKE_REVERSALS) return true;
  }
  return false;
}

void motion_wake(uint8_t woke) {
  const uint32_t now = now_s();
  if (woke & accel::INACT) {  // still again: put down, or held still
    accel::G g;
    if (accel::read(g)) {
      LOG("still: up axis %.2f g\n", g.z);
      rtc.rest_s = g.z > LEVEL_G ? max<uint32_t>(now, 1) : 0;
      // Face down and still in the hand. Lying face down on a table presses the keys: no flip.
      if (g.z < -FLIP_G && !keys::raw()) send_motion(hk::M_FLIP);
    }
    rtc.watch_move = true;
    return;
  }
  // Moved after lying still (ACT), or jolted in the hand (TAP)
  const bool pickup = (woke & accel::ACT) && rtc.rest_s && now - rtc.rest_s >= PICKUP_REST_S;
  rtc.rest_s = 0;
  rtc.watch_move = false;
  if (pickup) {
    radio::start();                             // ready for the first key press
    fx::pulse(0b1111, 0, 150, 600, 400, 0.5f);  // the dots wake up with it
  }
  if (shaken())
    send_motion(hk::M_SHAKE);
  else if (pickup)
    send_motion(hk::M_PICKUP);
  LOG("moved: pickup=%d\n", pickup);
}

void interactive(bool cold) {
  if (cold) {
    show_sweep(true);
    wait_fx();
    if (transmit(make_msg(hk::T_STATUS, 0, hk::S_BOOT)) == radio::FAIL)
      fx::play(NO_GATEWAY_TONE, COUNT(NO_GATEWAY_TONE));
  }
  uint32_t last_activity = millis();
  for (;;) {
    idle();
    const uint32_t now = millis();

    uint8_t mask;
    uint16_t ms;
    if (radio::pop_dots(mask, ms)) {
      if (mask) fx::pulse(mask, 0, 150, ms, 350, 0.8f);
      dots_until = 0;
      last_activity = now;
    }

    keys::Gesture g;
    if (keys::pop(g)) {
      handle(g);
      last_activity = millis();
      continue;
    }

    if (keys::stuck(now)) break;
    const bool done = keys::idle() && !fx::busy(now) && (int32_t)(now - dots_until) >= 0 &&
                      now - last_activity >= LINGER_MS;
    // Plugged into a computer: stay awake, so the firmware can be flashed through the case.
    // After a fresh boot, give the computer 2 s to start talking.
    if (done && !usb_host_present() && !(cold && now < 2000)) break;
  }
}

}  // namespace

void setup() {
  Serial.begin(115200);
  Serial.setTxTimeoutMs(0);  // never block when no computer is listening
#if HK_DEBUG
  // Give the computer's serial monitor up to 2 s to attach, so the first lines aren't lost.
  for (const uint32_t t = millis(); !Serial && millis() - t < 2000;) delay(10);
#endif

  const esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
  uint8_t wake_pins =
      cause == ESP_SLEEP_WAKEUP_GPIO ? keys::from_gpio_mask(esp_sleep_get_gpio_wakeup_status()) : 0;

  bool cold = rtc.magic != RTC_MAGIC;
  if (cold) {
    memset(&rtc, 0, sizeof(rtc));
    rtc.magic = RTC_MAGIC;
    rtc.seq = (uint8_t)random(256);  // so the gateway doesn't mistake new messages for repeats
    rtc.dot_level = DOT_LEVEL_UNKNOWN;
  }
  keys::begin(rtc.stuck);
  fx::begin();
  // Before anything reads the keys: what did the accelerometer see? Reading it clears its
  // interrupt, so if D3 is high now, it was the accelerometer that pulled it low, not key 3.
  const uint8_t woke = accel::begin();
  if (woke && !(keys::raw() & keys::PIN_C)) wake_pins &= ~keys::PIN_C;
  LOG("wake cause=%d pins=%u motion=%u cold=%d\n", cause, wake_pins, woke, cold);

  // Battery first, before the radio loads the cell.
  rtc.batt_mv = sensors::battery_mv();
  LOG("battery %u mV (0 = no cell)\n", rtc.batt_mv);
  if (rtc.shutdown) {
    if (rtc.batt_mv < BATT_RESUME_MV) sleep_now();
    rtc.shutdown = false;  // charged again: start like a fresh boot
    cold = true;
  } else if (rtc.batt_mv && rtc.batt_mv < BATT_SHUTDOWN_MV) {
    delay(20);
    rtc.batt_mv = sensors::battery_mv();
    if (rtc.batt_mv && rtc.batt_mv < BATT_SHUTDOWN_MV) shut_down(cause == ESP_SLEEP_WAKEUP_GPIO);
  }

  if (cause == ESP_SLEEP_WAKEUP_TIMER && !usb_host_present()) {
    timer_wake();
    // A key pressed while we were awake for the report can't wake us any more: handle it.
    // (Stuck keys don't count; the radio starts when a gesture is sent.)
    if (keys::idle() && !(keys::raw() & ~rtc.stuck)) sleep_now();
    interactive(false);
    sleep_now();
  }

  if (cause == ESP_SLEEP_WAKEUP_GPIO && !wake_pins) {  // the accelerometer woke us, not a key
    if (woke && !rtc.off) {
      fx::set_scale(dot_scale());
      motion_wake(woke);
    }
    interactive(false);  // a key pressed meanwhile; otherwise straight back to sleep
    sleep_now();
  }

  // A key woke us (or this is a fresh boot): the remote is in the hand.
  rtc.watch_move = false;
  fx::set_scale(dot_scale());
  keys::seed(wake_pins);
  if (!rtc.off) radio::start();  // Wi-Fi starts while we wait to see if it's a double tap
  interactive(cold);
  sleep_now();
}

void loop() {}  // never reached: setup() always ends in deep sleep
