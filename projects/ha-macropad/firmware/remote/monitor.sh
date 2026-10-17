#!/bin/sh
# Show the HK remote's log (build with HK_DEBUG 1). Reconnects by itself when the XIAO resets
# or wakes from sleep, so you can press RESET or a key without restarting this.
cd "$(dirname "$0")" || exit 1
echo "Waiting for the XIAO on USB... (Ctrl+C twice to stop)"
while :; do
  for p in /dev/cu.usbmodem*; do
    if [ -e "$p" ]; then
      echo "--- connected: $p"
      pio device monitor -p "$p" -b 115200 --quiet
      echo "--- disconnected (or the port is busy in another tab), waiting..."
      sleep 2
    fi
  done
  sleep 0.2
done
