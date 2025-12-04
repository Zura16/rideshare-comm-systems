from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit
import os

# Configure Flask to serve frontend files
app = Flask(__name__, static_folder='frontend', static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Track active vehicles and passengers
active_vehicles = {}
active_passengers = {}
active_rides = {}  # {passenger_id: {"vehicle_id": ..., "status": "assigned" | "en_route" | "completed"}}

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

@app.route("/api/passenger/request", methods=['POST'])
def receive_passenger_request():
    """Receive passenger requests"""
    data = request.get_json()
    passenger_id = data.get('passenger_id')
    lat = data.get('lat')
    lon = data.get('lon')
    dest_lat = data.get('dest_lat')
    dest_lon = data.get('dest_lon')
    status = data.get('status', 'waiting')
    
    if passenger_id and lat is not None and lon is not None:
        # Update active passengers
        active_passengers[passenger_id] = {
            "lat": lat,
            "lon": lon,
            "dest_lat": dest_lat,
            "dest_lon": dest_lon,
            "status": status
        }
        
        # Broadcast to all connected WebSocket clients
        socketio.emit("passenger_update", {
            "id": passenger_id,
            "lat": lat,
            "lon": lon,
            "dest_lat": dest_lat,
            "dest_lon": dest_lon,
            "status": status
        })
        
        # Auto-assign nearest available vehicle
        if status == 'waiting':
            assign_nearest_vehicle(passenger_id, lat, lon, dest_lat, dest_lon)
        
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two coordinates"""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def assign_nearest_vehicle(passenger_id, p_lat, p_lon, dest_lat, dest_lon):
    """Find and assign nearest available vehicle to passenger"""
    # Find available vehicles (not already assigned)
    assigned_vehicles = {r["vehicle_id"] for r in active_rides.values()}
    
    nearest_vehicle = None
    min_distance = float('inf')
    
    for vehicle_id, v_data in active_vehicles.items():
        if vehicle_id not in assigned_vehicles:
            distance = haversine_distance(p_lat, p_lon, v_data["lat"], v_data["lon"])
            if distance < min_distance:
                min_distance = distance
                nearest_vehicle = vehicle_id
    
    if nearest_vehicle:
        # Assign ride
        active_rides[passenger_id] = {
            "vehicle_id": nearest_vehicle,
            "status": "en_route_pickup",
            "passenger_lat": p_lat,
            "passenger_lon": p_lon,
            "dest_lat": dest_lat,
            "dest_lon": dest_lon
        }
        
        v_data = active_vehicles[nearest_vehicle]
        
        # Emit ride assignment to frontend
        socketio.emit("ride_assigned", {
            "passenger_id": passenger_id,
            "vehicle_id": nearest_vehicle,
            "vehicle_lat": v_data["lat"],
            "vehicle_lon": v_data["lon"],
            "passenger_lat": p_lat,
            "passenger_lon": p_lon,
            "dest_lat": dest_lat,
            "dest_lon": dest_lon
        })
        
        print(f"Assigned {nearest_vehicle} to {passenger_id}")

@app.route("/api/ride/check/<vehicle_id>", methods=['GET'])
def check_ride_assignment(vehicle_id):
    """Check if vehicle has an assigned ride"""
    for passenger_id, ride in active_rides.items():
        if ride["vehicle_id"] == vehicle_id:
            return jsonify({
                "assigned": True,
                "passenger_id": passenger_id,
                "passenger_lat": ride["passenger_lat"],
                "passenger_lon": ride["passenger_lon"],
                "dest_lat": ride.get("dest_lat"),
                "dest_lon": ride.get("dest_lon"),
                "status": ride["status"]
            }), 200
    
    return jsonify({"assigned": False}), 200

@app.route("/api/ride/pickup", methods=['POST'])
def mark_pickup():
    """Mark that passenger has been picked up"""
    data = request.get_json()
    passenger_id = data.get('passenger_id')
    
    if passenger_id in active_rides:
        # Update ride status
        active_rides[passenger_id]["status"] = "en_route_dest"
        
        ride = active_rides[passenger_id]
        
        # Emit destination routing event
        socketio.emit("destination_routing", {
            "passenger_id": passenger_id,
            "vehicle_id": ride["vehicle_id"],
            "dest_lat": ride["dest_lat"],
            "dest_lon": ride["dest_lon"]
        })
        
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "not_found"}), 404

@app.route("/api/ride/dropoff", methods=['POST'])
def mark_dropoff():
    """Mark that passenger has been dropped off"""
    data = request.get_json()
    passenger_id = data.get('passenger_id')
    
    if passenger_id in active_rides:
        del active_rides[passenger_id]
        
        # Remove passenger
        if passenger_id in active_passengers:
            del active_passengers[passenger_id]
            socketio.emit("passenger_removed", {"id": passenger_id})
        
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "not_found"}), 404

@app.route("/api/ride/complete", methods=['POST'])
def complete_ride():
    """Mark ride as completed (pickup happened)"""
    data = request.get_json()
    passenger_id = data.get('passenger_id')
    
    if passenger_id in active_rides:
        del active_rides[passenger_id]
        
        # Update passenger status
        if passenger_id in active_passengers:
            active_passengers[passenger_id]["status"] = "picked_up"
            socketio.emit("passenger_update", {
                "id": passenger_id,
                "status": "picked_up",
                "lat": active_passengers[passenger_id]["lat"],
                "lon": active_passengers[passenger_id]["lon"]
            })
        
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "not_found"}), 404

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
    """Send all active vehicles and passengers to newly connected clients"""
    print(f"Client connected. Sending {len(active_vehicles)} vehicles and {len(active_passengers)} passengers.")
    
    for vehicle_id, position in active_vehicles.items():
        emit("vehicle_update", {
            "id": vehicle_id,
            "lat": position["lat"],
            "lon": position["lon"]
        })
        
    for passenger_id, data in active_passengers.items():
        emit("passenger_update", {
            "id": passenger_id,
            "lat": data["lat"],
            "lon": data["lon"],
            "status": data.get("status", "waiting")
        })

if __name__ == "__main__":
    print("Starting Flask-SocketIO server on http://localhost:5000")
    print(f"Serving frontend from: {os.path.abspath('frontend')}")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
