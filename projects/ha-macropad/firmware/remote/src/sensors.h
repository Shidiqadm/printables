// Battery voltage (divider on D2).
#pragma once

#include <stdint.h>

namespace sensors {

uint16_t battery_mv();  // 0 = divider not fitted

}  // namespace sensors
