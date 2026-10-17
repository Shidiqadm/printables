#include "sensors.h"

#include <Arduino.h>
#include <Wire.h>

#include "config.h"

namespace sensors {

namespace {

constexpr uint8_t BH1750_ADDR = 0x23;  // ADDR pin to GND
constexpr uint8_t BH1750_POWER_ON = 0x01;
constexpr uint8_t BH1750_ONE_TIME_H = 0x20;  // 1 lx resolution, then powers itself down
constexpr uint32_t BH1750_MAX_MS = 180;      // datasheet maximum for H-resolution

bool pending = false;
uint32_t t_start = 0;

bool command(uint8_t c) {
  Wire.beginTransmission(BH1750_ADDR);
  Wire.write(c);
  return Wire.endTransmission() == 0;
}

}  // namespace

uint16_t battery_mv() {
  uint32_t sum = 0;
  for (int i = 0; i < 16; i++) sum += analogReadMilliVolts(PIN_BATT);
  const float mv = sum / 16.0f * BATT_DIVIDER * BATT_CAL;
  return mv < BATT_ABSENT_MV ? 0 : (uint16_t)mv;
}

void lux_start() {
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setTimeOut(20);
  pending = command(BH1750_POWER_ON) && command(BH1750_ONE_TIME_H);
  t_start = millis();
}

bool lux_pending() { return pending; }

bool lux_ready(uint32_t now) { return pending && now - t_start >= BH1750_MAX_MS; }

bool lux_read(uint16_t &lux) {
  if (!pending) return false;
  pending = false;
  if (Wire.requestFrom(BH1750_ADDR, (uint8_t)2) != 2) return false;
  uint16_t raw = Wire.read() << 8;
  raw |= Wire.read();
  lux = (uint16_t)((raw * 5UL + 3) / 6);  // raw / 1.2
  return true;
}

}  // namespace sensors
