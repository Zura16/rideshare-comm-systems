import socket
import threading
import json
from datetime import datetime

HOST = "0.0.0.0"  # listen on all interfaces (use "127.0.0.1" for localhost only)
PORT = 5001

# Keeps the latest state for each driver_id
driver_state = {}
driver_state_lock = threading.Lock()


def handle_client(conn, addr):
    print(f"[CONNECT] {addr} connected")
    buffer = b""
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buffer += chunk
            # newline-delimited JSON (NDJSON)
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                if not line.strip():
                    continue
                try:
                    msg = json.loads(line.decode("utf-8"))
                    # expected: {"driver_id": "...", "lat": float, "lng": float, "speed_kmh": float, "status": "available|enroute|off"}
                    driver_id = msg.get("driver_id", "unknown")
                    with driver_state_lock:
                        driver_state[driver_id] = {
                            "lat": msg.get("lat"),
                            "lng": msg.get("lng"),
                            "speed_kmh": msg.get("speed_kmh"),
                            "status": msg.get("status"),
                            "ts": datetime.utcnow().isoformat() + "Z"
                        }
                    # minimal server-side ack (optional)
                    ack = {"ok": True, "recv_ts": datetime.utcnow().isoformat() + "Z"}
                    conn.sendall((json.dumps(ack) + "\n").encode("utf-8"))
                except json.JSONDecodeError as e:
                    print(f"[WARN] Bad JSON from {addr}: {e}")
    finally:
        print(f"[DISCONNECT] {addr} disconnected")
        conn.close()


def printer():
    """Periodically prints the latest state of all drivers (for demo)."""
    import time
    while True:
        time.sleep(3)
        with driver_state_lock:
            if driver_state:
                print("\n=== Latest Driver States ===")
                for did, state in driver_state.items():
                    print(f"{did}: {state}")
            else:
                print("\n(No drivers connected yet)")


def main():
    print(f"[BOOT] Dispatcher listening on {HOST}:{PORT}")
    threading.Thread(target=printer, daemon=True).start()
    try: 
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen()
            while True:
                conn, addr = s.accept()
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt: #
        print("\n[SHUTDOWN] Server was interrupted.")

if __name__ == "__main__":
    main()

