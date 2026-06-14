/* ═══════════════════════════════════════════════════════════
   Rideshare Comm Systems — Network Protocol Visualizer
   Interactive Simulation & Animation Script
   ═══════════════════════════════════════════════════════════ */

(() => {
  'use strict';

  // ─── DOM References ───
  const topologyContainer = document.getElementById('topology-canvas');
  const svgLines = document.getElementById('svg-lines');
  const payloadTooltip = document.getElementById('payload-tooltip');
  const messageLog = document.getElementById('message-log');
  
  const btnRequest = document.getElementById('btn-request');
  const btnReset = document.getElementById('btn-reset');
  const btnAuto = document.getElementById('btn-auto');
  const btnClearLog = document.getElementById('btn-clear-log');
  
  const statMessages = document.getElementById('stat-messages');
  const statClock = document.getElementById('stat-clock');
  const protoLabel = document.getElementById('proto-label');
  const tabButtons = document.querySelectorAll('.protocol-tabs .tab');

  // ─── App State ───
  let currentProtocol = 'rest'; // 'rest', 'tcp', 'p2p'
  let messageCount = 0;
  let maxLogicalClock = 0;
  let isPlaying = false;
  let autoPlayTimer = null;
  let activeAnimations = [];

  // ─── Node Configurations ───
  const nodes = {
    alice:   { id: 'alice',   name: 'Rider: Alice',   type: 'rider',  icon: '', x: 15, y: 30, clock: 0 },
    bob:     { id: 'bob',     name: 'Rider: Bob',     type: 'rider',  icon: '', x: 15, y: 70, clock: 0 },
    server:  { id: 'server',  name: 'Central Server', type: 'server', icon: '', x: 50, y: 50, clock: 0 },
    charlie: { id: 'charlie', name: 'Driver: Charlie',type: 'driver', icon: '', x: 85, y: 30, clock: 0 },
    dave:    { id: 'dave',    name: 'Driver: Dave',   type: 'driver', icon: '', x: 85, y: 70, clock: 0 }
  };

  // ─── Initialize Nodes in DOM ───
  function initNodes() {
    // Clear old elements if any
    const existingNodes = topologyContainer.querySelectorAll('.node');
    existingNodes.forEach(n => n.remove());

    Object.keys(nodes).forEach(key => {
      const node = nodes[key];
      const nodeEl = document.createElement('div');
      nodeEl.className = `node node--${node.type}`;
      nodeEl.id = `node-${node.id}`;
      nodeEl.style.left = `${node.x}%`;
      nodeEl.style.top = `${node.y}%`;

      nodeEl.innerHTML = `
        <span class="node__icon">${node.icon}</span>
        <span class="node__name">${node.name.split(': ')[1] || node.name}</span>
        <span class="node__clock" id="clock-${node.id}">L: ${node.clock}</span>
      `;

      // Allow clicking node to see details
      nodeEl.addEventListener('click', () => showNodeDetails(node));

      topologyContainer.appendChild(nodeEl);
    });

    drawNetworkLines();
  }

  // ─── Draw Network Connections (SVG) ───
  function drawNetworkLines() {
    svgLines.innerHTML = '';
    const rect = topologyContainer.getBoundingClientRect();
    const w = rect.width;
    const h = rect.height;

    // Helper to get pixel coords from percentage
    const getCoords = (node) => ({
      x: (node.x / 100) * w,
      y: (node.y / 100) * h
    });

    const linesToDraw = [];

    if (currentProtocol === 'rest' || currentProtocol === 'tcp') {
      // Connect Riders to Server, and Server to Drivers
      linesToDraw.push({ from: nodes.alice, to: nodes.server });
      linesToDraw.push({ from: nodes.bob, to: nodes.server });
      linesToDraw.push({ from: nodes.server, to: nodes.charlie });
      linesToDraw.push({ from: nodes.server, to: nodes.dave });
    } else if (currentProtocol === 'p2p') {
      // Mesh: Connect Riders directly to Drivers
      linesToDraw.push({ from: nodes.alice, to: nodes.charlie });
      linesToDraw.push({ from: nodes.alice, to: nodes.dave });
      linesToDraw.push({ from: nodes.bob, to: nodes.charlie });
      linesToDraw.push({ from: nodes.bob, to: nodes.dave });
    }

    linesToDraw.forEach(conn => {
      const p1 = getCoords(conn.from);
      const p2 = getCoords(conn.to);

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', p1.x);
      line.setAttribute('y1', p1.y);
      line.setAttribute('x2', p2.x);
      line.setAttribute('y2', p2.y);
      line.setAttribute('class', `net-line ${currentProtocol}`);
      line.id = `line-${conn.from.id}-${conn.to.id}`;
      svgLines.appendChild(line);
    });
  }

  // Redraw SVG lines on window resize
  window.addEventListener('resize', drawNetworkLines);

  // ─── Logical Clock Logic ───
  function updateLocalClock(node, val) {
    node.clock = val;
    const clockBadge = document.getElementById(`clock-${node.id}`);
    if (clockBadge) {
      clockBadge.textContent = `L: ${node.clock}`;
      // Highlight clock tick animation
      clockBadge.style.transform = 'scale(1.3)';
      clockBadge.style.color = '#fff';
      clockBadge.style.background = 'var(--accent)';
      setTimeout(() => {
        clockBadge.style.transform = '';
        clockBadge.style.color = '';
        clockBadge.style.background = '';
      }, 500);
    }

    if (node.clock > maxLogicalClock) {
      maxLogicalClock = node.clock;
      statClock.textContent = maxLogicalClock;
    }
  }

  // ─── Logging ───
  function logEvent(proto, fromNode, toNode, msg, localClock) {
    // Remove empty log placeholder
    const emptyLog = messageLog.querySelector('.log-empty');
    if (emptyLog) emptyLog.remove();

    const row = document.createElement('div');
    row.className = 'log-row';

    const timestamp = document.createElement('span');
    timestamp.className = 'log-time';
    timestamp.textContent = `[Clock: ${localClock}]`;

    const protoTag = document.createElement('span');
    protoTag.className = `log-proto log-proto--${proto}`;
    protoTag.textContent = proto;

    const messageText = document.createElement('span');
    messageText.className = 'log-msg';
    messageText.innerHTML = `<strong>${fromNode.name.split(': ')[1]}</strong> ➔ <strong>${toNode.name.split(': ')[1]}</strong>: ${msg}`;

    row.appendChild(timestamp);
    row.appendChild(protoTag);
    row.appendChild(messageText);

    messageLog.appendChild(row);
    messageLog.scrollTop = messageLog.scrollHeight;
    
    messageCount++;
    statMessages.textContent = messageCount;
  }

  // ─── Node Details Modal/Tooltip ───
  function showNodeDetails(node) {
    const details = {
      rider: `Type: Rider Node\nClock: ${node.clock}\n Comm Type: Async REST Requests / Sockets`,
      driver: `Type: Driver Node\nClock: ${node.clock}\n Location Broadcast interval: ~5s`,
      server: `Type: Central Matching Server\nClock: ${node.clock}\nState: Active Connections, Driver Queue`
    };
    alert(`Node: ${node.name}\n\n${details[node.type]}`);
  }

  // ─── Message Flow Animation ───
  function animateMessage(fromNode, toNode, label, payload, protocolClass, duration = 1200) {
    return new Promise((resolve) => {
      const containerRect = topologyContainer.getBoundingClientRect();
      
      // Get exact pixel positions
      const startX = (fromNode.x / 100) * containerRect.width;
      const startY = (fromNode.y / 100) * containerRect.height;
      const endX = (toNode.x / 100) * containerRect.width;
      const endY = (toNode.y / 100) * containerRect.height;

      // Highlight line active state
      const lineId = `line-${fromNode.id}-${toNode.id}`;
      const revLineId = `line-${toNode.id}-${fromNode.id}`;
      const activeLine = document.getElementById(lineId) || document.getElementById(revLineId);
      if (activeLine) activeLine.classList.add('active');

      // Highlight active nodes
      const senderEl = document.getElementById(`node-${fromNode.id}`);
      const receiverEl = document.getElementById(`node-${toNode.id}`);
      if (senderEl) senderEl.classList.add('active');

      // Create animated message dot
      const dot = document.createElement('div');
      dot.className = `msg-dot ${protocolClass}`;
      dot.style.left = `${startX}px`;
      dot.style.top = `${startY}px`;
      topologyContainer.appendChild(dot);

      let startTime = null;

      function step(timestamp) {
        if (!startTime) startTime = timestamp;
        const progress = Math.min((timestamp - startTime) / duration, 1);

        // Linear interpolation
        const currX = startX + (endX - startX) * progress;
        const currY = startY + (endY - startY) * progress;

        dot.style.left = `${currX}px`;
        dot.style.top = `${currY}px`;

        // Show tooltip midway
        if (progress > 0.4 && progress < 0.8) {
          payloadTooltip.classList.add('show');
          payloadTooltip.style.left = `${currX}px`;
          payloadTooltip.style.top = `${currY}px`;
          payloadTooltip.innerHTML = `<strong>${label}</strong><br>${JSON.stringify(payload, null, 2)}`;
        }

        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          // Finished travel
          dot.remove();
          payloadTooltip.classList.remove('show');
          if (activeLine) activeLine.classList.remove('active');
          if (senderEl) senderEl.classList.remove('active');
          if (receiverEl) receiverEl.classList.add('active');
          
          setTimeout(() => {
            if (receiverEl) receiverEl.classList.remove('active');
          }, 400);

          resolve();
        }
      }

      requestAnimationFrame(step);
    });
  }

  // ─── Simulation Scenarios ───

  // Scenario 1: REST API
  async function runRestScenario(riderNode) {
    // 1. Send Request: Rider -> Server
    updateLocalClock(riderNode, riderNode.clock + 1);
    logEvent('rest', riderNode, nodes.server, `POST /ride_requests (Requesting Match)`, riderNode.clock);
    
    await animateMessage(
      riderNode, 
      nodes.server, 
      'POST /ride_requests', 
      { riderId: riderNode.id, lat: 37.77, lng: -122.41, type: 'standard' }, 
      'rest'
    );

    // Server Receives
    updateLocalClock(nodes.server, Math.max(nodes.server.clock, riderNode.clock) + 1);
    logEvent('rest', nodes.server, nodes.server, `Processing matching algorithm...`, nodes.server.clock);
    
    // Choose Charlie or Dave based on Rider
    const driverNode = riderNode.id === 'alice' ? nodes.charlie : nodes.dave;

    // 2. Dispatch Match: Server -> Driver
    updateLocalClock(nodes.server, nodes.server.clock + 1);
    logEvent('rest', nodes.server, driverNode, `POST /dispatches (Offer dispatch match)`, nodes.server.clock);
    
    await animateMessage(
      nodes.server,
      driverNode,
      'POST /dispatches',
      { dispatchId: 'disp_' + Math.floor(Math.random() * 1000), driverId: driverNode.id, riderId: riderNode.id },
      'rest'
    );

    // Driver Receives & Accepts
    updateLocalClock(driverNode, Math.max(driverNode.clock, nodes.server.clock) + 1);
    logEvent('rest', driverNode, nodes.server, `Response 200 OK (Match Accepted)`, driverNode.clock);

    await animateMessage(
      driverNode,
      nodes.server,
      '200 OK (Accepted)',
      { status: 'accepted', eta: '5 mins' },
      'rest'
    );

    // Server Receives Acceptance, Responds to Rider
    updateLocalClock(nodes.server, Math.max(nodes.server.clock, driverNode.clock) + 1);
    logEvent('rest', nodes.server, riderNode, `Response 200 OK (Driver Assigned)`, nodes.server.clock);

    await animateMessage(
      nodes.server,
      riderNode,
      '200 OK (Assigned)',
      { driverName: driverNode.name.split(': ')[1], status: 'assigned', eta: '5 mins' },
      'rest'
    );

    updateLocalClock(riderNode, Math.max(riderNode.clock, nodes.server.clock) + 1);
    logEvent('rest', riderNode, riderNode, `Ride Confirmed! Driver is on the way.`, riderNode.clock);
  }

  // Scenario 2: TCP / UDP
  async function runTcpScenario(riderNode) {
    // 1. TCP Handshake: Rider -> Server (SYN)
    updateLocalClock(riderNode, riderNode.clock + 1);
    logEvent('tcp', riderNode, nodes.server, `TCP SYN [Connect Request]`, riderNode.clock);
    await animateMessage(riderNode, nodes.server, 'SYN', { flags: 'SYN', seq: 100 }, 'tcp', 800);

    // Server SYN-ACK
    updateLocalClock(nodes.server, Math.max(nodes.server.clock, riderNode.clock) + 1);
    logEvent('tcp', nodes.server, riderNode, `TCP SYN-ACK [Connect Response]`, nodes.server.clock);
    await animateMessage(nodes.server, riderNode, 'SYN-ACK', { flags: 'SYN-ACK', seq: 200, ack: 101 }, 'tcp', 800);

    // Rider ACK
    updateLocalClock(riderNode, Math.max(riderNode.clock, nodes.server.clock) + 1);
    logEvent('tcp', riderNode, nodes.server, `TCP ACK [Handshake Complete]`, riderNode.clock);
    await animateMessage(riderNode, nodes.server, 'ACK', { flags: 'ACK', ack: 201 }, 'tcp', 800);

    // 2. Stream Request details: Rider -> Server (DATA)
    updateLocalClock(riderNode, riderNode.clock + 1);
    logEvent('tcp', riderNode, nodes.server, `Stream DATA [Request Ride]`, riderNode.clock);
    await animateMessage(riderNode, nodes.server, 'DATA Stream', { action: 'REQUEST_RIDE', lat: 37.77, timestamp: Date.now() }, 'tcp', 1000);

    // Server chooses driver
    const driverNode = riderNode.id === 'alice' ? nodes.charlie : nodes.dave;

    // 3. Dispatch to Driver: Server -> Driver (DATA)
    updateLocalClock(nodes.server, nodes.server.clock + 1);
    logEvent('tcp', nodes.server, driverNode, `Stream DATA [Dispatch Rider Info]`, nodes.server.clock);
    await animateMessage(nodes.server, driverNode, 'DATA Stream', { action: 'DISPATCH', rider: riderNode.id }, 'tcp', 1000);

    // Driver updates location via UDP Datagram (Unreliable but fast)
    updateLocalClock(driverNode, driverNode.clock + 1);
    logEvent('tcp', driverNode, nodes.server, `UDP Location Broadcast [No Ack Required]`, driverNode.clock);
    await animateMessage(driverNode, nodes.server, 'UDP Datagram', { lat: 37.785, lng: -122.42, speed: 25 }, 'udp', 800);
  }

  // Scenario 3: P2P Mesh
  async function runP2pScenario(riderNode) {
    // 1. P2P Discovery Gossip Broadcast
    updateLocalClock(riderNode, riderNode.clock + 1);
    logEvent('p2p', riderNode, riderNode, `Broadcasting DHT Discovery Request...`, riderNode.clock);
    
    // Animate broadcast to both driver nodes in parallel
    const p1 = animateMessage(riderNode, nodes.charlie, 'P2P DISCOVER', { query: 'driver_lookup', radius: 5 }, 'p2p', 1200);
    const p2 = animateMessage(riderNode, nodes.dave, 'P2P DISCOVER', { query: 'driver_lookup', radius: 5 }, 'p2p', 1200);
    
    await Promise.all([p1, p2]);

    // Drivers receive discovery
    updateLocalClock(nodes.charlie, Math.max(nodes.charlie.clock, riderNode.clock) + 1);
    updateLocalClock(nodes.dave, Math.max(nodes.dave.clock, riderNode.clock) + 1);

    // Choose the closest driver (Charlie for Alice, Dave for Bob)
    const activeDriver = riderNode.id === 'alice' ? nodes.charlie : nodes.dave;
    const idleDriver = riderNode.id === 'alice' ? nodes.dave : nodes.charlie;

    logEvent('p2p', idleDriver, riderNode, `Reject: out of range`, idleDriver.clock);
    logEvent('p2p', activeDriver, riderNode, `Direct Connect: In range. Sending Offer.`, activeDriver.clock);

    // 2. Direct peer connection Offer: Driver -> Rider
    updateLocalClock(activeDriver, activeDriver.clock + 1);
    await animateMessage(activeDriver, riderNode, 'P2P OFFER', { peerId: activeDriver.id, status: 'available', price: '$12.50' }, 'p2p', 1000);

    // Rider Accepts
    updateLocalClock(riderNode, Math.max(riderNode.clock, activeDriver.clock) + 1);
    logEvent('p2p', riderNode, activeDriver, `Confirming direct ride transaction`, riderNode.clock);
    await animateMessage(riderNode, activeDriver, 'P2P CONFIRM', { transaction: 'confirmed', method: 'crypto' }, 'p2p', 1000);
  }

  // ─── Trigger Simulation Sequence ───
  async function triggerRideRequest() {
    if (isPlaying) return;
    
    // Toggle controls
    btnRequest.disabled = true;
    btnRequest.style.opacity = 0.5;
    
    // Randomize rider
    const ridersList = [nodes.alice, nodes.bob];
    const rider = ridersList[Math.floor(Math.random() * ridersList.length)];

    if (currentProtocol === 'rest') {
      await runRestScenario(rider);
    } else if (currentProtocol === 'tcp') {
      await runTcpScenario(rider);
    } else if (currentProtocol === 'p2p') {
      await runP2pScenario(rider);
    }

    // Reset controls
    btnRequest.disabled = false;
    btnRequest.style.opacity = 1;
  }

  // ─── Auto Play Mode ───
  function toggleAutoPlay() {
    if (isPlaying) {
      // Pause
      clearInterval(autoPlayTimer);
      isPlaying = false;
      btnAuto.innerHTML = '▶ Auto-Play';
      btnAuto.classList.remove('btn--primary');
    } else {
      // Start
      isPlaying = true;
      btnAuto.innerHTML = '⏸ Pause';
      btnAuto.classList.add('btn--primary');
      
      triggerRideRequest(); // Run immediately
      
      autoPlayTimer = setInterval(() => {
        triggerRideRequest();
      }, 7000); // Trigger every 7s
    }
  }

  // ─── Reset State ───
  function resetSimulation() {
    clearInterval(autoPlayTimer);
    isPlaying = false;
    btnAuto.innerHTML = '▶ Auto-Play';
    btnAuto.classList.remove('btn--primary');
    btnRequest.disabled = false;
    btnRequest.style.opacity = 1;

    messageCount = 0;
    maxLogicalClock = 0;
    statMessages.textContent = '0';
    statClock.textContent = '0';

    Object.keys(nodes).forEach(key => {
      nodes[key].clock = 0;
    });

    messageLog.innerHTML = `<div class="log-empty">No messages yet — click <strong>Request Ride</strong> to start a simulation.</div>`;
    
    initNodes();
  }

  // ─── Protocol Switching ───
  function switchProtocol(proto) {
    currentProtocol = proto;
    protoLabel.textContent = proto.toUpperCase();

    tabButtons.forEach(btn => {
      if (btn.getAttribute('data-proto') === proto) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    drawNetworkLines();
  }

  // ─── Event Bindings ───
  btnRequest.addEventListener('click', triggerRideRequest);
  btnReset.addEventListener('click', resetSimulation);
  btnAuto.addEventListener('click', toggleAutoPlay);
  btnClearLog.addEventListener('click', () => {
    messageLog.innerHTML = `<div class="log-empty">No messages yet — click <strong>Request Ride</strong> to start a simulation.</div>`;
  });

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const proto = btn.getAttribute('data-proto');
      switchProtocol(proto);
    });
  });

  // ─── App Bootstrap ───
  initNodes();

})();
