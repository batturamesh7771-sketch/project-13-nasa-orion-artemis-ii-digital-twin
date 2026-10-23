/**
 * Comprehensive Automated Verification Suite for AIM 3 Reentry & 3D View Presentation
 */
const puppeteer = require('puppeteer-core');
const path = require('path');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const ARTIFACT_DIR = 'C:\\Users\\user\\.gemini\\antigravity\\brain\\bd4d2104-51f7-4d68-b523-07c931a12cbb';

async function run() {
  console.log('======================================================================');
  console.log('   VERIFYING AIM 3 REENTRY, 3D VIEW & FULLSCREEN ENLARGE SIMULATION   ');
  console.log('======================================================================');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1920,1080']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });

  console.log('[*] Navigating to http://127.0.0.1:8000/...');
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await new Promise(r => setTimeout(r, 2000));

  // -------------------------------------------------------------------------
  // Part 1: AIM 3 Complete Timeline Sequence
  // -------------------------------------------------------------------------
  console.log('\n[1/3] Testing AIM 3 Reentry Timeline Sequence in Main Viewport...');

  // 1A. ESM Separation
  console.log('      Step 1: ESM Separation (T+159h55m / 575,700s)...');
  await page.evaluate(() => window.jumpToMissionMilestone(575700));
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'aim3_1_esm_separation.png') });

  // 1B. 5,000°F Skip Reentry & Plasma Bow Shock
  console.log('      Step 2: 5,000°F Skip Reentry (25,000 mph / 576,400s)...');
  await page.evaluate(() => window.jumpToMissionMilestone(576400));
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'aim3_2_skip_reentry_5000f.png') });

  // 1C. 2x Drogue Parachutes (25,000 ft)
  console.log('      Step 3: 2x Drogue Parachutes (25,000 ft / 577,200s)...');
  await page.evaluate(() => window.jumpToMissionMilestone(577200));
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'aim3_3_drogue_parachutes.png') });

  // 1D. 3x Giant Ring-Sail Main Parachutes (9,500 ft)
  console.log('      Step 4: 3x Giant Ring-Sail Main Parachutes (9,500 ft / 577,500s)...');
  await page.evaluate(() => window.jumpToMissionMilestone(577500));
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'aim3_4_main_parachutes.png') });

  // 1E. Pacific Ocean Splashdown Impact
  console.log('      Step 5: Pacific Ocean Splashdown Impact (578,110s)...');
  await page.evaluate(() => window.jumpToMissionMilestone(578110));
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'aim3_5_ocean_splashdown_impact.png') });

  // 1F. 5x Orange CMUS Airbags, Flotation Collar & Navy Recovery
  console.log('      Step 6: CMUS Airbags, Flotation Collar & USS Portland / RHIBs (578,160s)...');
  await page.evaluate(() => window.jumpToMissionMilestone(578160));
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'aim3_6_cmus_airbags_navy_recovery.png') });

  // -------------------------------------------------------------------------
  // Part 2: [3D VIEW] Theater Tab Presenting ALL 3 AIMS
  // -------------------------------------------------------------------------
  console.log('\n[2/3] Testing [3D VIEW] Theater Tab Presenting ALL 3 AIMS...');
  await page.evaluate(() => window.switchTab('3dview'));
  await new Promise(r => setTimeout(r, 1000));

  // 2A. AIM 1 in Theater
  console.log('      Testing 3D View -> AIM 1: Launch & Pad LC-39B 3D...');
  await page.evaluate(() => window.setTheaterAim(1));
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'theater_aim1_launch_pad.png') });

  // 2B. AIM 2 in Theater
  console.log('      Testing 3D View -> AIM 2: Earth-Moon Orbit & Flyby 3D...');
  await page.evaluate(() => window.setTheaterAim(2));
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'theater_aim2_earth_moon.png') });

  // 2C. AIM 3 in Theater
  console.log('      Testing 3D View -> AIM 3: Skip Reentry & Splashdown 3D...');
  await page.evaluate(() => window.setTheaterAim(3));
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'theater_aim3_reentry.png') });

  // -------------------------------------------------------------------------
  // Part 3: Fullscreen / Enlarge 3D Simulation Mode
  // -------------------------------------------------------------------------
  console.log('\n[3/3] Testing Fullscreen / Enlarge 3D Simulation Mode...');
  await page.evaluate(() => window.switchTab('mission'));
  await new Promise(r => setTimeout(r, 600));

  await page.evaluate(() => window.toggleFullscreenSimulation());
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'fullscreen_3d_simulation.png') });

  // Exit fullscreen
  await page.evaluate(() => window.toggleFullscreenSimulation());
  await new Promise(r => setTimeout(r, 600));

  console.log('\n======================================================================');
  console.log('[+] ALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!');
  console.log('======================================================================');

  await browser.close();
}

run().catch(err => {
  console.error('Fatal Verification Error:', err);
  process.exit(1);
});
