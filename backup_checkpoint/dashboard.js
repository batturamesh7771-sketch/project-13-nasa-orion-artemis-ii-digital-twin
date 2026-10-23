/**
 * NASA Artemis II Digital Twin — Mission Operations Dashboard Controller
 * Full integration connecting:
 *   - 10 Hz WebSocket telemetry stream & REST state endpoints
 *   - 3D SLS Launch & Pad LC-39B Visualizer (launch3d.js)
 *   - 3D Earth-Moon Trajectory Viewer (orbit3d.js) across all 168 hours
 *   - 3D Orion Spacecraft Model (spacecraft3d.js)
 *   - Engineering Charts (Thrust, Mass, Altitude, Velocity, Q)
 *   - Live Real-Time Telemetry & Stage Status
 *   - Celestial Orbit Sphere with 28.5 deg inclination ring
 *   - CAD / Assembly component tree and Earth Map
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize 3D Visualizers
  let launchViewer = null;
  try {
    launchViewer = new SLSLaunchViewer3D('launchCanvas');
    window.launchViewer = launchViewer;
  } catch (err) {
    console.warn('Launch 3D Viewer error:', err);
  }

  let orbitViewer = null;
  try {
    orbitViewer = new OrionOrbit3D('orbitCanvas');
    window.orbitViewer = orbitViewer;
  } catch (err) {
    console.warn('Orbit 3D Viewer error:', err);
  }

  let theaterViewer = null;
  try {
    theaterViewer = new OrionOrbit3D('theaterCanvas');
    window.theaterViewer = theaterViewer;
  } catch (err) {
    console.warn('Theater 3D Viewer error:', err);
  }

  // 2. DOM Elements
  const hdrMet = document.getElementById('hdrMet');
  const hdrMetSub = document.getElementById('hdrMetSub');
  const hdrUtc = document.getElementById('hdrUtc');

  // Left Column Elements
  const tlPhaseName = document.getElementById('tlPhaseName');
  const tlEventName = document.getElementById('tlEventName');
  const tlProgressPct = document.getElementById('tlProgressPct');
  const tlProgressFill = document.getElementById('tlProgressFill');

  // Real-Time Telemetry Elements
  const rtMET = document.getElementById('rtMET');
  const rtAlt = document.getElementById('rtAlt');
  const rtVelInertial = document.getElementById('rtVelInertial');
  const rtVelRel = document.getElementById('rtVelRel');
  const rtMach = document.getElementById('rtMach');
  const rtQ = document.getElementById('rtQ');
  const rtG = document.getElementById('rtG');
  const rtFPA = document.getElementById('rtFPA');
  const rtThrust = document.getElementById('rtThrust');
  const rtMass = document.getElementById('rtMass');
  const rtProp = document.getElementById('rtProp');

  // Stage Status Elements
  const ssLAS = document.getElementById('ssLAS');
  const ssBoosterL = document.getElementById('ssBoosterL');
  const ssBoosterR = document.getElementById('ssBoosterR');
  const ssCore = document.getElementById('ssCore');
  const ssICPS = document.getElementById('ssICPS');
  const ssOrion = document.getElementById('ssOrion');
  const rtNextEvent = document.getElementById('rtNextEvent');

  // Orbital Parameters Elements
  const orbSMA = document.getElementById('orbSMA');
  const orbEcc = document.getElementById('orbEcc');
  const orbInc = document.getElementById('orbInc');
  const orbRAAN = document.getElementById('orbRAAN');
  const orbArgP = document.getElementById('orbArgP');
  const orbNu = document.getElementById('orbNu');

  // Canvases
  const engCanvas = document.getElementById('engChartCanvas');
  const engCtx = engCanvas ? engCanvas.getContext('2d') : null;

  const liveCanvas = document.getElementById('liveChartsCanvas');
  const liveCtx = liveCanvas ? liveCanvas.getContext('2d') : null;

  const globeCanvas = document.getElementById('globeCanvas');
  const globeCtx = globeCanvas ? globeCanvas.getContext('2d') : null;

  const cadCanvas = document.getElementById('cadPreviewCanvas');
  const cadCtx = cadCanvas ? cadCanvas.getContext('2d') : null;

  const earthCanvas = document.getElementById('earthMapCanvas');
  const earthCtx = earthCanvas ? earthCanvas.getContext('2d') : null;

  // 3. State Variables
  // Initialize to 17.49s which maps directly to MET 48s (Liftoff + 48s)
  let currentDemoSec = 17.49;
  const totalMissionSec = 4100.0;
  let isPlaying = true;
  let currentSpeed = 1.0;
  let activeAim = 1;
  let currentEngChart = 'thrust';

  // 4. Milestone Schedule
  const milestones = [
    { met: 0, name: 'Liftoff', timeStr: 'T+00:00:00  6:35 PM EDT' },
    { met: 7, name: 'Tower Clear / Roll-Pitch', timeStr: 'T+00:00:07' },
    { met: 56, name: 'Supersonic', timeStr: 'T+00:00:56' },
    { met: 71, name: 'Max Dynamic Pressure', timeStr: 'T+00:01:11' },
    { met: 129, name: 'Booster Separation', timeStr: 'T+00:02:09' },
    { met: 193, name: 'LAS / Fairing Jettison', timeStr: 'T+00:03:13' },
    { met: 482, name: 'Core Stage MECO', timeStr: 'T+00:08:02' },
    { met: 494, name: 'Core Stage Separation', timeStr: 'T+00:08:14' },
    { met: 660, name: 'ICPS Orbit Raise', timeStr: 'T+00:11:00' },
    { met: 960, name: 'Orion Separation', timeStr: 'T+00:16:00' },
    { met: 90840, name: 'TLI Burn', timeStr: 'T+25:14:00' }
  ];

  // 5. Connect WebSocket Telemetry
  let ws = null;
  function connectWebSocket() {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${window.location.host}/ws/telemetry`);

    ws.onopen = () => {
      console.log('[*] Connected to Artemis Telemetry WebSocket (10 Hz)');
      // Send initial seek to MET 48s
      ws.send(JSON.stringify({ cmd: 'seek', time_sec: currentDemoSec }));
    };

    ws.onmessage = (event) => {
      try {
        const pkt = JSON.parse(event.data);
        handleTelemetryUpdate(pkt);
      } catch (err) {
        console.error('Error parsing telemetry frame:', err);
      }
    };

    ws.onclose = () => {
      setTimeout(connectWebSocket, 1500);
    };

    ws.onerror = (err) => {
      console.warn('WebSocket error, falling back to REST poll:', err);
    };
  }

  connectWebSocket();

  // Polling fallback
  setInterval(() => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      fetch('/api/telemetry/current')
        .then(res => res.json())
        .then(pkt => handleTelemetryUpdate(pkt))
        .catch(() => {});
    }
  }, 250);

  // 6. Telemetry Frame Handler
  function handleTelemetryUpdate(pkt) {
    if (!pkt) return;
    const metReal = pkt.met_real_sec || 48.0;
    const fp = pkt.flight_parameters || {};
    const ss = pkt.stage_status || {};
    const orb = pkt.orbital_parameters || {};
    const traj = pkt.trajectory || {};

    // Header Clocks
    if (hdrMet) hdrMet.textContent = pkt.met_str || 'T+ 00:00:48';
    if (hdrMetSub) {
      const s = Math.round(metReal);
      hdrMetSub.textContent = `(Liftoff + ${s}s)`;
    }
    if (hdrUtc) hdrUtc.textContent = pkt.timestamp_utc || 'Apr 01, 2026  18:35:48 UTC';

    // Left Column: Phase & Events
    if (tlPhaseName) tlPhaseName.textContent = pkt.mission_phase_name || 'Ascent';
    let curEvent = 'Liftoff';
    for (let i = 0; i < milestones.length; i++) {
      if (metReal >= milestones[i].met) {
        curEvent = milestones[i].name;
      }
    }
    if (tlEventName) tlEventName.textContent = curEvent;

    // Timeline Progress
    const pct = Math.min(100, Math.max(0, (metReal / 90840.0) * 100)).toFixed(1);
    if (tlProgressPct) tlProgressPct.textContent = `${pct}%`;
    if (tlProgressFill) tlProgressFill.style.width = `${Math.max(2, parseFloat(pct))}%`;

    // Update Milestone Checkmarks
    const msItems = document.querySelectorAll('.milestone-item');
    msItems.forEach(el => {
      const mMet = parseFloat(el.getAttribute('data-met'));
      const icon = el.querySelector('.ms-icon');
      if (icon) {
        if (metReal >= mMet) {
          icon.className = 'ms-icon checked';
          icon.innerHTML = '&#10003;';
        } else {
          icon.className = 'ms-icon uncheck';
          icon.innerHTML = '&bull;';
        }
      }
    });

    // Right Column: Real-Time Telemetry Readouts
    if (rtMET) {
      const h = Math.floor(metReal / 3600);
      const m = Math.floor((metReal % 3600) / 60);
      const s = Math.floor(metReal % 60);
      rtMET.textContent = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    }
    if (rtAlt) rtAlt.textContent = `${(fp.altitude_km !== undefined ? fp.altitude_km : traj.altitude_km || 1.2).toFixed(1)} km`;
    if (rtVelInertial) rtVelInertial.textContent = `${(fp.inertial_velocity_m_s !== undefined ? fp.inertial_velocity_m_s : traj.velocity_m_s || 152.3).toFixed(1)} m/s`;
    if (rtVelRel) rtVelRel.textContent = `${(fp.relative_velocity_m_s !== undefined ? fp.relative_velocity_m_s : 151.8).toFixed(1)} m/s`;
    if (rtMach) rtMach.textContent = (fp.mach !== undefined ? fp.mach : traj.mach || 0.45).toFixed(2);
    if (rtQ) rtQ.textContent = `${(fp.dynamic_pressure_kPa !== undefined ? fp.dynamic_pressure_kPa : 12.4).toFixed(1)} kPa`;
    if (rtG) rtG.textContent = `${(fp.acceleration_g !== undefined ? fp.acceleration_g : 1.32).toFixed(2)} g`;
    if (rtFPA) rtFPA.textContent = `${(fp.flight_path_angle_deg !== undefined ? fp.flight_path_angle_deg : 72.6).toFixed(1)}°`;
    if (rtThrust) rtThrust.textContent = `${(fp.thrust_MN !== undefined ? fp.thrust_MN : 32.6).toFixed(1)} MN`;
    if (rtMass) {
      const kg = Math.round(fp.mass_current_kg || 2598000);
      rtMass.textContent = `${kg.toLocaleString()} kg`;
    }
    if (rtProp) {
      const p = Math.round(fp.propellant_remaining_kg || 2332000);
      rtProp.textContent = `${p.toLocaleString()} kg`;
    }

    // Stage Status
    if (ssLAS) ssLAS.textContent = ss.las || (metReal < 193 ? 'Active' : 'Jettisoned (N/A)');
    if (ssBoosterL) ssBoosterL.textContent = ss.booster_left || (metReal < 129 ? 'Active' : 'Separated');
    if (ssBoosterR) ssBoosterR.textContent = ss.booster_right || (metReal < 129 ? 'Active' : 'Separated');
    if (ssCore) ssCore.textContent = ss.core_stage || (metReal < 482 ? 'Active' : 'MECO / Separated');
    if (ssICPS) ssICPS.textContent = ss.icps || (metReal >= 494 && metReal < 12255 ? 'Active' : 'Inactive');
    if (ssOrion) ssOrion.textContent = ss.orion || (metReal >= 12255 ? 'Active' : 'Inactive');

    // Next Event
    if (rtNextEvent) {
      let nextEv = 'Booster Separation';
      for (let i = 0; i < milestones.length; i++) {
        if (milestones[i].met > metReal) {
          nextEv = milestones[i].name;
          break;
        }
      }
      rtNextEvent.textContent = nextEv;
    }

    // Orbital Parameters
    if (orbSMA) orbSMA.textContent = `${(orb.semi_major_axis_km || 6563.4).toLocaleString()} km`;
    if (orbEcc) orbEcc.textContent = (orb.eccentricity || 0.0012).toFixed(4);
    if (orbInc) orbInc.textContent = `${(orb.inclination_deg || 28.5).toFixed(1)}°`;
    if (orbRAAN) orbRAAN.textContent = `${(orb.raan_deg || 142.3).toFixed(1)}°`;
    if (orbArgP) orbArgP.textContent = `${(orb.arg_periapsis_deg || 87.6).toFixed(1)}°`;
    if (orbNu) orbNu.textContent = `${(orb.true_anomaly_deg || 12.4).toFixed(1)}°`;

    // 3D Viewport Updates
    if (launchViewer) {
      launchViewer.updateTelemetry(pkt);
    }
    if (orbitViewer) {
      const frac = Math.max(0, Math.min(1.0, currentDemoSec / totalMissionSec));
      orbitViewer.updateSpacecraftPosition(frac);
    }

    // Render 2D Canvases
    renderCelestialGlobe(orb.true_anomaly_deg || 12.4);
    renderEngineeringCharts(currentEngChart, metReal);
    renderLiveDataCharts(metReal);
    renderEarthMap();
    renderCadPreview();
  }

  // 7. Global Seek To AIM Handler
  window.dashboardSeekToAim = function(aimNum) {
    activeAim = aimNum;
    if (aimNum === 1) {
      currentDemoSec = 17.49; // MET 48s Launch
      if (launchViewer) launchViewer.setSceneMode('liftoff');
    } else if (aimNum === 2) {
      currentDemoSec = 240.0; // TLI
      if (launchViewer) launchViewer.setSceneMode('tli');
    } else {
      currentDemoSec = 2300.0; // Reentry
      if (launchViewer) launchViewer.setSceneMode('core_sep');
    }
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ cmd: 'seek', time_sec: currentDemoSec }));
    }
    fetch('/api/telemetry/current')
      .then(res => res.json())
      .then(pkt => handleTelemetryUpdate(pkt))
      .catch(() => {});
  };

  // 8. Engineering Chart Tabs Handler
  document.querySelectorAll('.card-eng-charts .mini-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.card-eng-charts .mini-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentEngChart = btn.getAttribute('data-chart') || 'thrust';
      renderEngineeringCharts(currentEngChart, 48.0);
    });
  });

  // 9. Celestial Orbit Globe Canvas Renderer (Inclination 28.5 deg)
  function renderCelestialGlobe(trueAnomalyDeg) {
    if (!globeCtx || !globeCanvas) return;
    const w = globeCanvas.width;
    const h = globeCanvas.height;
    const cx = w / 2;
    const cy = h / 2;

    globeCtx.clearRect(0, 0, w, h);

    // Earth Sphere
    globeCtx.beginPath();
    globeCtx.arc(cx, cy, 18, 0, Math.PI * 2);
    const grad = globeCtx.createRadialGradient(cx - 5, cy - 5, 2, cx, cy, 18);
    grad.addColorStop(0, '#1976d2');
    grad.addColorStop(0.7, '#0d47a1');
    grad.addColorStop(1, '#051937');
    globeCtx.fillStyle = grad;
    globeCtx.fill();

    // Equatorial Guideline
    globeCtx.beginPath();
    globeCtx.ellipse(cx, cy, 18, 4, 0, 0, Math.PI * 2);
    globeCtx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    globeCtx.lineWidth = 1;
    globeCtx.stroke();

    // Inclined Orbit Ellipse (28.5 deg tilt)
    globeCtx.save();
    globeCtx.translate(cx, cy);
    globeCtx.rotate(-0.497); // 28.5 deg
    globeCtx.beginPath();
    globeCtx.ellipse(0, 0, 24, 11, 0, 0, Math.PI * 2);
    globeCtx.strokeStyle = '#0084ff';
    globeCtx.lineWidth = 1.4;
    globeCtx.stroke();

    // Ascending Node (Green dot)
    globeCtx.beginPath();
    globeCtx.arc(24, 0, 2, 0, Math.PI * 2);
    globeCtx.fillStyle = '#00e676';
    globeCtx.fill();

    // Spacecraft Position (Yellow dot at True Anomaly)
    const nuRad = (trueAnomalyDeg * Math.PI) / 180.0;
    const px = Math.cos(nuRad) * 24;
    const py = Math.sin(nuRad) * 11;
    globeCtx.beginPath();
    globeCtx.arc(px, py, 2.8, 0, Math.PI * 2);
    globeCtx.fillStyle = '#ffd600';
    globeCtx.shadowColor = '#ffd600';
    globeCtx.shadowBlur = 4;
    globeCtx.fill();
    globeCtx.restore();
  }

  // 10. Engineering Dual-Curve Chart Renderer
  function renderEngineeringCharts(chartType, currentMet) {
    if (!engCtx || !engCanvas) return;
    const rect = engCanvas.getBoundingClientRect();
    engCanvas.width = rect.width || 270;
    engCanvas.height = rect.height || 100;
    const w = engCanvas.width;
    const h = engCanvas.height;

    engCtx.clearRect(0, 0, w, h);

    const padL = 26;
    const padR = 26;
    const padT = 12;
    const padB = 16;
    const plotW = w - padL - padR;
    const plotH = h - padT - padB;

    // Grid lines
    engCtx.strokeStyle = 'rgba(0, 102, 204, 0.2)';
    engCtx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padT + (i / 4) * plotH;
      engCtx.beginPath();
      engCtx.moveTo(padL, y);
      engCtx.lineTo(w - padR, y);
      engCtx.stroke();
    }

    // Y Axis Labels Left: Thrust (0 - 50 MN)
    engCtx.fillStyle = '#00e5ff';
    engCtx.font = '7px Consolas, monospace';
    engCtx.textAlign = 'right';
    engCtx.fillText('50M', padL - 2, padT + 4);
    engCtx.fillText('25M', padL - 2, padT + plotH / 2 + 2);
    engCtx.fillText('0', padL - 2, padT + plotH + 2);

    // Y Axis Labels Right: Mass (0 - 6M kg)
    engCtx.fillStyle = '#ff9100';
    engCtx.textAlign = 'left';
    engCtx.fillText('6M', w - padR + 2, padT + 4);
    engCtx.fillText('3M', w - padR + 2, padT + plotH / 2 + 2);
    engCtx.fillText('0', w - padR + 2, padT + plotH + 2);

    // X Axis Labels: 0:00, 0:02, 0:04, 0:06, 0:08, 0:10 (0 to 600s)
    engCtx.fillStyle = '#82a3c7';
    engCtx.textAlign = 'center';
    const xLabels = ['0:00', '0:02', '0:04', '0:06', '0:08', '0:10'];
    xLabels.forEach((lbl, i) => {
      const x = padL + (i / (xLabels.length - 1)) * plotW;
      engCtx.fillText(lbl, x, h - 3);
    });

    // Sourced Curve 1: Thrust (MN) - Cyan curve
    // Liftoff: 39.14 MN -> drops slightly to 28.5 at 129s -> core drops to 8.9MN -> MECO at 482s -> 0
    engCtx.strokeStyle = '#00e5ff';
    engCtx.lineWidth = 1.8;
    engCtx.beginPath();
    const thrustPts = [
      [0, 39.14], [30, 36.8], [71, 31.8], [128, 28.5],
      [130, 8.9], [250, 8.9], [400, 8.0], [482, 7.4], [485, 0.0], [600, 0.0]
    ];
    thrustPts.forEach((pt, i) => {
      const x = padL + (pt[0] / 600.0) * plotW;
      const y = padT + plotH - (pt[1] / 50.0) * plotH;
      if (i === 0) engCtx.moveTo(x, y);
      else engCtx.lineTo(x, y);
    });
    engCtx.stroke();

    // Sourced Curve 2: Mass (kg) - Orange curve
    // Liftoff: 2.604M kg -> 1.325M kg at 129s -> drops to 485k kg -> 141k kg at MECO
    engCtx.strokeStyle = '#ff9100';
    engCtx.lineWidth = 1.8;
    engCtx.beginPath();
    const massPts = [
      [0, 2.604], [60, 2.0], [128, 1.325], [130, 0.65],
      [300, 0.35], [482, 0.141], [494, 0.056], [600, 0.056]
    ];
    massPts.forEach((pt, i) => {
      const x = padL + (pt[0] / 600.0) * plotW;
      const y = padT + plotH - (pt[1] / 6.0) * plotH;
      if (i === 0) engCtx.moveTo(x, y);
      else engCtx.lineTo(x, y);
    });
    engCtx.stroke();

    // Current MET Vertical Indicator (MET 48s)
    const curX = padL + (Math.min(600, currentMet) / 600.0) * plotW;
    engCtx.strokeStyle = 'rgba(255, 255, 255, 0.7)';
    engCtx.lineWidth = 1;
    engCtx.setLineDash([2, 2]);
    engCtx.beginPath();
    engCtx.moveTo(curX, padT);
    engCtx.lineTo(curX, padT + plotH);
    engCtx.stroke();
    engCtx.setLineDash([]);
  }

  // 11. Live Data Sparkline Charts (in Telemetry card)
  function renderLiveDataCharts(currentMet) {
    if (!liveCtx || !liveCanvas) return;
    const rect = liveCanvas.getBoundingClientRect();
    liveCanvas.width = rect.width || 450;
    liveCanvas.height = rect.height || 48;
    const w = liveCanvas.width;
    const h = liveCanvas.height;

    liveCtx.clearRect(0, 0, w, h);

    const padL = 20;
    const padR = 20;
    const padT = 6;
    const padB = 10;
    const plotW = w - padL - padR;
    const plotH = h - padT - padB;

    // Grid line
    liveCtx.strokeStyle = 'rgba(0, 102, 204, 0.2)';
    liveCtx.lineWidth = 1;
    liveCtx.beginPath();
    liveCtx.moveTo(padL, padT + plotH / 2);
    liveCtx.lineTo(w - padR, padT + plotH / 2);
    liveCtx.stroke();

    // Left sparkline (Altitude & Mach curves)
    liveCtx.strokeStyle = '#00e5ff';
    liveCtx.lineWidth = 1.4;
    liveCtx.beginPath();
    for (let x = 0; x <= plotW / 2; x += 4) {
      const tNorm = x / (plotW / 2);
      const yNorm = Math.sin(tNorm * Math.PI * 0.5) * 0.85;
      const py = padT + plotH - yNorm * plotH;
      if (x === 0) liveCtx.moveTo(padL + x, py);
      else liveCtx.lineTo(padL + x, py);
    }
    liveCtx.stroke();

    // Velocity sparkline (Orange curve)
    liveCtx.strokeStyle = '#ff9100';
    liveCtx.lineWidth = 1.4;
    liveCtx.beginPath();
    for (let x = 0; x <= plotW / 2; x += 4) {
      const tNorm = x / (plotW / 2);
      const yNorm = Math.pow(tNorm, 1.4) * 0.9;
      const py = padT + plotH - yNorm * plotH;
      if (x === 0) liveCtx.moveTo(padL + x, py);
      else liveCtx.lineTo(padL + x, py);
    }
    liveCtx.stroke();

    // Right chart segment (Acceleration & Dynamic Pressure curves)
    const midX = padL + plotW / 2 + 10;
    const rightW = plotW / 2 - 10;
    liveCtx.strokeStyle = '#00e676';
    liveCtx.beginPath();
    for (let x = 0; x <= rightW; x += 4) {
      const tNorm = x / rightW;
      const yNorm = Math.sin(tNorm * Math.PI) * 0.75 + 0.1;
      const py = padT + plotH - yNorm * plotH;
      if (x === 0) liveCtx.moveTo(midX + x, py);
      else liveCtx.lineTo(midX + x, py);
    }
    liveCtx.stroke();
  }

  // 12. 3D CAD Preview Canvas (Rocket & Stage Assembly)
  function renderCadPreview() {
    if (!cadCtx || !cadCanvas) return;
    const rect = cadCanvas.getBoundingClientRect();
    cadCanvas.width = rect.width || 120;
    cadCanvas.height = rect.height || 65;
    const w = cadCanvas.width;
    const h = cadCanvas.height;

    cadCtx.clearRect(0, 0, w, h);

    const cx = w / 2;
    // Draw wireframe silhouette of SLS Core + Boosters
    cadCtx.strokeStyle = 'rgba(0, 229, 255, 0.7)';
    cadCtx.lineWidth = 1;

    // Core Stage Cylinder
    cadCtx.strokeRect(cx - 7, 10, 14, 45);
    // Orion Capsule on top
    cadCtx.beginPath();
    cadCtx.moveTo(cx, 2);
    cadCtx.lineTo(cx - 6, 10);
    cadCtx.lineTo(cx + 6, 10);
    cadCtx.closePath();
    cadCtx.stroke();

    // Left Booster
    cadCtx.strokeRect(cx - 15, 18, 6, 38);
    // Right Booster
    cadCtx.strokeRect(cx + 9, 18, 6, 38);

    // Callout dimensions
    cadCtx.fillStyle = 'rgba(0, 229, 255, 0.5)';
    cadCtx.font = '6px Consolas, monospace';
    cadCtx.fillText('98.3m', cx + 18, 32);
  }

  // 13. Earth Map Canvas (Globe with Day/Night Terminator)
  function renderEarthMap() {
    if (!earthCtx || !earthCanvas) return;
    const w = earthCanvas.width;
    const h = earthCanvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const r = 26;

    earthCtx.clearRect(0, 0, w, h);

    // Globe Base (Ocean)
    earthCtx.beginPath();
    earthCtx.arc(cx, cy, r, 0, Math.PI * 2);
    const grad = earthCtx.createRadialGradient(cx - 6, cy - 6, 3, cx, cy, r);
    grad.addColorStop(0, '#1a73e8');
    grad.addColorStop(0.65, '#0b4592');
    grad.addColorStop(1, '#031a40');
    earthCtx.fillStyle = grad;
    earthCtx.fill();

    // Continents (simplified green silhouettes)
    earthCtx.fillStyle = '#2e7d32';
    earthCtx.beginPath();
    // North America
    earthCtx.arc(cx - 6, cy - 7, 7, 0, Math.PI * 1.5);
    // South America
    earthCtx.arc(cx - 2, cy + 8, 6, 0, Math.PI * 1.2);
    earthCtx.fill();

    // Day/Night Terminator Shadow
    earthCtx.beginPath();
    earthCtx.arc(cx, cy, r, -Math.PI / 2, Math.PI / 2, false);
    earthCtx.bezierCurveTo(cx - 8, cy + 15, cx - 8, cy - 15, cx, cy - r);
    earthCtx.fillStyle = 'rgba(0, 5, 18, 0.55)';
    earthCtx.fill();

    // Atmosphere Glow Rim
    earthCtx.beginPath();
    earthCtx.arc(cx, cy, r + 1, 0, Math.PI * 2);
    earthCtx.strokeStyle = 'rgba(0, 229, 255, 0.45)';
    earthCtx.lineWidth = 1.2;
    earthCtx.stroke();
  }

  // Initial Renders
  renderEngineeringCharts(currentEngChart, 48.0);
  renderLiveDataCharts(48.0);
  renderCelestialGlobe(12.4);
  renderEarthMap();
  renderCadPreview();
});
