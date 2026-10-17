#!/bin/sh
# Flash the HK remote and open its log. Works on whichever USB port the XIAO shows up on.
# If the XIAO is asleep: unplug it, hold BOOT, plug it in, release BOOT.
cd "$(dirname "$0")" || exit 1

wait_port() {
  while :; do
    for p in /dev/cu.usbmodem*; do
      [ -e "$p" ] && { echo "$p"; return; }
    done
    sleep 0.2
  done
}

echo "Waiting for the XIAO on USB (asleep? unplug, hold BOOT, plug in, release BOOT)..."
port=$(wait_port)
echo "Found $port, flashing..."
pio run -t upload --upload-port "$port" || exit 1
sleep 1
port=$(wait_port)
echo "Opening the log on $port (Ctrl+C to stop)"
pio device monitor -p "$port" -b 115200
