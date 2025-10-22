# CECS 327 – RideShare Communication Systems


## Components and Purpose

| File | Type | Purpose |
|------|------|----------|
| `aggregator_server.py` | TCP Server | Central dispatcher that listens for multiple driver updates using sockets and threads. |
| `driver_client.py` | TCP Client | Simulated driver sending GPS/location/status to the dispatcher over TCP. |
| `aggregator_server_udp.py` | UDP Listener | Receives quick “fire-and-forget” GPS updates from drivers. |
| `driver_client_udp.py` | UDP Sender | Sends low-latency GPS pings to the UDP listener. |
| `routing_service.py` | REST API | Flask web service for passengers to request rides and check ETA. |
| `demo_client.py` | REST Client | Sends test ride requests to the Flask API. |
| `publisher_driver.py` | Pub/Sub Publisher | Broadcasts driver updates to subscribers using UDP. |
| `subscriber_rider.py` | Pub/Sub Subscriber | Receives broadcast messages and prints live driver updates. |

---

## Requirements

- Python 3.10 or higher  
- Works best on WSL/Linux (for sockets)  
- Dependencies:
  ```bash
  pip install flask requests
How to Run Each Module
TCP (Driver + Dispatcher)

Terminal 1:
python aggregator_server.py

Terminal 2:
UDP (Low-Latency Updates)

Terminal 1:
python aggregator_server_udp.py

Terminal 2:
python driver_client_udp.py
REST API (Flask)

Terminal 1:
python routing_service.py

Terminal 2:
python demo_client.py
Pub/Sub (Broadcast Model)

Terminal 1:
python subscriber_rider.py

Terminal 2:
python publisher_driver.py
