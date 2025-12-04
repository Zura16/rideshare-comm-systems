// ============================================
// RIDESHARE LIVE TRACKING - APPLICATION LOGIC
// ============================================

// Configuration
const CONFIG = {
    socketUrl: 'http://localhost:5000',
    mapCenter: [33.7838, -118.1141],
    mapZoom: 13,
    maxFeedItems: 10,
    markerColors: [
        '#667eea', '#764ba2', '#f093fb', '#f5576c',
        '#10b981', '#f59e0b', '#06b6d4', '#8b5cf6'
    ]
};

// State
const state = {
    map: null,
    socket: null,
    vehicles: new Map(),
    passengers: new Map(),
    destinations: new Map(),
    routes: new Map(),
    colorIndex: 0,
    feedItems: []
};

// ============================================
// MAP INITIALIZATION
// ============================================

function initializeMap() {
    state.map = L.map('map').setView(CONFIG.mapCenter, CONFIG.mapZoom);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap, CARTO',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(state.map);

    console.log('Map initialized');
}

// ============================================
// SOCKET.IO INITIALIZATION
// ============================================

function initializeSocket() {
    state.socket = io(CONFIG.socketUrl, {
        transports: ['websocket'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5
    });

    state.socket.on('connect', handleConnect);
    state.socket.on('disconnect', handleDisconnect);
    state.socket.on('vehicle_update', handleVehicleUpdate);
    state.socket.on('passenger_update', handlePassengerUpdate);
    state.socket.on('ride_assigned', handleRideAssigned);
    state.socket.on('destination_routing', handleDestinationRouting);
    state.socket.on('passenger_removed', handlePassengerRemoved);

    console.log('Socket.IO initialized');
}

function handleConnect() {
    updateConnectionStatus(true);
    addFeedItem("System", "Connected to tracking server");
}

function handleDisconnect() {
    updateConnectionStatus(false);
    addFeedItem("System", "Disconnected from server");
}

// ============================================
// VEHICLE TRACKING
// ============================================

function handleVehicleUpdate(data) {
    const { id, lat, lon } = data;
    if (!id || lat === undefined || lon === undefined) return;

    if (state.vehicles.has(id)) {
        updateVehicle(id, lat, lon);
    } else {
        createVehicle(id, lat, lon);
    }

    addFeedItem(id, `Updated position: ${lat.toFixed(4)}, ${lon.toFixed(4)}`);
    updateVehicleCount();
}

function createVehicle(id, lat, lon) {
    const color = CONFIG.markerColors[state.colorIndex % CONFIG.markerColors.length];
    state.colorIndex++;

    const icon = L.divIcon({
        className: 'custom-div-icon',
        html: `<div class="custom-marker" style="background:${color};border:3px solid white;"></div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });

    const marker = L.marker([lat, lon], { icon })
        .addTo(state.map)
        .bindPopup(createPopupContent(id, lat, lon));

    state.vehicles.set(id, { marker, color, lastUpdate: Date.now() });
    state.map.panTo([lat, lon]);
}

function updateVehicle(id, lat, lon) {
    const vehicle = state.vehicles.get(id);
    if (!vehicle) return;

    const current = vehicle.marker.getLatLng();
    const target = L.latLng(lat, lon);

    animateMarker(vehicle.marker, current, target);
    vehicle.marker.setPopupContent(createPopupContent(id, lat, lon));
    vehicle.lastUpdate = Date.now();


}

function animateMarker(marker, from, to, duration = 1000) {
    const start = Date.now();

    function step() {
        const progress = Math.min((Date.now() - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);

        marker.setLatLng([
            from.lat + (to.lat - from.lat) * eased,
            from.lng + (to.lng - from.lng) * eased
        ]);

        if (progress < 1) requestAnimationFrame(step);
    }

    step();
}

function createPopupContent(id, lat, lon) {
    return `
        <div class="popup-content">
            <div class="popup-vehicle-id">${id}</div>
            <div class="popup-coords">
                Lat: ${lat.toFixed(6)}<br>
                Lon: ${lon.toFixed(6)}
            </div>
        </div>
    `;
}

// ============================================
// PASSENGER TRACKING
// ============================================

function handlePassengerUpdate(data) {
    const { id, lat, lon, dest_lat, dest_lon, status } = data;

    if (status === "picked_up") {
        if (state.passengers.has(id)) {
            state.map.removeLayer(state.passengers.get(id).marker);
            state.passengers.delete(id);
        }
        return;
    }

    if (state.passengers.has(id)) {
        state.passengers.get(id).marker.setLatLng([lat, lon]);
    } else {
        createPassenger(id, lat, lon, dest_lat, dest_lon);
    }
}

function createPassenger(id, lat, lon, dest_lat, dest_lon) {
    const icon = L.divIcon({
        className: 'passenger-marker',
        html: `<div class="passenger-marker-inner"></div>`,
        iconSize: [25, 25],
        iconAnchor: [12.5, 12.5]
    });

    const marker = L.marker([lat, lon], { icon })
        .addTo(state.map)
        .bindPopup(`<div class="popup-content"><div>${id}</div><div>Passenger<br>Waiting</div></div>`);

    state.passengers.set(id, { marker, status: "waiting" });

    // Destination marker (green)
    if (dest_lat && dest_lon) {
        const destIcon = L.divIcon({
            className: "destination-marker",
            html: `<div class="destination-flag">📍</div>`,
            iconSize: [30, 30],
            iconAnchor: [15, 30]
        });

        const destMarker = L.marker([dest_lat, dest_lon], { icon: destIcon })
            .addTo(state.map)
            .bindPopup(`<div class="popup-content"><div style="color:#10b981;">Destination</div><div>For ${id}</div></div>`);

        state.destinations.set(id, destMarker);
    }

    addFeedItem("System", `New passenger: ${id}`);
}

// ============================================
// ROUTING
// ============================================

function handleRideAssigned(data) {
    const { passenger_id, vehicle_id, vehicle_lat, vehicle_lon, passenger_lat, passenger_lon } = data;

    drawRoute(passenger_id, vehicle_lat, vehicle_lon, passenger_lat, passenger_lon);
    addFeedItem("System", `${vehicle_id} assigned to ${passenger_id}`);
}

function drawRoute(passenger_id, vLat, vLon, pLat, pLon) {
    if (state.routes.has(passenger_id)) {
        state.map.removeLayer(state.routes.get(passenger_id));
    }

    const route = L.polyline(
        [[vLat, vLon], [pLat, pLon]],
        { color: "#f093fb", weight: 3, opacity: 0.7, dashArray: "10,10" }
    ).addTo(state.map);

    state.routes.set(passenger_id, route);
}

function handleDestinationRouting(data) {
    const { passenger_id, vehicle_id, dest_lat, dest_lon } = data;

    if (state.passengers.has(passenger_id)) {
        state.map.removeLayer(state.passengers.get(passenger_id).marker);
        state.passengers.delete(passenger_id);
    }

    if (state.routes.has(passenger_id)) {
        state.map.removeLayer(state.routes.get(passenger_id));
        state.routes.delete(passenger_id);
    }

    const vehicle = state.vehicles.get(vehicle_id);
    if (vehicle) {
        const vPos = vehicle.marker.getLatLng();

        const destRoute = L.polyline(
            [[vPos.lat, vPos.lng], [dest_lat, dest_lon]],
            { color: "#10b981", weight: 3, opacity: 0.7, dashArray: "5,5" }
        ).addTo(state.map);

        state.routes.set(passenger_id, destRoute);
    }

    addFeedItem("System", `${vehicle_id} en route to destination`);
}

function handlePassengerRemoved(data) {
    const { id } = data;

    if (state.destinations.has(id)) {
        state.map.removeLayer(state.destinations.get(id));
        state.destinations.delete(id);
    }

    if (state.routes.has(id)) {
        state.map.removeLayer(state.routes.get(id));
        state.routes.delete(id);
    }

    addFeedItem("System", `Dropoff complete for ${id}`);
}

// ============================================
// UI
// ============================================

function updateConnectionStatus(connected) {
    const el = document.querySelector(".connection-status");
    const text = document.querySelector(".status-text");

    if (!el || !text) return;

    if (connected) {
        el.classList.remove("disconnected");
        text.textContent = "Connected";
    } else {
        el.classList.add("disconnected");
        text.textContent = "Disconnected";
    }
}

function updateVehicleCount() {
    const el = document.querySelector(".count-value");
    if (el) el.textContent = state.vehicles.size;
}

function addFeedItem(id, message) {
    const entry = {
        id,
        message,
        timestamp: new Date().toLocaleTimeString()
    };

    state.feedItems.unshift(entry);
    if (state.feedItems.length > CONFIG.maxFeedItems) {
        state.feedItems.pop();
    }

    renderFeed();
}

function renderFeed() {
    const feed = document.querySelector(".update-feed");
    if (!feed) return;

    feed.innerHTML = `
        <div class="feed-title">Recent Updates</div>
        ${state.feedItems.map(item => `
            <div class="feed-item">
                <span class="vehicle-id">${item.id}</span>: ${item.message}
                <div style="font-size:0.7rem;opacity:.7;">${item.timestamp}</div>
            </div>
        `).join("")}
    `;
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener("DOMContentLoaded", () => {
    initializeMap();
    initializeSocket();
    updateConnectionStatus(false);
    updateVehicleCount();
});

// ============================================
// CLEANUP
// ============================================

function cleanupInactiveVehicles(timeout = 300000) {
    const now = Date.now();

    state.vehicles.forEach((vehicle, id) => {
        if (now - vehicle.lastUpdate > timeout) {
            state.map.removeLayer(vehicle.marker);
            state.vehicles.delete(id);
        }
    });

    updateVehicleCount();
}

setInterval(() => cleanupInactiveVehicles(), 60000);
