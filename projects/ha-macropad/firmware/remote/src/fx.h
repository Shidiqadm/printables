// Key dots (PWM, fades, auto-dim) and the buzzer. Everything runs from tick(), so the
// keys keep being read while a pattern plays.
#pragma once

#include <stdint.h>

namespace fx {

struct Tone {
  uint16_t hz;  // 0 = silence
  uint16_t ms;
};

void begin();
void set_scale(float scale);  // room brightness for the dots, 0..1 (auto-dim)

// Fade the dots in `mask` (bit 0 = key 1) up and down again, starting `delay_ms` from now.
void pulse(uint8_t mask, uint32_t delay_ms, uint16_t in_ms, uint16_t hold_ms, uint16_t out_ms,
           float level = 1.0f);
void glow(uint8_t mask, float level);  // steady layer under the pulses; mask 0 = off
void play(const Tone *tones, uint8_t n, bool append = false);  // append: after what's playing

void tick(uint32_t now);
bool busy(uint32_t now);  // a pulse or tone is still playing
void end();               // everything off, pins safe for deep sleep

}  // namespace fx
