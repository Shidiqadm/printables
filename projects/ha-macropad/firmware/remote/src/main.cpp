// HK remote: 4-key battery remote for Home Assistant (Seeed XIAO ESP32-C3).
//
// The chip deep-sleeps until a key wakes it, works out the gesture (single, double, long,
// a two-key combo, or key 4 held 5 s), sends it over ESP-NOW to the gateway, flashes the
// key's dot and chirps when the gateway confirms, then sleeps again. A timer wake every
// REPORT_EVERY_S reads the BH1750 and the battery and reports them when they change.
// All settings are in config.h; the radio format is in hk_protocol.h.

#include <Arduino.h>
#include <driver/gpio.h>
#include <esp_sleep.h>
#include <math.h>
#include <soc/usb_serial_jtag_struct.h>
#include <sys/time.h>

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

// Dot brightness for the room: DOT_MIN in the dark up to DOT_MAX at DOT_FULL_LUX.
float dot_scale() {
  if (!rtc.lux_valid) return (DOT_MIN + DOT_MAX) / 2;
  const float t = log10f(1.0f + rtc.lux) / log10f(1.0f + DOT_FULL_LUX);
  return DOT_MIN + (DOT_MAX - DOT_MIN) * constrain(t, 0.0f, 1.0f);
}

void poll_lux(bool wait) {
  if (wait)
    while (sensors::lux_pending() && !sensors::lux_ready(millis())) delay(5);
  uint16_t lux;
  if (sensors::lux_ready(millis()) && sensors::lux_read(lux)) {
    rtc.lux = lux;
    rtc.lux_valid = true;
    rtc.lux_read_s = now_s();
  }
  fx::set_scale(dot_scale());
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
  m.lux = rtc.lux_valid ? rtc.lux : hk::LUX_UNKNOWN;
  m.flags = (rtc.off ? hk::F_OFF : 0) | (battery_low() ? hk::F_BATT_LOW : 0);
  return m;
}

radio::Result transmit(const hk::Msg &m, bool scan_allowed = true) {
  const radio::Result r = radio::send(m, idle, scan_allowed);
  // Every message carries light and battery. NO_HA counts too: the hub keeps the values
  // and Home Assistant gets them when it reconnects.
  if (r != radio::FAIL) {
    rtc.sent_mv = rtc.batt_mv;
    rtc.sent_lux = rtc.lux;
    rtc.sent_s = now_s();
  }
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

bool lux_changed() {
  if (!rtc.lux_valid) return false;
  const int d = abs((int)rtc.lux - (int)rtc.sent_lux);
  return d >= LUX_DELTA_MIN && d * 100 >= (int)rtc.sent_lux * LUX_DELTA_PCT;
}

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
  // Stuck-key checks wake us every minute; read the light only every REPORT_EVERY_S.
  if (now - rtc.lux_read_s + 30 >= REPORT_EVERY_S) {
    sensors::lux_start();
    poll_lux(true);
  }
  if (lux_changed() || battery_changed() || now - rtc.sent_s + 30 >= HEARTBEAT_S) report();
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

  poll_lux(false);
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

void interactive(bool cold) {
  if (cold) {
    show_sweep(true);
    wait_fx();
    poll_lux(false);
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
  const uint8_t wake_pins =
      cause == ESP_SLEEP_WAKEUP_GPIO ? keys::from_gpio_mask(esp_sleep_get_gpio_wakeup_status()) : 0;

  bool cold = rtc.magic != RTC_MAGIC;
  if (cold) {
    memset(&rtc, 0, sizeof(rtc));
    rtc.magic = RTC_MAGIC;
    rtc.seq = (uint8_t)random(256);  // so the gateway doesn't mistake new messages for repeats
  }
  keys::begin(rtc.stuck);
  fx::begin();
  LOG("wake cause=%d pins=%u cold=%d\n", cause, wake_pins, cold);

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

  // A key woke us (or this is a fresh boot).
  sensors::lux_start();  // ready in 180 ms, in time to dim the confirmation flash
  fx::set_scale(dot_scale());
  keys::seed(wake_pins);
  if (!rtc.off) radio::start();  // Wi-Fi starts while we wait to see if it's a double tap
  interactive(cold);
  sleep_now();
}

void loop() {}  // never reached: setup() always ends in deep sleep
