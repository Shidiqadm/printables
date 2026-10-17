// Key reading and gesture detection: single, double and long presses, two-key combos,
// and the 5 s hold of key 4.
#pragma once

#include <stdint.h>

namespace keys {

// Pin bits used everywhere below: bit 0 = D0 (GPIO2), bit 1 = D1 (GPIO3), bit 2 = D3 (GPIO5).
constexpr uint8_t PIN_A = 1, PIN_B = 2, PIN_C = 4, ALL = 7;

constexpr uint8_t TOGGLE = 10;  // Gesture::kind for the 5 s hold of key 4

struct Gesture {
  uint8_t key;   // hk::Key
  uint8_t kind;  // hk::Press, or TOGGLE
};

// Set up the pins. `ignore` holds the pins of stuck keys: they are skipped until released.
void begin(uint8_t ignore);

// Start with the key that woke the chip. It may already be released by the time we boot.
void seed(uint8_t wake_pins);

void tick(uint32_t now);
bool pop(Gesture &g);
bool idle();             // no press in progress and nothing queued
bool armed();            // key 4 held past the long-press time (on its way to 5 s)
bool stuck(uint32_t now);

uint8_t raw();             // pins that read low right now, ignored ones included
uint8_t dots(uint8_t key); // dot mask (bit 0 = key 1) for a key or combo
uint64_t gpio_mask(uint8_t pins);
uint8_t from_gpio_mask(uint64_t mask);

}  // namespace keys
