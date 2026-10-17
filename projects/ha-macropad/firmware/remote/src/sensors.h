// Battery voltage (divider on D2) and the BH1750 light sensor.
#pragma once

#include <stdint.h>

namespace sensors {

uint16_t battery_mv();  // 0 = divider not fitted

void lux_start();                  // one high-resolution reading, ready about 180 ms later
bool lux_pending();                // a reading was started and not yet read
bool lux_ready(uint32_t now);
bool lux_read(uint16_t &lux);      // once per start; false if the sensor didn't answer

}  // namespace sensors
