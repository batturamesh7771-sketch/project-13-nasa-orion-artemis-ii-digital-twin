/**
 * NASA Open MCT Telemetry Server & Bridge for Orion Artemis II Digital Twin
 * Port: 8080
 * Ingests live telemetry from FastAPI backend (ws://127.0.0.1:8000/ws/telemetry)
 * Buffers historical telemetry and broadcasts realtime streams to Open MCT Web Client.
 */

const http = require('http');
const path = require('path');
const express = require('express');
const cors = require('cors');
const { WebSocketServer, WebSocket } = require('ws');
const fs = require('fs');

const PORT = process.env.PORT || 8080;
const PYTHON_WS_URL = 'ws://127.0.0.1:8000/ws/telemetry';
const PYTHON_API_BASE = 'http://127.0.0.1:8000';

const app = express();
app.use(cors());

// Serve Open MCT distribution files
const OPENMCT_DIST = path.join(__dirname, 'node_modules', 'openmct', 'dist');
if (fs.existsSync(OPENMCT_DIST)) {
  app.use('/openmct', express.static(OPENMCT_DIST));
} else {
  console.warn('[Warning] Open MCT dist folder not found at:', OPENMCT_DIST);
}

// Serve static plugin and dictionary
app.use(express.static(__dirname));

// Historical In-Memory Ring Buffer per telemetry channel
const MAX_HISTORY = 100000;
const historyBuffers = {
  'traj.altitude': [],
  'traj.velocity': [],
  'traj.perilune': [],
  'env.q': [],
  'env.temp': [],
  'env.rad': [],
  'sys.cabin_press': [],
  'sys.propellant': []
};

// Authoritative NASA Launch Epoch: 2026-04-01T22:35:00Z (UTC)
const LAUNCH_EPOCH_MS = Date.UTC(2026, 3, 1, 22, 35, 0);

// REST endpoint for historical telemetry queries from Open MCT
app.get('/history/:pointId', (req, res) => {
  const pointId = req.params.pointId;
  const start = req.query.start ? parseInt(req.query.start, 10) : 0;
  const end = req.query.end ? parseInt(req.query.end, 10) : Date.now() + 86400000000;

  const buffer = historyBuffers[pointId] || [];
  const results = buffer.filter(p => p.timestamp >= start && p.timestamp <= end);
  res.json(results);
});

// REST endpoint for system status & health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ONLINE',
    server: 'NASA Open MCT Telemetry Server (Artemis II)',
    port: PORT,
    bridge_connected: isBridgeConnected,
    client_connections: wss.clients.size,
    history_points: Object.keys(historyBuffers).reduce((acc, k) => acc + historyBuffers[k].length, 0)
  });
});

const server = http.createServer(app);

// Open MCT Realtime WebSocket Server
const wss = new WebSocketServer({ server, path: '/realtime' });

wss.on('connection', (clientWs) => {
  console.log('[Open MCT] Web client connected to realtime stream. Total clients:', wss.clients.size);
  
  // Immediately send the latest state for each channel
  const latestBatch = [];
  for (const [id, buf] of Object.entries(historyBuffers)) {
    if (buf.length > 0) {
      latestBatch.push(buf[buf.length - 1]);
    }
  }
  if (latestBatch.length > 0 && clientWs.readyState === WebSocket.OPEN) {
    clientWs.send(JSON.stringify(latestBatch));
  }

  clientWs.on('close', () => {
    console.log('[Open MCT] Client disconnected. Remaining clients:', wss.clients.size);
  });
});

function broadcastToClients(points) {
  if (!points || points.length === 0) return;
  const msg = JSON.stringify(points);
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(msg);
    }
  });
}

// Telemetry Bridge to FastAPI Backend (127.0.0.1:8000)
let bridgeWs = null;
let isBridgeConnected = false;
let reconnectTimer = null;

function appendPoint(id, timestamp, value, met) {
  const buf = historyBuffers[id];
  if (!buf) return;
  const pt = { id, timestamp, value: Number(value), met: Number(met) };
  
  // Avoid duplicate timestamps
  if (buf.length === 0 || buf[buf.length - 1].timestamp < timestamp) {
    buf.push(pt);
    if (buf.length > MAX_HISTORY) buf.shift();
  } else if (buf[buf.length - 1].timestamp === timestamp) {
    buf[buf.length - 1] = pt;
  }
  return pt;
}

function connectToDigitalTwinBridge() {
  if (bridgeWs) {
    try { bridgeWs.terminate(); } catch (e) {}
    bridgeWs = null;
  }

  console.log(`[Bridge] Connecting to Digital Twin backend at ${PYTHON_WS_URL}...`);
  
  try {
    bridgeWs = new WebSocket(PYTHON_WS_URL);
  } catch (err) {
    console.warn('[Bridge] WebSocket instantiation error:', err.message);
    scheduleReconnect();
    return;
  }

  bridgeWs.on('open', () => {
    isBridgeConnected = true;
    console.log('[Bridge] Connected successfully to FastAPI Telemetry WebSocket (127.0.0.1:8000)');
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  });

  bridgeWs.on('message', (data) => {
    try {
      const packet = JSON.parse(data.toString());
      processIncomingPacket(packet);
    } catch (e) {
      console.error('[Bridge] Error parsing telemetry packet:', e.message);
    }
  });

  bridgeWs.on('close', () => {
    if (isBridgeConnected) {
      console.log('[Bridge] Connection to FastAPI backend lost.');
    }
    isBridgeConnected = false;
    scheduleReconnect();
  });

  bridgeWs.on('error', (err) => {
    // Suppress spammy ECONNREFUSED logs if backend is temporarily restarting
    isBridgeConnected = false;
    scheduleReconnect();
  });
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectToDigitalTwinBridge();
  }, 2500);
}

function processIncomingPacket(pkt) {
  if (!pkt) return;

  const metSec = pkt.met_real_sec !== undefined ? pkt.met_real_sec : (pkt.met_sec || 0);
  const timestamp = LAUNCH_EPOCH_MS + Math.round(metSec * 1000);

  const traj = pkt.trajectory || {};
  const aero = pkt.aero_thermal || {};
  const env = pkt.environment || {};
  const eclss = pkt.eclss || {};
  const fuel = pkt.mass_fuel || pkt.propulsion_power || {};

  // Extract / convert mapped telemetry metrics
  const altKm = traj.altitude_km !== undefined ? traj.altitude_km : 0.0;
  const velKmS = traj.velocity_m_s !== undefined ? (traj.velocity_m_s / 1000.0) : 0.0;
  const lunarDistKm = traj.dist_to_moon_km !== undefined ? traj.dist_to_moon_km : 384400.0;
  const qKpa = aero.dynamic_pressure_kPa !== undefined ? aero.dynamic_pressure_kPa : (env.dynamic_pressure_kPa || 0.0);
  
  // Heat shield temperature in °F (convert from °C)
  const surfTempC = aero.surface_temp_C !== undefined ? aero.surface_temp_C : (env.temp_external_C || 20.0);
  const tempF = (surfTempC * 1.8) + 32.0;

  // Radiation dosage in mSv/hr
  const radRate = env.radiation_mSv_hr !== undefined ? env.radiation_mSv_hr : 0.01;

  // Cabin Pressure in psi (convert from kPa: 1 kPa = 0.145038 psi)
  const cabinKpa = eclss.cabin_pressure_kPa !== undefined ? eclss.cabin_pressure_kPa : 101.325;
  const cabinPsi = cabinKpa * 0.145038;

  // ESM Propellant remaining in kg
  const propKg = fuel.fuel_remaining_kg !== undefined ? fuel.fuel_remaining_kg : (fuel.propellant_remaining_kg || 8618.0);

  // Build telemetry batch
  const batch = [
    appendPoint('traj.altitude', timestamp, altKm, metSec),
    appendPoint('traj.velocity', timestamp, velKmS, metSec),
    appendPoint('traj.perilune', timestamp, lunarDistKm, metSec),
    appendPoint('env.q', timestamp, qKpa, metSec),
    appendPoint('env.temp', timestamp, tempF, metSec),
    appendPoint('env.rad', timestamp, radRate, metSec),
    appendPoint('sys.cabin_press', timestamp, cabinPsi, metSec),
    appendPoint('sys.propellant', timestamp, propKg, metSec)
  ].filter(Boolean);

  broadcastToClients(batch);
}

// Start HTTP & WebSocket server
server.listen(PORT, '0.0.0.0', () => {
  console.log('='.repeat(70));
  console.log('   NASA OPEN MCT MISSION CONTROL TELEMETRY SERVER (ORION ARTEMIS II)   ');
  console.log('='.repeat(70));
  console.log(`[*] Open MCT Web URL:       http://127.0.0.1:${PORT}/`);
  console.log(`[*] Telemetry WebSocket:    ws://127.0.0.1:${PORT}/realtime`);
  console.log(`[*] Bridging to Simulator:  ${PYTHON_WS_URL}`);
  console.log('='.repeat(70));

  // Connect to backend
  connectToDigitalTwinBridge();
});
