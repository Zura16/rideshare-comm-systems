from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit
import os

# Configure Flask to serve frontend files
app = Flask(__name__, static_folder='frontend', static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Track active vehicles
active_vehicles = {}

@app.route("/")
def home():
    """Serve the main frontend page"""
    return send_from_directory('frontend', 'index.html')

@app.route("/<path:path>")
def serve_static(path):
    """Serve static frontend files (CSS, JS, etc.)"""
    return send_from_directory('frontend', path)

@app.route("/api/vehicle/position", methods=['POST'])
def receive_vehicle_position():
    """Receive vehicle position updates from vehicle peers"""
    data = request.get_json()
    vehicle_id = data.get('vehicle_id')
    lat = data.get('lat')
    lon = data.get('lon')
    
    if vehicle_id and lat is not None and lon is not None:
        # Update active vehicles
        active_vehicles[vehicle_id] = {"lat": lat, "lon": lon}
        
        # Broadcast to all connected WebSocket clients
        socketio.emit("vehicle_update", {
            "id": vehicle_id,
            "lat": lat,
            "lon": lon
        })
        
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

# Called by vehicle peers - now properly async-compatible
async def broadcast_position(vehicle_id, lat, lon):
    """Broadcast vehicle position to all connected clients"""
    active_vehicles[vehicle_id] = {"lat": lat, "lon": lon}
    socketio.emit("vehicle_update", {
        "id": vehicle_id,
        "lat": lat,
        "lon": lon
    })

@socketio.on('connect')
def handle_connect():
    """Send all active vehicles to newly connected clients"""
    print(f"Client connected. Sending {len(active_vehicles)} active vehicles.")
    for vehicle_id, position in active_vehicles.items():
        emit("vehicle_update", {
            "id": vehicle_id,
            "lat": position["lat"],
            "lon": position["lon"]
        })

if __name__ == "__main__":
    print("Starting Flask-SocketIO server on http://localhost:5000")
    print(f"Serving frontend from: {os.path.abspath('frontend')}")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
