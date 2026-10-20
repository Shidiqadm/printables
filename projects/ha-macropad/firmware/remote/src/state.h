// State kept in RTC memory across deep sleep. A cold boot (battery connected, reset,
// new firmware) starts it again from zero.
#pragma once

#include <stdint.h>

struct RtcState {
  uint32_t magic;

  uint8_t seq;            // message counter (random start after a cold boot)
  bool gw_known;          // gateway MAC and channel found
  uint8_t gw_mac[6];
  uint8_t gw_channel;
  bool dots_feature;      // the gateway said Home Assistant sends scene-state dots

  bool off;               // keys switched off (key 4 held 5 s)
  bool shutdown;          // battery empty: sleeping until it's charged
  uint8_t stuck;          // key pins held down when we last went to sleep

  uint16_t batt_mv;       // last measurement (0 = divider not fitted)
  bool lux_valid;
  uint16_t lux;           // last BH1750 reading
  uint32_t lux_read_s;

  uint16_t sent_mv;       // values the gateway last confirmed
  uint16_t sent_lux;
  uint32_t sent_s;
  uint32_t report_failed_s;  // last timer report nobody answered (0 = none)

  bool watch_move;        // accelerometer: lying still, so wake on a move (else: in the hand)
  uint32_t rest_s;        // when it was last put down level and face up (0 = not lying so)
};

extern RtcState rtc;

constexpr uint32_t RTC_MAGIC = 0x484B0108;  // 'HK' v1.8: change to reset state on update
