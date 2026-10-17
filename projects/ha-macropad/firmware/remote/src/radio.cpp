#include "radio.h"

#include <Arduino.h>
#include <WiFi.h>
#include <esp_idf_version.h>
#include <esp_now.h>
#include <esp_wifi.h>

#include "config.h"
#include "state.h"

namespace radio {

namespace {

const uint8_t BROADCAST[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
#ifdef HK_GATEWAY_MAC
const uint8_t LOCKED_GW[6] = HK_GATEWAY_MAC;
#endif

// Most routers sit on 1, 6 or 11: try those first.
const uint8_t SCAN_ORDER[] = {1, 6, 11, 2, 3, 4, 5, 7, 8, 9, 10, 12, 13};

volatile bool started = false, ready = false;
uint8_t channel_now = 0;

// Filled in by the ESP-NOW callbacks (Wi-Fi task), read by the main loop.
// Every esp_now_send() gets exactly one send callback. Counting them tells us which
// send a callback belongs to, so a late one can't pass for the current send.
uint32_t sends_out = 0;
volatile uint32_t sends_done = 0;
volatile bool last_delivered = false;
volatile uint8_t wait_seq = 0;
volatile bool ack_got = false;
volatile uint8_t ack_flags = 0, ack_channel = 0;
uint8_t ack_mac[6];
volatile bool dots_got = false;
volatile uint8_t dots_mask = 0, dots_ds = 0;

void on_recv(const uint8_t *mac, const uint8_t *data, int len) {
  if (len < 7 || data[0] != 'H' || data[1] != 'K' || data[2] != hk::VERSION) return;
#ifdef HK_GATEWAY_MAC
  if (memcmp(mac, LOCKED_GW, 6) != 0) return;
#endif
  if (data[3] == hk::T_ACK && data[4] == wait_seq) {
    memcpy(ack_mac, mac, 6);
    ack_flags = data[5];
    ack_channel = data[6];
    ack_got = true;
  } else if (data[3] == hk::T_DOTS) {
    dots_mask = data[5];
    dots_ds = data[6];
    dots_got = true;
  }
}

#if ESP_IDF_VERSION_MAJOR >= 5
void recv_cb(const esp_now_recv_info_t *info, const uint8_t *data, int len) { on_recv(info->src_addr, data, len); }
#else
void recv_cb(const uint8_t *mac, const uint8_t *data, int len) { on_recv(mac, data, len); }
#endif

#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 5, 0)
void sent_cb(const esp_now_send_info_t *, esp_now_send_status_t status) {
#else
void sent_cb(const uint8_t *, esp_now_send_status_t status) {
#endif
  last_delivered = status == ESP_NOW_SEND_SUCCESS;
  sends_done = sends_done + 1;
}

void add_peer(const uint8_t *mac) {
  if (esp_now_is_peer_exist(mac)) return;
  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, mac, 6);
  peer.channel = 0;  // whatever channel the radio is on
  peer.ifidx = WIFI_IF_STA;
  peer.encrypt = false;
  esp_now_add_peer(&peer);
}

void set_channel(uint8_t ch) {
  if (ch == channel_now || ch < 1 || ch > 13) return;
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(ch, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(false);
  channel_now = ch;
}

void init_task(void *) {
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  esp_wifi_set_ps(WIFI_PS_NONE);
  if (esp_now_init() == ESP_OK) {
    esp_now_register_recv_cb(recv_cb);
    esp_now_register_send_cb(sent_cb);
    add_peer(BROADCAST);
    if (rtc.gw_known) {
      add_peer(rtc.gw_mac);
      set_channel(rtc.gw_channel);
    }
    ready = true;
  }
  LOG("radio ready=%d after %lu ms\n", ready, millis());
  vTaskDelete(nullptr);
}

bool wait(volatile bool &flag, uint32_t ms, Idle idle) {
  const uint32_t t0 = millis();
  while (!flag && millis() - t0 < ms) idle();
  return flag;
}

bool send_raw(const uint8_t *mac, const hk::Msg &msg) {
  if (esp_now_send(mac, (const uint8_t *)&msg, sizeof(msg)) != ESP_OK) return false;
  sends_out++;
  return true;
}

// Wait until every send so far has had its callback (MAC-level retries can take a while).
bool drain(Idle idle) {
  const uint32_t t0 = millis();
  while (sends_done != sends_out && millis() - t0 < 200) idle();
  return sends_done == sends_out;
}

// 2 = acked, 1 = the gateway's radio took it but no ack came, 0 = not delivered.
int unicast(const hk::Msg &msg, Idle idle) {
  if (!drain(idle)) return 0;
  ack_got = false;
  if (!send_raw(rtc.gw_mac, msg)) return 0;
  if (!drain(idle) || !last_delivered) return 0;
  return wait(ack_got, ACK_TIMEOUT_MS, idle) ? 2 : 1;
}

// Broadcast on each channel until a gateway answers, and remember it.
bool scan(const hk::Msg &msg, Idle idle) {
  for (uint8_t ch : SCAN_ORDER) {
    set_channel(ch);
    ack_got = false;
    send_raw(BROADCAST, msg);
    if (wait(ack_got, SCAN_WAIT_MS, idle)) {
      memcpy(rtc.gw_mac, ack_mac, 6);
      // Trust the channel the gateway reports: a neighbouring channel can leak through.
      rtc.gw_channel = (ack_channel >= 1 && ack_channel <= 13) ? ack_channel : ch;
      rtc.gw_known = true;
      add_peer(rtc.gw_mac);
      set_channel(rtc.gw_channel);
      LOG("gateway on channel %u\n", rtc.gw_channel);
      return true;
    }
  }
  return false;
}

}  // namespace

void start() {
  if (started) return;
  started = true;
  xTaskCreate(init_task, "hk_radio", 8192, nullptr, 1, nullptr);
}

Result send(const hk::Msg &msg, Idle idle, bool scan_allowed) {
  start();
  const uint32_t t0 = millis();
  while (!ready && millis() - t0 < 2000) idle();
  if (!ready) return FAIL;

  wait_seq = msg.seq;
  bool acked = false, heard = false;
  if (rtc.gw_known) {
    set_channel(rtc.gw_channel);
    for (int attempt = 0; attempt < SEND_ATTEMPTS && !acked; attempt++) {
      const int r = unicast(msg, idle);
      acked = r == 2;
      heard = heard || r == 1;
    }
  }
  // Never delivered: the gateway is new to us, or the router moved it to another channel.
  if (!acked && !heard && (scan_allowed || !rtc.gw_known)) acked = scan(msg, idle);
  if (!acked) {
    LOG("no ack for seq %u\n", msg.seq);
    return FAIL;
  }
  rtc.dots_feature = ack_flags & hk::A_DOTS;
  return (ack_flags & hk::A_HA) ? OK : NO_HA;
}

bool pop_dots(uint8_t &mask, uint16_t &ms) {
  if (!dots_got) return false;
  dots_got = false;
  mask = dots_mask;
  ms = dots_ds ? dots_ds * 100 : DOTS_SHOW_MS;
  return true;
}

}  // namespace radio
