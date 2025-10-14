"""UDP: low-latency, fire-and-forget --> great for frequent,
ephemeral GPS pings where an occasional drop is okay."""

import socket
import json
import time
import random

DISPATCHER_HOST = "127.0.0.1"   # change to server IP if remote
DISPATCHER_PORT = 6000          # UDP port (must match listener)
DRIVER_ID = "driver-udp-1"

# Starting position (Long Beach area for example)
lat, lng = 33.7701, -118.1937
status_cycle = ["available", "enroute", "available"]
i = 0

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"[START] Sending UDP updates to {DISPATCHER_HOST}:{DISPATCHER_PORT}")

while True:
    # Generate slightly changing position + speed
    msg = {
        "driver_id": DRIVER_ID,
        "lat": lat + random.uniform(-0.0008, 0.0008),
        "lng": lng + random.uniform(-0.0008, 0.0008),
        "speed_kmh": max(0.0, 35 + random.uniform(-5, 5)),
        "status": status_cycle[i % len(status_cycle)]
    }

    # Send JSON + newline
    sock.sendto((json.dumps(msg) + "\n").encode("utf-8"),
                (DISPATCHER_HOST, DISPATCHER_PORT))

    # Simulate motion and update loop counter
    lat += 0.0009
    lng += 0.0006
    i += 1

    # 1 update per second
    time.sleep(1.0)

