#include "sensors.h"

#include <Arduino.h>

#include "config.h"

namespace sensors {

uint16_t battery_mv() {
  uint32_t sum = 0;
  for (int i = 0; i < 16; i++) sum += analogReadMilliVolts(PIN_BATT);
  const float mv = sum / 16.0f * BATT_DIVIDER * BATT_CAL;
  return mv < BATT_ABSENT_MV ? 0 : (uint16_t)mv;
}

}  // namespace sensors
