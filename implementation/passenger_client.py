import socket
import json
import sys

DISPATCHER_HOST = "127.0.0.1"
DISPATCHER_PORT = 5001

def request_ride(passenger_id):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((DISPATCHER_HOST, DISPATCHER_PORT))
            
            request = {
                "type": "ride_request",
                "passenger_id": passenger_id
            }
            
            s.sendall((json.dumps(request) + "\n").encode("utf-8"))
            print(f"[{passenger_id}] 🚗 Requesting ride...")
            
            response = s.makefile().readline().strip()
            if response:
                data = json.loads(response)
                if data.get("status") == "assigned":
                    print(f"\n✓ Driver assigned!")
                    print(f"   Driver: {data.get('driver_id')}")
                    print(f"   Location: ({data.get('driver_lat'):.4f}, {data.get('driver_lng'):.4f})")
                    print(f"   Status: BOOKED\n")
                else:
                    print(f"\n✗ No drivers available\n")
    
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    passenger_id = sys.argv[1] if len(sys.argv) > 1 else "passenger-501"
    request_ride(passenger_id)
