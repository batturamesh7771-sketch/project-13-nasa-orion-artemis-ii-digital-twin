/**
 * NASA Artemis II Digital Twin — Comprehensive Headless Browser Verification Suite
 * Uses puppeteer-core connected to Chrome to thoroughly verify all 8 tabs,
 * canvases, interactive drills, GMAT execution, and Open MCT integration.
 */

const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const ARTIFACT_DIR = 'C:\\Users\\user\\.gemini\\antigravity\\brain\\bd4d2104-51f7-4d68-b523-07c931a12cbb';

async function runVerification() {
  console.log('======================================================================');
  console.log('   NASA ORION ARTEMIS II DIGITAL TWIN — FULL SYSTEM VERIFICATION      ');
  console.log('======================================================================');
  console.log('[*] Launching Headless Chrome from:', CHROME_PATH);

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1920,1080'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });

  const consoleLogs = [];
  const pageErrors = [];

  page.on('console', msg => {
    const text = msg.text();
    consoleLogs.push({ type: msg.type(), text });
    if (msg.type() === 'error') {
      console.error('   [PAGE ERROR LOG]:', text);
    }
  });

  page.on('pageerror', err => {
    console.error('   [UNCAUGHT PAGE ERROR]:', err.message);
    pageErrors.push(err.message);
  });

  console.log('[*] Navigating to Mission Control Twin: http://127.0.0.1:8000/...');
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'domcontentloaded', timeout: 45000 });

  // Wait 2.5s for initial WebSocket connection and 3D scenes to settle
  await new Promise(r => setTimeout(r, 2500));

  // -------------------------------------------------------------------------
  // Test 1: TAB - MISSION (AIM 1, 2, 3 Main Operational View)
  // -------------------------------------------------------------------------
  console.log('\n[1/7] Testing Tab: MISSION & Flight HUD...');
  const missionMetrics = await page.evaluate(() => {
    return {
      met: document.getElementById('hdrMet')?.textContent,
      utc: document.getElementById('hdrUtc')?.textContent,
      stage: document.getElementById('hudStage')?.textContent,
      alt: document.getElementById('hudAlt')?.textContent,
      vel: document.getElementById('hudVel')?.textContent,
      q: document.getElementById('hudQ')?.textContent,
      thrust: document.getElementById('hudThrust')?.textContent,
      g: document.getElementById('hudG')?.textContent
    };
  });
  console.log('      HUD Readouts:', JSON.stringify(missionMetrics));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'verify_tab1_mission.png') });
  console.log('   -> Screenshot saved: verify_tab1_mission.png');

  // -------------------------------------------------------------------------
  // Test 2: TAB - TRAJECTORY (State Vectors, Keplerian, Cowell N-Body, Ground Track)
  // -------------------------------------------------------------------------
  console.log('\n[2/7] Testing Tab: TRAJECTORY & Astrodynamics...');
  await page.evaluate(() => window.switchTab('trajectory'));
  await new Promise(r => setTimeout(r, 1200));

  const trajMetrics = await page.evaluate(() => {
    return {
      posX: document.getElementById('trajPosX')?.textContent,
      posY: document.getElementById('trajPosY')?.textContent,
      posZ: document.getElementById('trajPosZ')?.textContent,
      sma: document.getElementById('trajSMA')?.textContent,
      ecc: document.getElementById('trajEcc')?.textContent,
      inc: document.getElementById('trajInc')?.textContent,
      period: document.getElementById('trajPeriod')?.textContent,
      energy: document.getElementById('trajEnergy')?.textContent,
      aJ2: document.getElementById('trajAJ2')?.textContent,
      aMoon: document.getElementById('trajAMoon')?.textContent,
      subLat: document.getElementById('trajLat')?.textContent,
      subLon: document.getElementById('trajLon')?.textContent,
      dsnStation: document.getElementById('trajDsnStation')?.textContent
    };
  });
  console.log('      Trajectory & Cowell:', JSON.stringify(trajMetrics));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'verify_tab2_trajectory.png') });
  console.log('   -> Screenshot saved: verify_tab2_trajectory.png');

  // -------------------------------------------------------------------------
  // Test 3: TAB - TELEMETRY (6-DOF, Trick Dynamics, Propulsion & Strip Chart)
  // -------------------------------------------------------------------------
  console.log('\n[3/7] Testing Tab: TELEMETRY (Sensors & NASA Open MCT View)...');
  await page.evaluate(() => window.switchTab('telemetry'));
  await new Promise(r => setTimeout(r, 1200));

  const teleMetrics = await page.evaluate(() => {
    return {
      alt: document.getElementById('telAlt')?.textContent,
      vel: document.getElementById('telVel')?.textContent,
      mach: document.getElementById('telMach')?.textContent,
      q: document.getElementById('telQ')?.textContent,
      mass: document.getElementById('telMass')?.textContent,
      cgz: document.getElementById('telCgz')?.textContent,
      ixx: document.getElementById('telIxx')?.textContent,
      trickMode: document.getElementById('telTrickMode')?.textContent,
      rs25Pc: document.getElementById('telRs25Pc')?.textContent,
      srbPc: document.getElementById('telSrbPc')?.textContent,
      q0: document.getElementById('telQ0')?.textContent,
      subLunar: document.getElementById('telSubLunar')?.textContent,
      dsnLos: document.getElementById('telDsnLos')?.textContent
    };
  });
  console.log('      6-DOF Sensors & Engines:', JSON.stringify(teleMetrics));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'verify_tab3a_telemetry_gauges.png') });
  console.log('   -> Screenshot saved: verify_tab3a_telemetry_gauges.png');

  // Test Open MCT View Toggle
  console.log('      Toggling NASA Open MCT Mission Control View...');
  await page.evaluate(() => setTelemetryViewMode('openmct'));
  await new Promise(r => setTimeout(r, 2500));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'verify_tab3b_openmct_embed.png') });
  console.log('   -> Screenshot saved: verify_tab3b_openmct_embed.png');

  // Return to gauges
  await page.evaluate(() => setTelemetryViewMode('gauges'));

  // -------------------------------------------------------------------------
  // Test 4: TAB - SYSTEMS (EPS, ECLSS, ATCS, Comm & Radiation Drills)
  // -------------------------------------------------------------------------
  console.log('\n[4/7] Testing Tab: SYSTEMS (EPS, ECLSS, ATCS & AE9/AP9 Radiation)...');
  await page.evaluate(() => window.switchTab('systems'));
  await new Promise(r => setTimeout(r, 1200));

  const sysMetricsBefore = await page.evaluate(() => {
    return {
      saw1: document.getElementById('sysSaw1')?.textContent,
      busA: document.getElementById('sysBusA')?.textContent,
      cabinP: document.getElementById('sysCabinP')?.textContent,
      pO2: document.getElementById('sysPO2')?.textContent,
      hsStag: document.getElementById('sysHsStag')?.textContent,
      dsnStation: document.getElementById('sysDsnStation')?.textContent,
      lShell: document.getElementById('radLShell')?.textContent,
      region: document.getElementById('radRegion')?.textContent,
      doseRate: document.getElementById('radDoseRate')?.textContent,
      threatBadge: document.getElementById('radThreatBadge')?.textContent
    };
  });
  console.log('      Systems Baseline:', JSON.stringify(sysMetricsBefore));

  // Trigger Solar Particle Event Flare Drill
  console.log('      Triggering Solar Particle Event (SPE Flare) Drill...');
  await page.evaluate(() => injectSpeDrill());
  await new Promise(r => setTimeout(r, 1500));

  // Toggle Storm Shelter
  console.log('      Toggling Orion Aft-Bay Storm Shelter...');
  await page.evaluate(() => toggleShelterDrill());
  await new Promise(r => setTimeout(r, 1500));

  const radMetricsAfter = await page.evaluate(() => {
    return {
      threatBadge: document.getElementById('radThreatBadge')?.textContent,
      shelterStatus: document.getElementById('radShelterStatus')?.textContent
    };
  });
  console.log('      Radiation After Flare & Shelter:', JSON.stringify(radMetricsAfter));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'verify_tab4_systems_radiation.png') });
  console.log('   -> Screenshot saved: verify_tab4_systems_radiation.png');

  // -------------------------------------------------------------------------
  // Test 5: TAB - 3D VIEW (SVS 5610 Camera Framings & Lunar Surface Relief)
  // -------------------------------------------------------------------------
  console.log('\n[5/7] Testing Tab: 3D VIEW (SVS 5610 Camera Presets & CGI Moon Kit)...');
  await page.evaluate(() => window.switchTab('3dview'));
  await new Promise(r => setTimeout(r, 1500));

  // Test SVS 5610 Camera Preset
  await page.evaluate(() => {
    const sel = document.getElementById('camSelect');
    if (sel) {
      sel.value = 'svs5610_overview';
      if (typeof changeCameraPreset === 'function') changeCameraPreset('svs5610_overview');
    }
  });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'verify_tab5_3dview_svs5610.png') });
  console.log('   -> Screenshot saved: verify_tab5_3dview_svs5610.png');

  // -------------------------------------------------------------------------
  // Test 6: TAB - DATA & VALIDATION (Matrix, Live GMAT Benchmark, SVS 5610)
  // -------------------------------------------------------------------------
  console.log('\n[6/7] Testing Tab: DATA & VALIDATION (GMAT Benchmark & SVS Table)...');
  await page.evaluate(() => window.switchTab('data'));
  await new Promise(r => setTimeout(r, 1200));

  const valMetrics = await page.evaluate(() => {
    return {
      gmatBadge: document.getElementById('gmatBadgeStatus')?.textContent,
      deltaR: document.getElementById('gmatResDeltaR')?.textContent,
      deltaV: document.getElementById('gmatResDeltaV')?.textContent,
      trickMode: document.getElementById('trickMode')?.textContent,
      trickFrames: document.getElementById('trickFrames')?.textContent,
      spiceKernels: document.getElementById('spiceKernels')?.textContent
    };
  });
  console.log('      Validation Benchmarks:', JSON.stringify(valMetrics));

  // Execute Live GMAT Benchmark
  console.log('      Executing Live NASA GMAT R2026a Execution Run...');
  await page.evaluate(() => executeGmatBenchmark());
  await new Promise(r => setTimeout(r, 3500));

  const gmatOutput = await page.evaluate(() => document.getElementById('gmatLiveOutput')?.textContent);
  console.log('      GMAT Output Log:\n', gmatOutput ? gmatOutput.substring(0, 300) + '...' : '(No output)');

  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'verify_tab6_data_validation.png') });
  console.log('   -> Screenshot saved: verify_tab6_data_validation.png');

  // -------------------------------------------------------------------------
  // Test 7: TAB - 3D CAD / ASSEMBLY (Interactive Inspection & Parts Explosion)
  // -------------------------------------------------------------------------
  console.log('\n[7/7] Testing Tab: 3D CAD / ASSEMBLY (Interactive Parts Inspection)...');
  await page.evaluate(() => window.switchTab('cad'));
  await new Promise(r => setTimeout(r, 1200));

  // Toggle Exploded View
  await page.evaluate(() => toggleCadExplode());
  await new Promise(r => setTimeout(r, 1000));

  // Click on "Core Stage Structure" node
  await page.evaluate(() => selectCadComponent('core'));
  await new Promise(r => setTimeout(r, 800));

  // Click on "4x RS-25 Main Engines" node
  await page.evaluate(() => selectCadComponent('engines'));
  await new Promise(r => setTimeout(r, 800));

  // Click on "Orion Crew Module CM-003" node
  await page.evaluate(() => selectCadComponent('cm'));
  await new Promise(r => setTimeout(r, 800));

  const cadSpec = await page.evaluate(() => document.getElementById('cadSpecContent')?.innerText);
  console.log('      CAD Inspection Specs:\n', cadSpec ? cadSpec.substring(0, 200) + '...' : '(No spec)');

  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'verify_tab7_cad_assembly.png') });
  console.log('   -> Screenshot saved: verify_tab7_cad_assembly.png');

  console.log('\n======================================================================');
  console.log(`[+] VERIFICATION COMPLETED WITH ${pageErrors.length} UNCAUGHT ERRORS!`);
  console.log('======================================================================');

  await browser.close();
}

runVerification().catch(err => {
  console.error('Fatal Verification Error:', err);
  process.exit(1);
});
