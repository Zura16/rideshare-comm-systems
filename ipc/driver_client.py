import socket
import json
import random
import time

DISPATCHER_HOST = "127.0.0.1"  # change to server IP if running across machines
DISPATCHER_PORT = 5000

def jitter(val, spread=0.0008):
    return val + random.uniform(-spread, spread)

def simulate_driver(driver_id, start_lat, start_lng):
    status_cycle = ["available", "enroute", "available"]
    i = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((DISPATCHER_HOST, DISPATCHER_PORT))
        print(f"[CONNECTED] {driver_id} -> dispatcher")
        lat, lng = start_lat, start_lng
        speed = 35.0
        while True:
            status = status_cycle[i % len(status_cycle)]
            msg = {
                "driver_id": driver_id,
                "lat": jitter(lat),
                "lng": jitter(lng),
                "speed_kmh": max(0.0, speed + random.uniform(-5, 5)),
                "status": status
            }
            s.sendall((json.dumps(msg) + "\n").encode("utf-8"))
            # optional: read small ACK
            ack_line = s.makefile().readline().strip()
            if ack_line:
                try:
                    ack = json.loads(ack_line)
                    # print(f"[ACK] {driver_id} {ack}")
                except json.JSONDecodeError:
                    pass
            # simulate movement a bit
            lat += 0.0009
            lng += 0.0006
            i += 1
            time.sleep(1.0)

if __name__ == "__main__":
    # Example: simulate a driver
    simulate_driver(driver_id="driver-101", start_lat=33.7701, start_lng=-118.1937)

