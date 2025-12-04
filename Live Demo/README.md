# 🚗 RideShare Live Tracking - Demo Guide

A comprehensive guide to demonstrate the real-time vehicle tracking system with premium UI and live location updates.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Step-by-Step Demo](#step-by-step-demo)
5. [Features Showcase](#features-showcase)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This demo showcases a **real-time vehicle tracking system** built with:
- **Backend**: Flask-SocketIO server with HTTP API endpoints
- **Frontend**: Premium dark-mode UI with Leaflet.js maps and WebSocket updates
- **P2P Network**: Vehicle peers communicating via multicast and TCP
- **Real-time Updates**: Live position tracking with smooth animations

### What You'll See

- Multiple vehicles moving on an interactive map
- Real-time position updates every 1.5 seconds
- Premium glassmorphism UI with dark mode
- Connection status indicators
- Live update feed
- Smooth marker animations

---

## ✅ Prerequisites

Before running the demo, ensure you have:

### Required Software
- **Python 3.10+** installed
- **Web browser** (Chrome, Firefox, Edge, or Safari)

### Required Python Packages
```bash
pip install flask flask-socketio eventlet requests
```

Or install from requirements:
```bash
pip install -r requirements.txt
```

### Verify Installation
```bash
# Check Python version
python --version

# Check if packages are installed
pip list | grep -E "flask|socketio|eventlet|requests"
```

---

## 🚀 Quick Start

### 1. Start the Flask Server

Open a terminal and run:

```bash
cd c:\FrontEnd\cecs327-rideshare-comm-systems
py server.py
```

**Expected Output:**
```
Starting Flask-SocketIO server on http://localhost:5000
Serving frontend from: C:\FrontEnd\cecs327-rideshare-comm-systems\frontend
 * Debugger is active!
 * Debugger PIN: xxx-xxx-xxx
(xxxxx) wsgi starting up on http://0.0.0.0:5000
```

✅ Server is running when you see "wsgi starting up"

---

### 2. Open the Frontend

Open your web browser and navigate to:

```
http://localhost:5000
```

**You should see:**
- Dark-themed map centered on Long Beach, CA
- Status panel on the right showing "Connected"
- "Active Vehicles: 0"
- Branding in the bottom-left corner

---

### 3. Launch Vehicle Peers

Open **2-3 new terminal windows** and run these commands:

**Terminal 1 - Vehicle A:**
```bash
cd c:\FrontEnd\cecs327-rideshare-comm-systems
py -m p2p.vehicle_peer --id veh-A --host 127.0.0.1 --port 0
```

**Terminal 2 - Vehicle B:**
```bash
cd c:\FrontEnd\cecs327-rideshare-comm-systems
py -m p2p.vehicle_peer --id veh-B --host 127.0.0.1 --port 0
```

**Terminal 3 - Vehicle C (Optional):**
```bash
cd c:\FrontEnd\cecs327-rideshare-comm-systems
py -m p2p.vehicle_peer --id veh-C --host 127.0.0.1 --port 0
```

**Expected Output (per vehicle):**
```
[veh-A] Position sent to server: (33.783775, -118.113627)
[veh-A] requesting CS...
>>> [veh-A] ENTER CS
<<< [veh-A] EXIT CS
```

---

### 4. Watch the Magic! ✨

Switch back to your browser and observe:

- **Vehicle markers appear** on the map with different colors
- **Active Vehicles counter** updates (shows 2 or 3)
- **Markers move smoothly** as vehicles update positions
- **Update feed** shows recent position changes
- **Click on markers** to see vehicle details

---

## 📖 Step-by-Step Demo

### Demo Script (5 Minutes)

#### **Minute 1: Introduction**

> "This is a real-time vehicle tracking system for a rideshare application. Let me show you how it works."

1. Point to the browser showing the frontend
2. Highlight the key UI elements:
   - Map view
   - Status panel
   - Connection indicator
   - Branding

#### **Minute 2: Starting the System**

> "First, we start the Flask server that handles real-time communication."

1. Show the terminal running `py server.py`
2. Point out the server startup messages
3. Show the browser at `http://localhost:5000`

#### **Minute 3: Adding Vehicles**

> "Now let's add some vehicles to the system. Each vehicle is a separate peer that simulates GPS movement."

1. Open terminal and run first vehicle peer
2. Watch the browser as the first marker appears
3. Run second vehicle peer
4. Point out the vehicle count increasing

#### **Minute 4: Real-Time Tracking**

> "Notice how the vehicles move in real-time. Each marker updates its position every 1.5 seconds with smooth animations."

1. Click on a vehicle marker to show popup
2. Point out the coordinates in the popup
3. Show the update feed scrolling with new entries
4. Demonstrate the smooth animation as markers move

#### **Minute 5: System Architecture**

> "Behind the scenes, vehicle peers send HTTP POST requests to the Flask server, which broadcasts updates via WebSocket to all connected browsers."

1. Show the vehicle peer terminal output
2. Point out "Position sent to server" messages
3. Explain the P2P communication between vehicles
4. Show the Ricart-Agrawala mutual exclusion in action

---

## 🎨 Features Showcase

### 1. Premium UI Design

**Dark Mode with Glassmorphism:**
- Frosted glass effect panels
- Backdrop blur for depth
- Purple-to-pink gradient accents
- Smooth animations throughout

**Responsive Design:**
- Works on desktop and mobile
- Adaptive layouts
- Touch-friendly controls

### 2. Real-Time Tracking

**Live Position Updates:**
- Updates every 1.5 seconds
- HTTP POST from vehicles → Flask server
- WebSocket broadcast to all clients
- Smooth marker transitions (1-second ease-out)

**Multiple Vehicle Support:**
- Unlimited vehicles can connect
- Each vehicle gets a unique color
- Automatic marker management
- Inactive vehicle cleanup (5-minute timeout)

### 3. Interactive Map

**Leaflet.js Integration:**
- Dark-themed map tiles (CARTO)
- Zoom and pan controls
- Custom vehicle markers
- Click markers for details

**Vehicle Markers:**
- Colored circles (30px)
- White borders
- Bounce animation on creation
- Hover effects (scale 1.2x)

### 4. Status Panel

**Connection Indicator:**
- Green dot + "Connected" when active
- Red dot + "Disconnected" when offline
- Pulsing animation on connected state

**Active Vehicle Counter:**
- Real-time count of tracked vehicles
- Large gradient number display
- Updates instantly when vehicles join/leave

**Update Feed:**
- Shows last 10 position updates
- Vehicle ID highlighted
- Timestamp for each update
- Auto-scrolling list

### 5. P2P Communication

**Ricart-Agrawala Mutual Exclusion:**
- Distributed critical section management
- Vehicles coordinate access to shared resources
- Request/Reply messaging between peers
- Logical clock synchronization

**Multicast Discovery:**
- Vehicles discover each other via UDP multicast
- Automatic peer detection
- TCP connections for reliable messaging

---

## 🎬 Demo Scenarios

### Scenario 1: Basic Tracking (2 Vehicles)

**Goal:** Show basic real-time tracking functionality

1. Start server
2. Open browser
3. Launch veh-A and veh-B
4. Watch vehicles move on map
5. Click markers to show details

**Key Points:**
- Smooth animations
- Real-time updates
- Premium UI

---

### Scenario 2: Scalability (5+ Vehicles)

**Goal:** Demonstrate system handling multiple vehicles

1. Start server
2. Launch 5 vehicle peers (veh-A through veh-E)
3. Show all vehicles tracking simultaneously
4. Point out different colored markers
5. Show update feed with multiple vehicles

**Key Points:**
- System handles many vehicles
- Each vehicle has unique color
- No performance degradation

---

### Scenario 3: Connection Resilience

**Goal:** Show system handles disconnections gracefully

1. Start with 2-3 vehicles running
2. Stop one vehicle peer (Ctrl+C)
3. Show marker remains on map
4. Wait 5 minutes for cleanup (or explain timeout)
5. Restart vehicle peer
6. Show marker reappears

**Key Points:**
- Graceful handling of disconnections
- Automatic cleanup of stale data
- Easy reconnection

---

## 🛠️ Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask_socketio'"

**Solution:**
```bash
pip install flask-socketio eventlet
```

---

### Issue: Vehicles not appearing on map

**Check:**
1. Is the Flask server running?
2. Are vehicle peers showing "Position sent to server" messages?
3. Is browser connected? (Check status panel shows "Connected")
4. Check browser console for errors (F12 → Console tab)

**Solution:**
- Restart Flask server
- Refresh browser page
- Ensure all terminals are in correct directory

---

### Issue: "Address already in use" error

**Cause:** Port 5000 is already in use

**Solution:**
```bash
# Find and kill process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or change port in server.py:
socketio.run(app, host="0.0.0.0", port=5001)
```

---

### Issue: Vehicles not discovering each other (P2P)

**Check:**
- Are vehicles using same multicast group? (224.0.0.250)
- Are vehicles on same network/localhost?
- Firewall blocking multicast?

**Solution:**
- Use `--host 127.0.0.1` for localhost testing
- Check firewall settings
- Ensure all vehicles use same `--mgroup` parameter

---

## 📊 System Architecture

```
┌─────────────────┐
│  Vehicle Peer A │──┐
└─────────────────┘  │
                     │  HTTP POST
┌─────────────────┐  │  /api/vehicle/position
│  Vehicle Peer B │──┼──────────────────────┐
└─────────────────┘  │                      │
                     │                      ▼
┌─────────────────┐  │              ┌──────────────┐
│  Vehicle Peer C │──┘              │ Flask Server │
└─────────────────┘                 │  (Port 5000) │
                                    └──────┬───────┘
      P2P Network                          │
      (Multicast)                          │ WebSocket
         ◄─────────────────────────────────┤
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │   Frontend   │
                                    │   (Browser)  │
                                    └──────────────┘
```

---

## 🎓 Technical Details

### Communication Flow

1. **Vehicle → Server:**
   - Vehicle simulates GPS movement
   - Sends HTTP POST to `/api/vehicle/position`
   - Payload: `{vehicle_id, lat, lon}`

2. **Server Processing:**
   - Receives position update
   - Stores in `active_vehicles` dictionary
   - Broadcasts via Socket.IO

3. **Server → Frontend:**
   - WebSocket event: `vehicle_update`
   - Payload: `{id, lat, lon}`
   - All connected clients receive update

4. **Frontend Rendering:**
   - Receives update via Socket.IO
   - Creates marker if new vehicle
   - Animates marker to new position
   - Updates UI (count, feed)

### File Structure

```
cecs327-rideshare-comm-systems/
├── server.py                 # Flask-SocketIO server
├── frontend/
│   ├── index.html           # Main page
│   ├── style.css            # Premium UI styles
│   └── app.js               # Real-time tracking logic
├── p2p/
│   ├── vehicle_peer.py      # Vehicle simulation
│   ├── p2p_node.py          # P2P networking
│   └── ricart_agrawala.py   # Mutual exclusion
└── Live Demo/
    └── README.md            # This file
```

---

## 🎯 Next Steps

After completing this demo, you can:

1. **Add Passenger Pickup** - Implement ride request functionality
2. **Route Visualization** - Draw paths between locations
3. **Vehicle Status** - Show available/busy/offline states
4. **Historical Tracking** - Store and replay vehicle paths
5. **Authentication** - Add user login for production

---

## 📝 Demo Checklist

Before presenting:

- [ ] All Python packages installed
- [ ] Flask server starts without errors
- [ ] Browser opens to `http://localhost:5000`
- [ ] Frontend shows "Connected" status
- [ ] At least 2 vehicle peers ready to launch
- [ ] Terminals arranged for easy viewing
- [ ] Browser window visible alongside terminals

During demo:

- [ ] Explain the problem being solved
- [ ] Show the premium UI design
- [ ] Demonstrate real-time tracking
- [ ] Click markers to show details
- [ ] Highlight smooth animations
- [ ] Explain the architecture
- [ ] Show P2P communication in terminals

---

## 🙏 Credits

Built with:
- **Flask** - Web framework
- **Socket.IO** - Real-time communication
- **Leaflet.js** - Interactive maps
- **Eventlet** - Async networking
- **Python Requests** - HTTP client

---

**Ready to demo?** Start with the [Quick Start](#quick-start) section and follow along! 🚀
