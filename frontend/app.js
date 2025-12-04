// ============================================
// RIDESHARE LIVE TRACKING - APPLICATION LOGIC
// ============================================

// Configuration
const CONFIG = {
    socketUrl: 'http://localhost:5000',
    mapCenter: [33.7838, -118.1141], // Long Beach, CA
    mapZoom: 13,
    maxFeedItems: 10,
    markerColors: [
        '#667eea', '#764ba2', '#f093fb', '#f5576c', 
        '#10b981', '#f59e0b', '#06b6d4', '#8b5cf6'
    ]
};

// State Management
const state = {
    map: null,
    socket: null,
    vehicles: new Map(),
    colorIndex: 0,
    feedItems: []
};

// ============================================
// MAP INITIALIZATION
// ============================================

function initializeMap() {
    // Create map instance
    state.map = L.map('map').setView(CONFIG.mapCenter, CONFIG.mapZoom);

    // Add tile layer with dark theme
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(state.map);

    console.log('Map initialized');
}

// ============================================
// SOCKET.IO CONNECTION
// ============================================

function initializeSocket() {
    state.socket = io(CONFIG.socketUrl, { 
        transports: ['websocket'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5
    });

    // Connection events
    state.socket.on('connect', handleConnect);
    state.socket.on('disconnect', handleDisconnect);
    state.socket.on('vehicle_update', handleVehicleUpdate);

    console.log('Socket.IO initialized');
}

function handleConnect() {
    console.log('Connected to server');
    updateConnectionStatus(true);
    addFeedItem('System', 'Connected to tracking server');
}

function handleDisconnect() {
    console.log('Disconnected from server');
    updateConnectionStatus(false);
    addFeedItem('System', 'Disconnected from server');
}

// ============================================
// VEHICLE TRACKING
// ============================================

function handleVehicleUpdate(data) {
    const { id, lat, lon } = data;
    
    if (!id || lat === undefined || lon === undefined) {
        console.warn('Invalid vehicle data:', data);
        return;
    }

    if (state.vehicles.has(id)) {
        updateVehicle(id, lat, lon);
    } else {
        createVehicle(id, lat, lon);
    }

    addFeedItem(id, `Updated position: ${lat.toFixed(4)}, ${lon.toFixed(4)}`);
    updateVehicleCount();
}

function createVehicle(id, lat, lon) {
    // Assign color
    const color = CONFIG.markerColors[state.colorIndex % CONFIG.markerColors.length];
    state.colorIndex++;

    // Create custom icon
    const icon = L.divIcon({
        className: 'custom-div-icon',
        html: `<div class="custom-marker" style="background: ${color}; border: 3px solid white;"></div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });

    // Create marker
    const marker = L.marker([lat, lon], { icon })
        .addTo(state.map)
        .bindPopup(createPopupContent(id, lat, lon));

    // Store vehicle data
    state.vehicles.set(id, {
        marker,
        color,
        lastUpdate: Date.now()
    });

    console.log(`Created vehicle: ${id} at [${lat}, ${lon}]`);
    
    // Pan to new vehicle
    state.map.panTo([lat, lon]);
}

function updateVehicle(id, lat, lon) {
    const vehicle = state.vehicles.get(id);
    
    if (!vehicle) return;

    // Smooth marker movement
    const currentLatLng = vehicle.marker.getLatLng();
    const newLatLng = L.latLng(lat, lon);
    
    // Animate marker movement
    animateMarker(vehicle.marker, currentLatLng, newLatLng);
    
    // Update popup content
    vehicle.marker.setPopupContent(createPopupContent(id, lat, lon));
    vehicle.lastUpdate = Date.now();

    console.log(`Updated vehicle: ${id} to [${lat}, ${lon}]`);
}

function animateMarker(marker, from, to, duration = 1000) {
    const startTime = Date.now();
    
    function animate() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function (ease-out)
        const eased = 1 - Math.pow(1 - progress, 3);
        
        const lat = from.lat + (to.lat - from.lat) * eased;
        const lng = from.lng + (to.lng - from.lng) * eased;
        
        marker.setLatLng([lat, lng]);
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    animate();
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
// UI UPDATES
// ============================================

function updateConnectionStatus(connected) {
    const statusElement = document.querySelector('.connection-status');
    const statusText = document.querySelector('.status-text');
    
    if (connected) {
        statusElement.classList.remove('disconnected');
        statusText.textContent = 'Connected';
    } else {
        statusElement.classList.add('disconnected');
        statusText.textContent = 'Disconnected';
    }
}

function updateVehicleCount() {
    const countElement = document.querySelector('.count-value');
    if (countElement) {
        countElement.textContent = state.vehicles.size;
    }
}

function addFeedItem(vehicleId, message) {
    const timestamp = new Date().toLocaleTimeString();
    const feedItem = {
        id: vehicleId,
        message,
        timestamp
    };

    state.feedItems.unshift(feedItem);
    
    // Limit feed items
    if (state.feedItems.length > CONFIG.maxFeedItems) {
        state.feedItems.pop();
    }

    renderFeed();
}

function renderFeed() {
    const feedContainer = document.querySelector('.update-feed');
    if (!feedContainer) return;

    const feedHTML = state.feedItems.map(item => `
        <div class="feed-item">
            <span class="vehicle-id">${item.id}</span>: ${item.message}
            <div style="font-size: 0.7rem; opacity: 0.7; margin-top: 2px;">${item.timestamp}</div>
        </div>
    `).join('');

    feedContainer.innerHTML = `
        <div class="feed-title">Recent Updates</div>
        ${feedHTML}
    `;
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing RideShare Live Tracking...');
    
    initializeMap();
    initializeSocket();
    
    // Initial UI state
    updateConnectionStatus(false);
    updateVehicleCount();
    
    console.log('Application ready!');
});

// ============================================
// UTILITY FUNCTIONS
// ============================================

// Clean up old vehicles (optional - for production)
function cleanupInactiveVehicles(timeoutMs = 300000) { // 5 minutes
    const now = Date.now();
    
    state.vehicles.forEach((vehicle, id) => {
        if (now - vehicle.lastUpdate > timeoutMs) {
            state.map.removeLayer(vehicle.marker);
            state.vehicles.delete(id);
            console.log(`Removed inactive vehicle: ${id}`);
        }
    });
    
    updateVehicleCount();
}

// Run cleanup every minute
setInterval(() => cleanupInactiveVehicles(), 60000);
