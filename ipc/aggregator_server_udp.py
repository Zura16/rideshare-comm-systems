import socket
import json

HOST = "0.0.0.0"   # listen on all network interfaces
PORT = 6000        # must match driver_udp.py
print(f"[BOOT] UDP listener on {HOST}:{PORT}")

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

driver_state = {}

while True:
    # Receive data
    data, addr = sock.recvfrom(4096)
    try:
        msg = json.loads(data.decode("utf-8").strip())
        driver_id = msg.get("driver_id", "unknown")
        driver_state[driver_id] = msg
        print(f"[UPDATE from {addr}] {driver_id}: "
              f"({msg['lat']:.5f}, {msg['lng']:.5f}) "
              f"{msg['speed_kmh']:.1f} km/h [{msg['status']}]")
    except json.JSONDecodeError:
        print(f"[WARN] Could not parse message from {addr}")