// HK ESP-NOW protocol, version 1.
//
// The gateway (../../gateway/hk/hk-gateway.yaml) reads and writes the same byte offsets
// in its lambdas, so change both together. Both ends are little-endian RISC-V.
#pragma once

#include <stdint.h>

namespace hk {

constexpr uint8_t VERSION = 1;

enum Type : uint8_t {
  T_PRESS = 1,    // remote -> gateway: a key gesture
  T_REPORT = 2,   // remote -> gateway: light and battery (timer wake)
  T_STATUS = 3,   // remote -> gateway: boot / on / off / shutdown
  T_MOTION = 4,   // remote -> gateway: picked up, shaken or flipped (ADXL345)
  T_ACK = 0x81,   // gateway -> remote: got it
  T_DOTS = 0x82,  // gateway -> remote: light these dots (scene state from Home Assistant)
};

// Single keys, then the two-key combos. 1+2 can't exist: the diodes make it read as key 4.
enum Key : uint8_t { K_NONE = 0, K1 = 1, K2 = 2, K3 = 3, K4 = 4, K13 = 5, K23 = 6, K34 = 7 };

enum Press : uint8_t { P_SINGLE = 1, P_DOUBLE = 2, P_LONG = 3 };

enum Status : uint8_t { S_BOOT = 1, S_ON = 2, S_OFF = 3, S_SHUTDOWN = 4 };

enum Motion : uint8_t { M_PICKUP = 1, M_SHAKE = 2, M_FLIP = 3 };

enum Flag : uint8_t {
  F_OFF = 1,       // keys switched off (key 4 held 5 s)
  F_BATT_LOW = 2,  // below BATT_WARN_MV
};

enum AckFlag : uint8_t {
  A_HA = 1,    // the gateway is connected to Home Assistant, so the event went through
  A_DOTS = 2,  // Home Assistant uses scene-state dots: listen for a T_DOTS after this ack
};

constexpr uint16_t LUX_UNKNOWN = 0xFFFF;

#pragma pack(push, 1)

struct Msg {           // remote -> gateway, 13 bytes
  uint8_t magic[2];    // 0-1  'H' 'K'
  uint8_t version;     // 2
  uint8_t type;        // 3    T_PRESS, T_REPORT, T_STATUS or T_MOTION
  uint8_t seq;         // 4    the same for retries, so the gateway can drop repeats
  uint8_t remote;      // 5    HK_REMOTE_ID
  uint8_t key;         // 6    Key (T_PRESS)
  uint8_t value;       // 7    Press (T_PRESS), Status (T_STATUS) or Motion (T_MOTION)
  uint16_t batt_mv;    // 8-9  0 = not measured
  uint16_t lux;        // 10-11 LUX_UNKNOWN = no reading
  uint8_t flags;       // 12   Flag bits
};

struct Ack {           // gateway -> remote, 7 bytes
  uint8_t magic[2];    // 0-1
  uint8_t version;     // 2
  uint8_t type;        // 3    T_ACK
  uint8_t seq;         // 4    echo of Msg::seq
  uint8_t flags;       // 5    AckFlag bits
  uint8_t channel;     // 6    the gateway's Wi-Fi channel
};

struct Dots {          // gateway -> remote, 7 bytes
  uint8_t magic[2];    // 0-1
  uint8_t version;     // 2
  uint8_t type;        // 3    T_DOTS
  uint8_t seq;         // 4
  uint8_t mask;        // 5    bit 0 = key 1 ... bit 3 = key 4; 0 = none
  uint8_t show_ds;     // 6    how long, in 0.1 s (0 = DOTS_SHOW_MS)
};

#pragma pack(pop)

static_assert(sizeof(Msg) == 13, "Msg layout");
static_assert(sizeof(Ack) == 7, "Ack layout");
static_assert(sizeof(Dots) == 7, "Dots layout");

}  // namespace hk
