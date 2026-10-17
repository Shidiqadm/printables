// ESP-NOW link to the gateway: finds its channel, sends, waits for the ack, and
// receives scene-state dots.
#pragma once

#include <stdint.h>

#include "hk_protocol.h"

namespace radio {

enum Result : uint8_t {
  FAIL,     // no gateway answered
  NO_HA,    // gateway answered, but it isn't connected to Home Assistant
  OK,       // Home Assistant has the event
};

using Idle = void (*)();  // called while waiting, to keep keys and dots running

void start();        // start Wi-Fi in the background (about 50-100 ms)
// scan_allowed = false: if the known gateway doesn't answer, don't search the other channels
// (timer reports, to save battery while the hub is unplugged).
Result send(const hk::Msg &msg, Idle idle, bool scan_allowed = true);
bool pop_dots(uint8_t &mask, uint16_t &ms);

}  // namespace radio
