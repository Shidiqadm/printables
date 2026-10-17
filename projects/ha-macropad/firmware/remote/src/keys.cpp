#include "keys.h"

#include <Arduino.h>
#include <driver/gpio.h>

#include "config.h"
#include "hk_protocol.h"

namespace keys {

namespace {

enum State : uint8_t {
  IDLE,     // nothing pressed
  DOWN,     // first press held; collecting combo keys, timing long / off-hold
  GAP,      // released; waiting to see if a second tap follows
  SECOND,   // second press started; settling which key(s) it is
  LATCHED,  // gesture already sent; waiting for every key to come up
};

State st = IDLE;
uint8_t ignore_ = 0;  // stuck pins, skipped until they read high once

// Debouncer
uint8_t last = 0, stable = 0;
uint32_t last_change = 0, stable_since = 0;

// Gesture in progress
uint8_t mask = 0, mask2 = 0, first = hk::K_NONE;
uint32_t t_down = 0, t_up = 0, t_second = 0;
bool armed_ = false;

Gesture queue[4];
uint8_t q_head = 0, q_len = 0;

void emit(uint8_t key, uint8_t kind) {
  if (key == hk::K_NONE || q_len == sizeof(queue) / sizeof(queue[0])) return;
  queue[(q_head + q_len++) % 4] = {key, kind};
  LOG("gesture key=%u kind=%u\n", key, kind);
}

uint8_t code(uint8_t m) {
  const bool a = m & PIN_A, b = m & PIN_B, c = m & PIN_C;
  if (c) return (a && b) ? hk::K34 : a ? hk::K13 : b ? hk::K23 : hk::K3;
  return (a && b) ? hk::K4 : a ? hk::K1 : b ? hk::K2 : hk::K_NONE;
}

}  // namespace

uint8_t raw() {
  return (digitalRead(PIN_KEY_A) == LOW ? PIN_A : 0) | (digitalRead(PIN_KEY_B) == LOW ? PIN_B : 0) |
         (digitalRead(PIN_KEY_C) == LOW ? PIN_C : 0);
}

uint64_t gpio_mask(uint8_t pins) {
  return ((pins & PIN_A) ? 1ULL << PIN_KEY_A : 0) | ((pins & PIN_B) ? 1ULL << PIN_KEY_B : 0) |
         ((pins & PIN_C) ? 1ULL << PIN_KEY_C : 0);
}

uint8_t from_gpio_mask(uint64_t m) {
  return ((m >> PIN_KEY_A) & 1 ? PIN_A : 0) | ((m >> PIN_KEY_B) & 1 ? PIN_B : 0) |
         ((m >> PIN_KEY_C) & 1 ? PIN_C : 0);
}

uint8_t dots(uint8_t key) {
  switch (key) {
    case hk::K1: return 0b0001;
    case hk::K2: return 0b0010;
    case hk::K3: return 0b0100;
    case hk::K4: return 0b1000;
    case hk::K13: return 0b0101;
    case hk::K23: return 0b0110;
    case hk::K34: return 0b1100;
    default: return 0;
  }
}

void begin(uint8_t ignore) {
  for (int pin : {PIN_KEY_A, PIN_KEY_B, PIN_KEY_C}) {
    gpio_hold_dis((gpio_num_t)pin);  // sleep_now() holds them
    pinMode(pin, INPUT_PULLUP);
  }
  ignore_ = ignore;
  delayMicroseconds(50);  // let the pull-ups charge the wiring
}

void seed(uint8_t wake_pins) {
  const uint8_t held = raw() & ~ignore_;
  const uint8_t pins = held ? held : (wake_pins & ~ignore_);
  if (!pins) return;
  // The press started at wake, before setup() ran: count from 0.
  mask = pins;
  t_down = 0;
  st = DOWN;
  last = stable = held;
  last_change = stable_since = millis();
}

void tick(uint32_t now) {
  uint8_t r = raw();
  ignore_ &= r;  // a stuck key that came up is live again
  r &= ~ignore_;
  if (r != last) {
    last = r;
    last_change = now;
  } else if (r != stable && now - last_change >= DEBOUNCE_MS) {
    stable = r;
    stable_since = now;
  }
  const uint8_t s = stable;

  switch (st) {
    case IDLE:
      if (s) {
        mask = s;
        t_down = now;
        st = DOWN;
      }
      break;

    case DOWN: {
      const uint32_t held = now - t_down;
      if (s) {
        mask |= s;  // a second key joining makes it a combo
        const uint8_t c = code(mask);
        if (c == hk::K4) {
          // Key 4's long press waits for release, so holding on to 5 s doesn't send it.
          if (held >= OFF_HOLD_MS) {
            emit(hk::K4, TOGGLE);
            armed_ = false;
            st = LATCHED;
          } else if (held >= LONG_PRESS_MS) {
            armed_ = true;
          }
        } else if (held >= LONG_PRESS_MS) {
          emit(c, hk::P_LONG);
          st = LATCHED;
        }
      } else {
        const uint8_t c = code(mask);
        armed_ = false;
        if (c == hk::K4 && held >= LONG_PRESS_MS) {
          emit(c, hk::P_LONG);
          st = IDLE;
        } else {
          first = c;
          t_up = now;
          st = GAP;
        }
      }
      break;
    }

    case GAP:
      if (s) {
        mask2 = s;
        t_second = now;
        st = SECOND;
      } else if (now - t_up >= DOUBLE_GAP_MS) {
        emit(first, hk::P_SINGLE);
        st = IDLE;
      }
      break;

    case SECOND:
      if (s) mask2 |= s;
      if (!s || now - t_second >= COMBO_SETTLE_MS) {
        if (code(mask2) == first) {
          emit(first, hk::P_DOUBLE);
          st = s ? LATCHED : IDLE;
        } else {
          // A different key: the first one was a single, and this one starts over.
          emit(first, hk::P_SINGLE);
          mask = mask2;
          t_down = t_second;
          st = DOWN;
        }
      }
      break;

    case LATCHED:
      if (!s) st = IDLE;
      break;
  }
  if (st != DOWN || code(mask) != hk::K4) armed_ = false;  // e.g. key 3 joined: now a 3+4 combo
}

bool pop(Gesture &g) {
  if (!q_len) return false;
  g = queue[q_head];
  q_head = (q_head + 1) % 4;
  q_len--;
  return true;
}

bool idle() { return st == IDLE && q_len == 0; }

bool armed() { return armed_; }

bool stuck(uint32_t now) { return stable && now - stable_since >= STUCK_MS; }

}  // namespace keys
