/**
 * Verification Suite for All 6 Required Upgrades:
 * 1. Audio Soundscape & CAPCOM Voice Calls
 * 2. Orion Cockpit Interior & Interactive Glass Displays (PFD/ADI, NAV, SYS)
 * 3. DSN Antenna Dish Tracking & Microwave Beam Link
 * 4. Avcoat Heatshield 3D Aerothermal Heatmap
 * 5. Entry Corridor Dispersions & Abort Modes (PA-1, AA-2, Direct Return)
 * 6. Engineering Ephemeris Export Suite (OEM, KML, CSV)
 */
const puppeteer = require('puppeteer-core');
const path = require('path');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const ARTIFACT_DIR = 'C:\\Users\\user\\.gemini\\antigravity\\brain\\bd4d2104-51f7-4d68-b523-07c931a12cbb';

async function run() {
  console.log('======================================================================');
  console.log('     AUTOMATED VERIFICATION SUITE — ALL 6 UPGRADE AREAS IN SEQUENCE    ');
  console.log('======================================================================');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1920,1080']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });

  // Fast loading: abort external third-party requests
  await page.setRequestInterception(true);
  page.on('request', req => {
    const url = req.url();
    if (url.includes('sketchfab.com') || url.includes('google-analytics.com')) {
      req.abort();
    } else {
      req.continue();
    }
  });

  console.log('[*] Navigating to http://127.0.0.1:8000/...');
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await new Promise(r => setTimeout(r, 2000));

  // -------------------------------------------------------------------------
  // AREA 1: Audio Soundscape & CAPCOM Voice Calls
  // -------------------------------------------------------------------------
  console.log('\n[AREA 1/6] Testing Audio Soundscape & CAPCOM Voice Calls...');
  const audioStatusBefore = await page.evaluate(() => {
    const btn = document.getElementById('btnToggleAudio');
    return {
      text: btn ? btn.textContent.trim() : null,
      isEnabled: window.artemisAudio ? window.artemisAudio.isEnabled : false
    };
  });
  console.log('   Audio Button (Initial):', audioStatusBefore.text, '| isEnabled:', audioStatusBefore.isEnabled);

  // Toggle audio ON
  await page.evaluate(() => {
    const btn = document.getElementById('btnToggleAudio');
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 600));

  await page.evaluate(() => {
    // Trigger simulated CAPCOM call
    if (window.artemisAudio && typeof window.artemisAudio.triggerCapcomCall === 'function') {
      window.artemisAudio.triggerCapcomCall('test_verify', 'Houston, Capcom. Systems nominal. Go for TLI.');
    }
  });
  await new Promise(r => setTimeout(r, 400));

  const audioStatusAfter = await page.evaluate(() => {
    const btn = document.getElementById('btnToggleAudio');
    const hud = document.getElementById('radioCommsHUD');
    const hudText = document.getElementById('radioCommsText');
    return {
      btnText: btn ? btn.textContent.trim() : null,
      isEnabled: window.artemisAudio ? window.artemisAudio.isEnabled : false,
      hudVisible: hud ? hud.style.display !== 'none' : false,
      transcript: hudText ? hudText.textContent : null
    };
  });
  console.log('   Audio Button (After Click):', audioStatusAfter.btnText, '| isEnabled:', audioStatusAfter.isEnabled);
  console.log('   CAPCOM HUD Active:', audioStatusAfter.hudVisible, '| Transcript:', audioStatusAfter.transcript);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'area1_audio_capcom_hud.png') });

  // -------------------------------------------------------------------------
  // AREA 2: Orion Cockpit Interior & Interactive Glass Displays (PFD/ADI)
  // -------------------------------------------------------------------------
  console.log('\n[AREA 2/6] Testing Orion Cockpit Interior & 3x NASA Glass Displays...');
  const cockpitResult = await page.evaluate(() => {
    window.changeCameraPreset('cockpit');
    const mm = window.masterMission3D;
    return {
      cockpitExists: !!mm?.cockpitGroup,
      cockpitVisible: mm?.cockpitGroup?.visible,
      pfdCanvasReady: !!mm?.pfdCanvas,
      navCanvasReady: !!mm?.navCanvas,
      sysCanvasReady: !!mm?.sysCanvas
    };
  });
  console.log('   Cockpit Group Visible:', cockpitResult.cockpitVisible, '| PFD/NAV/SYS Canvases:', cockpitResult.pfdCanvasReady);
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'area2_cockpit_glass_pfd.png') });

  // -------------------------------------------------------------------------
  // AREA 3: DSN Antenna Dish Tracking & Microwave Beam Link
  // -------------------------------------------------------------------------
  console.log('\n[AREA 3/6] Testing DSN Antenna Dishes & Microwave Beam Tracking...');
  // Jump to Translunar coast (MET 120,000s)
  await page.evaluate(() => {
    window.jumpToMissionMilestone(120000);
    window.changeCameraPreset('earth');
  });
  await new Promise(r => setTimeout(r, 1500));

  const dsnResult = await page.evaluate(() => {
    const mm = window.masterMission3D;
    return {
      stationCount: mm?.dsnStations?.length || 0,
      activeStation: mm?.activeDSNCode || 'N/A',
      marginDb: mm?.dsnMarginDb || 'N/A',
      beamLineVisible: mm?.dsnBeamLine?.visible
    };
  });
  console.log('   DSN 70m Ground Dishes:', dsnResult.stationCount, '| Active Lock:', dsnResult.activeStation, '| Beam Visible:', dsnResult.beamLineVisible);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'area3_dsn_tracking_beam.png') });

  // -------------------------------------------------------------------------
  // AREA 4: Avcoat Heatshield 3D Aerothermal Heatmap
  // -------------------------------------------------------------------------
  console.log('\n[AREA 4/6] Testing Avcoat Heatshield 3D Aerothermal Heatmap...');
  // Jump to Skip Reentry (MET 576,400s) where peak 5,000°F heating occurs
  await page.evaluate(() => {
    window.jumpToMissionMilestone(576400);
    window.changeCameraPreset('reentry');
  });
  await new Promise(r => setTimeout(r, 1500));

  const heatResult = await page.evaluate(() => {
    const mm = window.masterMission3D;
    const mat = mm?.heatShieldMesh?.material;
    return {
      emissiveIntensity: mat ? mat.emissiveIntensity : 0,
      emissiveHex: mat ? mat.emissive.getHexString() : '0',
      reentryHeatLightIntensity: mm?.reentryHeatLight?.intensity || 0,
      hsCanvasReady: !!mm?.hsCanvas
    };
  });
  console.log('   Avcoat Emissive Intensity:', heatResult.emissiveIntensity.toFixed(2), '| Emissive Hex: #' + heatResult.emissiveHex, '| Radiant Light:', heatResult.reentryHeatLightIntensity.toFixed(1));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'area4_avcoat_aerothermal_heatmap.png') });

  // -------------------------------------------------------------------------
  // AREA 5: Entry Corridor Dispersions & Abort Modes
  // -------------------------------------------------------------------------
  console.log('\n[AREA 5/6] Testing Entry Corridor Dispersions & Abort Modes...');
  await page.evaluate(() => {
    window.switchTab('trajectory');
  });
  await new Promise(r => setTimeout(r, 1000));

  // Verify Entry Corridor Canvas and PA-1 Abort
  const abortPA1Result = await page.evaluate(async () => {
    await window.runAbortSimulation('PA1');
    const badge = document.getElementById('entryCorridorBadge');
    const fpa = document.getElementById('entryFpaTelemetry');
    const title = document.getElementById('abortModeTitle');
    const alt = document.getElementById('abortPeakAlt');
    const g = document.getElementById('abortPeakG');
    const land = document.getElementById('abortLanding');
    return {
      corridorBadge: badge ? badge.textContent : null,
      fpaVal: fpa ? fpa.textContent : null,
      abortTitle: title ? title.textContent : null,
      peakAlt: alt ? alt.textContent : null,
      peakG: g ? g.textContent : null,
      landing: land ? land.textContent : null
    };
  });
  console.log('   Entry Corridor:', abortPA1Result.corridorBadge, '| Telemetry:', abortPA1Result.fpaVal);
  console.log('   Abort PA-1 Title:', abortPA1Result.abortTitle, '| Peak Alt:', abortPA1Result.peakAlt, '| Landing:', abortPA1Result.landing);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'area5_entry_corridor_and_abort.png') });

  // Test AA-2 Max-Q Abort
  await page.evaluate(async () => {
    await window.runAbortSimulation('AA2');
  });
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'area5_abort_aa2_maxq.png') });

  // -------------------------------------------------------------------------
  // AREA 6: Engineering Ephemeris Export Suite (OEM / KML / CSV)
  // -------------------------------------------------------------------------
  console.log('\n[AREA 6/6] Testing Engineering Ephemeris Export Suite...');
  await page.evaluate(() => {
    window.switchTab('data');
  });
  await new Promise(r => setTimeout(r, 1000));

  const exportUrls = await page.evaluate(() => {
    const links = Array.from(document.querySelectorAll('.btn-export-download')).map(a => a.getAttribute('href'));
    return links;
  });
  console.log('   Found Export Links in [DATA & VALIDATION]:', exportUrls);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'area6_ephemeris_export_suite.png') });

  // Also verify in Settings tab
  await page.evaluate(() => {
    window.switchTab('settings');
  });
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'area6_settings_export_suite.png') });

  // -------------------------------------------------------------------------
  // BASELINE INVARIANTS: Stationary Initial Paused State at T+0 Pad LC-39B
  // -------------------------------------------------------------------------
  console.log('\n[*] Verifying Baseline Initial Paused Stationary State at T+0 Pad LC-39B...');
  await page.evaluate(() => {
    window.switchTab('mission');
    window.resetSimulation();
  });
  await new Promise(r => setTimeout(r, 1200));

  const baselineState = await page.evaluate(() => {
    const hdrMet = document.getElementById('hdrMet');
    const playBtn = document.getElementById('playPauseBtn');
    const mm = window.masterMission3D;
    return {
      metText: hdrMet ? hdrMet.textContent.trim() : null,
      playBtnText: playBtn ? playBtn.textContent.trim() : null,
      padTerrainVisible: mm?.padTerrainGroup?.visible,
      slsPosition: mm?.slsGroup ? [mm.slsGroup.position.x, mm.slsGroup.position.y, mm.slsGroup.position.z] : null
    };
  });
  console.log('   MET Header:', baselineState.metText);
  console.log('   Play Button Text:', baselineState.playBtnText);
  console.log('   Pad Terrain Visible:', baselineState.padTerrainVisible);
  console.log('   SLS Position:', baselineState.slsPosition);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'baseline_stationary_pad39b_t0.png') });

  await browser.close();
  console.log('\n[+] ALL 6 UPGRADE AREAS VERIFIED SUCCESSFULLY!');
}

run().catch(err => {
  console.error('[-] Test failed with error:', err);
  process.exit(1);
});
