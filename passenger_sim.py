import requests
import time
import random
import sys

SERVER_URL = "http://localhost:5000/api/passenger/request"
LONG_BEACH_COORDS = (33.7838, -118.1141)

def generate_passenger(id):
    # Generate random coordinates around Long Beach
    lat = LONG_BEACH_COORDS[0] + random.uniform(-0.02, 0.02)
    lon = LONG_BEACH_COORDS[1] + random.uniform(-0.02, 0.02)
    
    # Generate random destination
    dest_lat = LONG_BEACH_COORDS[0] + random.uniform(-0.02, 0.02)
    dest_lon = LONG_BEACH_COORDS[1] + random.uniform(-0.02, 0.02)
    
    payload = {
        "passenger_id": f"Passenger-{id}",
        "lat": lat,
        "lon": lon,
        "dest_lat": dest_lat,
        "dest_lon": dest_lon,
        "status": "waiting"
    }
    
    try:
        response = requests.post(SERVER_URL, json=payload)
        if response.status_code == 200:
            print(f"Successfully requested ride for Passenger-{id} at [{lat:.4f}, {lon:.4f}] → [{dest_lat:.4f}, {dest_lon:.4f}]")
        else:
            print(f"Failed to request ride: {response.text}")
    except Exception as e:
        print(f"Error connecting to server: {e}")

def main():
    print("Starting Passenger Simulation...")
    print(f"Target Server: {SERVER_URL}")
    
    passenger_count = 0
    MAX_PASSENGERS = 10  # limit the total number of simulated passengers
    
    try:
        while passenger_count < MAX_PASSENGERS:
            passenger_count += 1
            generate_passenger(passenger_count)
            
            # Wait for a random interval before next passenger
            sleep_time = random.uniform(8, 12)
            time.time()  # just to keep import usage, not needed
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    finally:
        print(f"Simulation completed: generated {passenger_count} passengers (max {MAX_PASSENGERS}).")

if __name__ == "__main__":
    main()
