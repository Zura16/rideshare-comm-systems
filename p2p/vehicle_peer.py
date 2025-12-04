"""
Vehicle peer runner that uses P2PNode to exchange location/route updates with nearby peers.
"""
import asyncio
import random
import time
import requests
from typing import Dict, Any

from p2p.p2p_node import P2PNode
from p2p.ricart_agrawala import RicartAgrawalaMutex

# Flask server URL for sending position updates
FLASK_SERVER_URL = "http://localhost:5000/api/vehicle/position"


def send_position_to_server(vehicle_id: str, lat: float, lon: float):
    """Send vehicle position to Flask server via HTTP POST"""
    try:
        response = requests.post(
            FLASK_SERVER_URL,
            json={
                "vehicle_id": vehicle_id,
                "lat": lat,
                "lon": lon
            },
            timeout=1
        )
        if response.status_code == 200:
            print(f"[{vehicle_id}] Position sent to server: ({lat}, {lon})")
        else:
            print(f"[{vehicle_id}] Failed to send position: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[{vehicle_id}] Error sending position to server: {e}")


async def cs_worker(node_id: str, mutex: RicartAgrawalaMutex):
    """Periodically test Ricart–Agrawala critical section logic."""
    while True:
        await asyncio.sleep(3)  # wait between CS attempts
        print(f"[{node_id}] requesting CS...")

        await mutex.request_cs("intersection-A")
        print(f" >>> [{node_id}] ENTER CS")

        await asyncio.sleep(2)  # simulate work

        print(f" <<< [{node_id}] EXIT CS")
        await mutex.release_cs("intersection-A")


async def run_vehicle(node_id: str, host: str = "0.0.0.0", port: int = 0, mgroup: str = "224.0.0.250", mport: int = 50000) -> None:
    node = P2PNode(node_id=node_id, listen_host=host, listen_port=port, mcast_group=mgroup, mcast_port=mport)

    def on_msg(msg: Dict[str, Any]) -> None:
        mtype = msg.get('type')
        if mtype == 'location_update':
            print(f"[{node_id}] Location from {msg.get('from')}: {msg.get('payload')}")
        elif mtype == 'route_update':
            print(f"[{node_id}] Route from {msg.get('from')}: {msg.get('payload')}")
        else:
            print(f"[{node_id}] Message: {msg}")

    node.on_message(on_msg)
    await node.start()

    # Initialize Ricart–Agrawala mutual exclusion
    mutex = RicartAgrawalaMutex(node)

    # Start RA worker in background
    asyncio.create_task(cs_worker(node_id, mutex))


    lat, lon = 33.7838, -118.1141
    try:
        while True:
            # Simulate movement
            lat += (random.random() - 0.5) * 0.0005
            lon += (random.random() - 0.5) * 0.0005
            payload = {"lat": round(lat, 6), "lon": round(lon, 6), "ts": time.time()}
            
            # Broadcast to P2P peers
            await node.broadcast({"type": "location_update", "payload": payload})
            
            # Send to Flask server for frontend display
            send_position_to_server(node_id, payload["lat"], payload["lon"])

            await asyncio.sleep(1.5)
    except KeyboardInterrupt:
        pass
    finally:
        await node.stop()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Vehicle peer")
    parser.add_argument('--id', required=True)
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--mgroup', default='224.0.0.250')
    parser.add_argument('--mport', type=int, default=50000)
    args = parser.parse_args()
    asyncio.run(run_vehicle(args.id, args.host, args.port, args.mgroup, args.mport))

