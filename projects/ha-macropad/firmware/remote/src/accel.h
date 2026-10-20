// ADXL345 accelerometer (GY-291 module) on the I2C bus (D4 / D5), HK-22 only.
//
// It watches for motion by itself while the chip deep-sleeps, and pulls D3 low through a
// diode when something happens. D3 is also key 3, so while we're awake its interrupt is off
// and D3 belongs to the key alone. Nothing here runs if no ADXL345 answers.
#pragma once

#include <stdint.h>

namespace accel {

// What woke us (INT_SOURCE bits)
constexpr uint8_t TAP = 0x40;    // a hard jolt while in the hand: maybe a shake
constexpr uint8_t ACT = 0x10;    // moved after lying still: maybe picked up
constexpr uint8_t INACT = 0x08;  // held or lying still for ACCEL_STILL_S

// What to watch for in deep sleep
enum Watch : uint8_t {
  OFF,    // standby, 0.1 uA (switched off, battery empty, or key 3 stuck)
  MOVE,   // lying still: wake on a tilt or a push (ACT)
  STILL,  // in the hand: wake when it's still again (INACT), or on a hard jolt (TAP)
};

struct G {
  float x, y, z;  // in g; z points up out of the deck
};

// At wake, before the keys are read: finds the chip, reads and clears what it saw, and turns
// its interrupt off while we're awake. Returns TAP / ACT / INACT bits (0: none, or no chip).
uint8_t begin();
bool present();
bool read(G &g);
void fast();  // 100 Hz sampling, to watch a gesture while awake
void sleep(Watch w);

// Counts direction changes of hard shaking: the gravity part (the running mean) is taken
// away, and an axis counts when it swings past SHAKE_G one way after the other.
class Shake {
 public:
  void add(const G &g);
  uint8_t reversals() const { return rev_; }

 private:
  float mean_[3] = {0, 0, 0};
  int8_t sign_[3] = {0, 0, 0};
  uint16_t n_ = 0;
  uint8_t rev_ = 0;
};

}  // namespace accel
