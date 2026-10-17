#include "fx.h"

#include <Arduino.h>
#include <driver/gpio.h>
#include <driver/ledc.h>

#include "config.h"

namespace fx {

namespace {

constexpr ledc_mode_t MODE = LEDC_LOW_SPEED_MODE;
constexpr ledc_timer_t BUZ_TIMER = LEDC_TIMER_0;
constexpr ledc_timer_t DOT_TIMER = LEDC_TIMER_1;
constexpr ledc_channel_t BUZ_CH = LEDC_CHANNEL_0;
constexpr uint32_t MAX_DUTY = (1 << 10) - 1;  // 10-bit

struct Pulse {
  uint8_t mask;
  uint32_t start;
  uint16_t in, hold, out;
  float level;
};

Pulse pulses[8];
uint8_t n_pulses = 0;

uint8_t glow_mask = 0;
float glow_level = 0;
float scale_ = 0.5f;

Tone tones_[12];
uint8_t n_tones = 0, tone_idx = 0;
uint32_t tone_start = 0;
uint16_t tone_hz = 0;
bool tone_pending = false;

uint32_t duty_now[4] = {MAX_DUTY + 1, MAX_DUTY + 1, MAX_DUTY + 1, MAX_DUTY + 1};

ledc_channel_t dot_ch(int i) { return (ledc_channel_t)(LEDC_CHANNEL_1 + i); }

float envelope(const Pulse &p, uint32_t now) {
  if ((int32_t)(now - p.start) < 0) return 0;
  const uint32_t t = now - p.start;
  if (t < p.in) return (float)t / p.in;
  if (t < (uint32_t)p.in + p.hold) return 1;
  if (t < (uint32_t)p.in + p.hold + p.out) return 1 - (float)(t - p.in - p.hold) / p.out;
  return -1;  // finished
}

void set_tone(uint16_t hz) {
  if (hz == tone_hz) return;
  tone_hz = hz;
  if (hz && BUZZER_ENABLED) {
    ledc_set_freq(MODE, BUZ_TIMER, hz);
    ledc_set_duty(MODE, BUZ_CH, (uint32_t)(BUZZER_DUTY * MAX_DUTY));
  } else {
    ledc_set_duty(MODE, BUZ_CH, 0);
  }
  ledc_update_duty(MODE, BUZ_CH);
}

}  // namespace

void begin() {
  gpio_hold_dis((gpio_num_t)PIN_BUZZER);  // sleep_now() holds it low

  ledc_timer_config_t t = {};
  t.speed_mode = MODE;
  t.duty_resolution = LEDC_TIMER_10_BIT;
  t.clk_cfg = LEDC_AUTO_CLK;

  t.timer_num = DOT_TIMER;
  t.freq_hz = 5000;
  ledc_timer_config(&t);

  t.timer_num = BUZ_TIMER;
  t.freq_hz = 2700;
  ledc_timer_config(&t);

  ledc_channel_config_t c = {};
  c.speed_mode = MODE;
  c.intr_type = LEDC_INTR_DISABLE;
  c.duty = 0;
  c.hpoint = 0;

  c.gpio_num = PIN_BUZZER;
  c.channel = BUZ_CH;
  c.timer_sel = BUZ_TIMER;
  ledc_channel_config(&c);

  // The dots are wired 3V3 -> LED -> resistor -> pin, so invert: duty 0 = pin high = off.
  c.timer_sel = DOT_TIMER;
  c.flags.output_invert = 1;
  for (int i = 0; i < 4; i++) {
    c.gpio_num = PIN_DOT[i];
    c.channel = dot_ch(i);
    ledc_channel_config(&c);
  }
}

void set_scale(float scale) { scale_ = constrain(scale, 0.0f, 1.0f); }

void pulse(uint8_t mask, uint32_t delay_ms, uint16_t in_ms, uint16_t hold_ms, uint16_t out_ms,
           float level) {
  if (n_pulses == sizeof(pulses) / sizeof(pulses[0])) return;
  pulses[n_pulses++] = {mask, millis() + delay_ms, (uint16_t)max<uint16_t>(in_ms, 1), hold_ms,
                        (uint16_t)max<uint16_t>(out_ms, 1), level};
}

void glow(uint8_t mask, float level) {
  glow_mask = mask;
  glow_level = level;
}

void play(const Tone *tones, uint8_t n, bool append) {
  if (!append || !tone_pending) {
    n_tones = tone_idx = 0;
    tone_start = millis();
  } else if (tone_idx > 0) {  // drop the steps already played; tone_start stays with the current one
    memmove(tones_, tones_ + tone_idx, (n_tones - tone_idx) * sizeof(Tone));
    n_tones -= tone_idx;
    tone_idx = 0;
  }
  const uint8_t room = sizeof(tones_) / sizeof(tones_[0]) - n_tones;
  const uint8_t k = min(n, room);
  memcpy(tones_ + n_tones, tones, k * sizeof(Tone));
  n_tones += k;
  tone_pending = n_tones > 0;
}

void tick(uint32_t now) {
  // Dots: the brightest of every pulse and the glow layer, scaled for the room.
  float lvl[4] = {0, 0, 0, 0};
  for (int i = 0; i < 4; i++)
    if (glow_mask & (1 << i)) lvl[i] = glow_level;
  for (uint8_t p = 0; p < n_pulses;) {
    const float e = envelope(pulses[p], now);
    if (e < 0) {
      pulses[p] = pulses[--n_pulses];
      continue;
    }
    for (int i = 0; i < 4; i++)
      if (pulses[p].mask & (1 << i)) lvl[i] = max(lvl[i], e * e * pulses[p].level);  // e^2: even fades
    p++;
  }
  for (int i = 0; i < 4; i++) {
    const uint32_t duty = (uint32_t)(lvl[i] * scale_ * MAX_DUTY + 0.5f);
    if (duty != duty_now[i]) {
      duty_now[i] = duty;
      ledc_set_duty(MODE, dot_ch(i), duty);
      ledc_update_duty(MODE, dot_ch(i));
    }
  }

  // Buzzer: step through the tone list.
  if (tone_pending) {
    while (tone_idx < n_tones && now - tone_start >= tones_[tone_idx].ms) {
      tone_start += tones_[tone_idx].ms;
      tone_idx++;
    }
    if (tone_idx < n_tones) {
      set_tone(tones_[tone_idx].hz);
    } else {
      set_tone(0);
      tone_pending = false;
    }
  }
}

bool busy(uint32_t now) {
  (void)now;
  return n_pulses > 0 || tone_pending;
}

void end() {
  set_tone(0);
  for (int i = 0; i < 4; i++) {
    ledc_stop(MODE, dot_ch(i), 0);
    pinMode(PIN_DOT[i], INPUT);  // floating: no path to GND, so the LED stays dark
  }
  ledc_stop(MODE, BUZ_CH, 0);
  // Hold the buzzer pin low in deep sleep, so a transistor-driven buzzer can't half-turn-on.
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
  gpio_hold_en((gpio_num_t)PIN_BUZZER);
}

}  // namespace fx
