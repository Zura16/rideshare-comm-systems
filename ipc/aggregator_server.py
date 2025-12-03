import socket
import threading
import json
from datetime import datetime

HOST = "0.0.0.0"  # listen on all interfaces (use "127.0.0.1" for localhost only)
PORT = 5001

# Keeps the latest state for each driver_id
driver_state = {}
driver_state_lock = threading.Lock()

def find_and_book_driver():
    """Find closest available driver and mark as booked"""
    with driver_state_lock:
        available = [(did, state) for did, state in driver_state.items() 
                    if state.get('status') == 'available' and state.get('lat') is not None]
        
        if not available:
            return None
        
        # Get first available driver
        driver_id, state = available[0]
        
        # Change status to booked
        driver_state[driver_id]['status'] = 'booked'
        
        print(f"\n[MATCH] ✓ Assigned {driver_id} to passenger")
        print(f"        Status changed: available → booked")
        print(f"        Location: ({state['lat']:.4f}, {state['lng']:.4f})\n")
        
        return {
            "driver_id": driver_id,
            "lat": state['lat'],
            "lng": state['lng'],
            "speed_kmh": state['speed_kmh']
        }

def find_nearest_driver():
    """Find closest available driver"""
    with driver_state_lock:
        available = {did: state for did, state in driver_state.items() 
                    if state.get('status') == 'available' and state.get('lat') is not None}
        
        if not available:
            return None
        
        # Return first available (in real system, calculate distance)
        driver_id = list(available.keys())[0]
        return {
            "driver_id": driver_id,
            "driver_lat": available[driver_id]['lat'],
            "driver_lng": available[driver_id]['lng'],
            "eta": 5  # Mock ETA
        }

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
                    
                    # DEBUG
                    print(f"[DEBUG] Message type: {msg.get('type', msg.get('event_type'))}")
                    
                    # Handle ride request FIRST
                    if msg.get("type") == "ride_request":
                        print("[DEBUG] Processing ride request...")
                        driver = find_and_book_driver()
                        if driver:
                            response = {
                                "status": "assigned",
                                "driver_id": driver['driver_id'],
                                "driver_lat": driver['lat'],
                                "driver_lng": driver['lng']
                            }
                        else:
                            response = {"status": "no_drivers_available"}
                        
                        conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
                        continue
                    
                    # Handle Lamport timestamp GPS updates
                    if "event_type" in msg and msg["event_type"] == "gps_update":
                        gps_data = msg.get("data", {})
                        driver_id = gps_data.get("driver_id", "unknown")
                        lamport_time = msg.get("lamport_time", 0)
                        
                        with driver_state_lock:
                            driver_state[driver_id] = {
                                "lat": gps_data.get("lat"),
                                "lng": gps_data.get("lng"),
                                "speed_kmh": gps_data.get("speed_kmh"),
                                "status": gps_data.get("status"),
                                "lamport_time": lamport_time,
                                "ts": datetime.utcnow().isoformat() + "Z"
                            }
                        
                        ack = {
                            "ok": True,
                            "lamport_time": lamport_time,
                            "recv_ts": datetime.utcnow().isoformat() + "Z"
                        }
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

