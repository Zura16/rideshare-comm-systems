"""
Vehicle peer runner that uses P2PNode to exchange location/route updates with nearby peers.
"""

import asyncio
import random
import time
import math
import requests
from typing import Dict, Any

from p2p.p2p_node import P2PNode
from p2p.ricart_agrawala import RicartAgrawalaMutex

# Flask server URLs
FLASK_SERVER_URL = "http://localhost:5000/api/vehicle/position"
RIDE_CHECK_URL = "http://localhost:5000/api/ride/check"
RIDE_PICKUP_URL = "http://localhost:5000/api/ride/pickup"
RIDE_DROPOFF_URL = "http://localhost:5000/api/ride/dropoff"


def send_position_to_server(vehicle_id: str, lat: float, lon: float) -> None:
    """Send vehicle position to Flask server via HTTP POST."""
    try:
        response = requests.post(
            FLASK_SERVER_URL,
            json={"vehicle_id": vehicle_id, "lat": lat, "lon": lon},
            timeout=1,
        )
        if response.status_code == 200:
            print(f"[{vehicle_id}] Position sent to server: ({lat}, {lon})")
        else:
            print(
                f"[{vehicle_id}] Failed to send position: "
                f"{response.status_code} {response.text}"
            )
    except requests.exceptions.RequestException as e:
        print(f"[{vehicle_id}] Error sending position to server: {e}")


async def cs_worker(node_id: str, mutex: RicartAgrawalaMutex) -> None:
    """Periodically test Ricart–Agrawala critical section logic."""
    while True:
        await asyncio.sleep(3)
        print(f"[{node_id}] requesting CS...")

        await mutex.request_cs("intersection-A")
        print(f" >>> [{node_id}] ENTER CS")

        await asyncio.sleep(2)

        print(f" <<< [{node_id}] EXIT CS")
        await mutex.release_cs("intersection-A")


def check_ride_assignment(vehicle_id: str) -> Dict[str, Any]:
    """
    Check if vehicle has an assigned ride.

    Returns a dict, e.g.
    {
        "assigned": bool,
        "passenger_id": str,
        "passenger_lat": float,
        "passenger_lon": float,
        "dest_lat": float | None,
        "dest_lon": float | None,
        "status": "en_route_pickup" | "en_route_dest" | ...
    }
    """
    try:
        response = requests.get(f"{RIDE_CHECK_URL}/{vehicle_id}", timeout=1)
        if response.status_code == 200:
            data = response.json() or {}
            return data
        else:
            print(f"[{vehicle_id}] ride check failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[{vehicle_id}] ride check error: {e}")
    return {}  # Fallback: no assignment


def mark_pickup(passenger_id: str) -> None:
    """Notify server that pickup has occurred."""
    try:
        r = requests.post(
            RIDE_PICKUP_URL,
            json={"passenger_id": passenger_id},
            timeout=1,
        )
        print(f"[pickup] {passenger_id}: {r.status_code} {r.text}")
    except requests.exceptions.RequestException as e:
        print(f"[pickup] error for {passenger_id}: {e}")


def complete_ride(passenger_id: str) -> None:
    """Notify server that dropoff has completed."""
    try:
        r = requests.post(
            RIDE_DROPOFF_URL,
            json={"passenger_id": passenger_id},
            timeout=1,
        )
        print(f"[dropoff] {passenger_id}: {r.status_code} {r.text}")
    except requests.exceptions.RequestException as e:
        print(f"[dropoff] error for {passenger_id}: {e}")


def calculate_direction(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
    step_size: float = 0.0005,
):
    """
    Calculate movement step toward destination.

    Returns (new_lat, new_lon, arrived_bool).
    """
    dlat = to_lat - from_lat
    dlon = to_lon - from_lon
    distance = math.sqrt(dlat**2 + dlon**2)

    if distance < step_size:
        # Close enough — snap to target
        return to_lat, to_lon, True

    new_lat = from_lat + (dlat / distance) * step_size
    new_lon = from_lon + (dlon / distance) * step_size
    return new_lat, new_lon, False


async def run_vehicle(
    node_id: str,
    host: str = "0.0.0.0",
    port: int = 0,
    mgroup: str = "224.0.0.250",
    mport: int = 50000,
) -> None:
    """Main vehicle loop: P2P + ride navigation."""
    node = P2PNode(
        node_id=node_id,
        listen_host=host,
        listen_port=port,
        mcast_group=mgroup,
        mcast_port=mport,
    )

    def on_msg(msg: Dict[str, Any]) -> None:
        mtype = msg.get("type")
        if mtype == "location_update":
            print(f"[{node_id}] Location from {msg.get('from')}: {msg.get('payload')}")
        elif mtype == "route_update":
            print(f"[{node_id}] Route from {msg.get('from')}: {msg.get('payload')}")
        else:
            print(f"[{node_id}] Message: {msg}")

    node.on_message(on_msg)
    await node.start()

    mutex = RicartAgrawalaMutex(node)
    asyncio.create_task(cs_worker(node_id, mutex))

    # Start somewhere near Long Beach
    lat, lon = 33.7838, -118.1141

    assigned_passenger = None
    current_phase = None  # "pickup" or "dropoff"
    destination = None    # (dest_lat, dest_lon) or None

    try:
        while True:
            # --- Check ride status from server ---
            ride_data = check_ride_assignment(node_id) or {}

            if ride_data.get("assigned"):
                passenger_id = ride_data["passenger_id"]
                p_lat = ride_data["passenger_lat"]
                p_lon = ride_data["passenger_lon"]
                dest_lat = ride_data.get("dest_lat")
                dest_lon = ride_data.get("dest_lon")
                ride_status = ride_data.get("status", "en_route_pickup")

                # New assignment or changed passenger
                if assigned_passenger != passenger_id:
                    assigned_passenger = passenger_id
                    current_phase = "pickup"
                    destination = (dest_lat, dest_lon)
                    print(f"[{node_id}] Assigned to passenger {passenger_id}")
                    print(
                        f"    pickup @ ({p_lat}, {p_lon}), "
                        f"dest=({dest_lat}, {dest_lon})"
                    )

                # --- Phase 1: navigate to passenger for pickup ---
                if ride_status == "en_route_pickup" or current_phase == "pickup":
                    lat, lon, arrived = calculate_direction(lat, lon, p_lat, p_lon)
                    if arrived:
                        print(f"[{node_id}] Arrived for pickup: {passenger_id}")
                        mark_pickup(passenger_id)
                        current_phase = "dropoff"

                # --- Phase 2: navigate to destination ---
                elif ride_status == "en_route_dest" or current_phase == "dropoff":
                    if destination and destination[0] is not None and destination[1] is not None:
                        dest_lat, dest_lon = destination
                        lat, lon, arrived = calculate_direction(
                            lat, lon, dest_lat, dest_lon
                        )
                        if arrived:
                            print(f"[{node_id}] Arrived at destination: {passenger_id}")
                            complete_ride(passenger_id)
                            assigned_passenger = None
                            current_phase = None
                            destination = None
                    else:
                        # No destination info yet, just drift slightly
                        lat += (random.random() - 0.5) * 0.0002
                        lon += (random.random() - 0.5) * 0.0002

            else:
                # No ride — random movement
                if assigned_passenger:
                    print(f"[{node_id}] No longer assigned, returning to idle.")
                assigned_passenger = None
                current_phase = None
                destination = None
                lat += (random.random() - 0.5) * 0.0005
                lon += (random.random() - 0.5) * 0.0005

            payload = {
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "ts": time.time(),
            }

            # Broadcast to P2P peers
            await node.broadcast({"type": "location_update", "payload": payload})

            # Send to Flask server (for frontend map)
            send_position_to_server(node_id, payload["lat"], payload["lon"])

            await asyncio.sleep(1.5)

    except KeyboardInterrupt:
        print(f"[{node_id}] Shutting down vehicle loop...")
    finally:
        await node.stop()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vehicle peer")
    parser.add_argument("--id", required=True)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--mgroup", default="224.0.0.250")
    parser.add_argument("--mport", type=int, default=50000)
    args = parser.parse_args()

    asyncio.run(
        run_vehicle(
            args.id,
            host=args.host,
            port=args.port,
            mgroup=args.mgroup,
            mport=args.mport,
        )
    )
