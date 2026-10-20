#include "accel.h"

#include <Arduino.h>
#include <Wire.h>
#include <math.h>

#include "config.h"

namespace accel {

namespace {

constexpr uint8_t ADDR = 0x53;  // SDO to GND
constexpr uint8_t DEVID_VALUE = 0xE5;

// Registers (ADXL345 datasheet, Rev. G)
constexpr uint8_t DEVID = 0x00, THRESH_TAP = 0x1D, DUR = 0x21, THRESH_ACT = 0x24, THRESH_INACT = 0x25,
                  TIME_INACT = 0x26, ACT_INACT_CTL = 0x27, TAP_AXES = 0x2A, BW_RATE = 0x2C,
                  POWER_CTL = 0x2D, INT_ENABLE = 0x2E, INT_MAP = 0x2F, INT_SOURCE = 0x30,
                  DATA_FORMAT = 0x31, DATAX0 = 0x32;

constexpr uint8_t LOW_POWER = 0x10, RATE_25HZ = 0x08, RATE_100HZ = 0x0A;  // BW_RATE
constexpr uint8_t MEASURE = 0x08, SLEEP = 0x04, WAKEUP_8HZ = 0x00;      // POWER_CTL
constexpr uint8_t INT_INVERT = 0x20, FULL_RES = 0x08, RANGE_8G = 0x02;  // DATA_FORMAT
constexpr uint8_t ACT_AC = 0x80, INACT_AC = 0x08;                       // ACT_INACT_CTL
constexpr uint8_t ACT_X = 0x40, ACT_Y = 0x20, ACT_Z = 0x10, INACT_XYZ = 0x07;
constexpr uint8_t TAP_XYZ = 0x07;
constexpr float G_PER_LSB = 0.0039f;  // full resolution: 3.9 mg per count in every range
constexpr float MG_PER_THRESH = 62.5f;

bool present_ = false;

bool write(uint8_t reg, uint8_t v) {
  Wire.beginTransmission(ADDR);
  Wire.write(reg);
  Wire.write(v);
  return Wire.endTransmission() == 0;
}

bool read_regs(uint8_t reg, uint8_t *buf, uint8_t n) {
  Wire.beginTransmission(ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(ADDR, n) != n) return false;
  for (uint8_t i = 0; i < n; i++) buf[i] = Wire.read();
  return true;
}

uint8_t take_source() {
  uint8_t s = 0;
  read_regs(INT_SOURCE, &s, 1);  // reading it clears the latch, and INT goes high again
  return s & (TAP | ACT | INACT);
}

uint8_t thresh(uint16_t mg) { return (uint8_t)constrain(lroundf(mg / MG_PER_THRESH), 1, 255); }

}  // namespace

uint8_t begin() {
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setTimeOut(20);
  uint8_t id = 0;
  present_ = HK_ACCEL && read_regs(DEVID, &id, 1) && id == DEVID_VALUE;
  if (!present_) return 0;
  // INT active-low: idle high, so the diode to D3 is off. A fresh chip starts active-high,
  // which would hold D3 (key 3) low until this is written.
  write(DATA_FORMAT, INT_INVERT | FULL_RES | RANGE_8G);
  write(INT_MAP, 0);  // everything on INT1
  uint8_t woke = take_source();
  write(INT_ENABLE, 0);
  woke |= take_source();  // anything that latched in between
  delayMicroseconds(50);  // let D3's pull-up recharge the wiring
  return woke;
}

bool present() { return present_; }

bool read(G &g) {
  uint8_t b[6];
  if (!present_ || !read_regs(DATAX0, b, 6)) return false;
  g.x = (int16_t)(b[0] | (b[1] << 8)) * G_PER_LSB;
  g.y = (int16_t)(b[2] | (b[3] << 8)) * G_PER_LSB;
  g.z = (int16_t)(b[4] | (b[5] << 8)) * G_PER_LSB * ACCEL_Z_UP;
  return true;
}

void fast() {
  if (!present_) return;
  write(POWER_CTL, 0);  // standby first (datasheet, when leaving sleep mode)
  write(BW_RATE, RATE_100HZ);
  write(POWER_CTL, MEASURE);
  delay(12);  // first sample
}

void sleep(Watch w) {
  if (!present_) return;
  G g = {0, 0, 1};
  if (w == MOVE) read(g);  // which way up it's lying, before standby
  write(POWER_CTL, 0);
  write(INT_ENABLE, 0);
  take_source();
  if (w == OFF) return;

  if (w == MOVE) {
    // Watch the two axes that are level now: a tilt or a push shows there, but the jolt of
    // a key press (straight down into the table) doesn't.
    const float ax = fabsf(g.x), ay = fabsf(g.y), az = fabsf(g.z);
    const uint8_t level = (az >= ax && az >= ay) ? ACT_X | ACT_Y : (ay >= ax) ? ACT_X | ACT_Z : ACT_Y | ACT_Z;
    write(THRESH_ACT, thresh(ACCEL_MOVE_MG));
    write(ACT_INACT_CTL, ACT_AC | level);  // relative to how it lies when we go to sleep
    write(INT_ENABLE, ACT);
    write(POWER_CTL, MEASURE | SLEEP | WAKEUP_8HZ);  // sleep mode samples at 8 Hz; only ACT runs
  } else {
    write(BW_RATE, LOW_POWER | RATE_25HZ);
    write(THRESH_INACT, thresh(ACCEL_STILL_MG));
    write(TIME_INACT, ACCEL_STILL_S);
    write(ACT_INACT_CTL, INACT_AC | INACT_XYZ);
    write(THRESH_TAP, thresh(ACCEL_JOLT_MG));
    write(DUR, 0xFF);  // up to 160 ms above the threshold still counts: shakes are slow taps
    write(TAP_AXES, TAP_XYZ);
    write(INT_ENABLE, INACT | TAP);
    write(POWER_CTL, MEASURE);
  }
}

void Shake::add(const G &g) {
  const float a[3] = {g.x, g.y, g.z};
  n_++;
  for (int i = 0; i < 3; i++) {
    mean_[i] += (a[i] - mean_[i]) / n_;
    const float d = a[i] - mean_[i];
    const int8_t s = d > SHAKE_G ? 1 : d < -SHAKE_G ? -1 : 0;
    if (s && sign_[i] && s != sign_[i]) rev_++;
    if (s) sign_[i] = s;
  }
}

}  // namespace accel
