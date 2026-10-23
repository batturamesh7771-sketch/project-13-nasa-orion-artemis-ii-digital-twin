import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "web" / "static"

css_file = STATIC_DIR / "css" / "dashboard.css"
html_file = STATIC_DIR / "index.html"

with open(css_file, "r", encoding="utf-8") as f:
    css_text = f.read()

with open(html_file, "r", encoding="utf-8") as f:
    html_text = f.read()

# 1. Clean any existing inline <style>...</style> block that contains dashboard CSS
html_text = re.sub(r'  <style>.*?</style>', '', html_text, flags=re.DOTALL)

# 2. Clean any existing inline global <script> right before </body>
html_text = re.sub(r'  <script>\s*// Global tab switching handler.*?</script>\s*</body>', '</body>', html_text, flags=re.DOTALL)

# 3. Embed CSS inside <style> in <head>
style_block = f"""  <link rel="stylesheet" href="/static/css/dashboard.css?v=20261020_1">
  <style>
{css_text}
  </style>"""

html_text = re.sub(r'<link rel="stylesheet" href="/static/css/dashboard\.css[^"]*">', style_block, html_text)

# 4. Add explicit width="14" height="14" to all .tab-icon svgs if not present
html_text = re.sub(
    r'<svg class="tab-icon"(?! width="14") viewBox="0 0 24 24">',
    r'<svg class="tab-icon" width="14" height="14" style="width:14px;height:14px;min-width:14px;min-height:14px;display:inline-block;vertical-align:middle;" viewBox="0 0 24 24">',
    html_text
)

# 5. Add onclick="switchTab('...')" to nav-tab buttons if not present
for tab_id in ['mission', 'trajectory', 'telemetry', 'systems', '3dview', 'data', 'settings']:
    old_btn = f'data-tab="{tab_id}"'
    new_btn = f'data-tab="{tab_id}" onclick="switchTab(\'{tab_id}\')"'
    if f'onclick="switchTab(\'{tab_id}\')"' not in html_text:
        html_text = html_text.replace(old_btn, new_btn)

# 6. Add onclick to btnRunGmatLive
old_gmat_btn = 'id="btnRunGmatLive" class="btn-run-gmat"'
new_gmat_btn = 'id="btnRunGmatLive" class="btn-run-gmat" onclick="executeGmatBenchmark()"'
if 'onclick="executeGmatBenchmark()"' not in html_text:
    html_text = html_text.replace(old_gmat_btn, new_gmat_btn)

# 7. Replace #view3DPanel with complete 3D Theater Viewport containing theaterCanvas
theater_markup = """  <div id="view3DPanel" class="view-panel" style="display: none; height: calc(100vh - 82px); max-height: calc(100vh - 82px); padding: 10px 16px; flex-direction: column;">
    <div class="hud-card card-viewport" style="flex: 1; min-height: 0; display: flex; flex-direction: column; height: 100%;">
      <div class="viewport-header" style="padding: 6px 12px;">
        <div class="vp-title">
          <svg class="orion-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="#00e5ff" d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71z"/>
          </svg>
          <span style="font-size: 13px; font-weight: 800; color: #fff; letter-spacing: 1px;">ARTEMIS II 3D INTERACTIVE FLIGHT THEATER</span>
          <span class="vp-sub" style="color: var(--accent-cyan); font-size: 10px;">EXPANDED MISSION VIEWPORT</span>
        </div>
        <div style="display: flex; gap: 8px; align-items: center;">
          <div class="vp-status-pills">
            <span class="source-pill">[SIMULATED: MULTI-BODY ODE]</span>
            <span class="source-pill">[VALIDATED: NASA GMAT R2026a]</span>
          </div>
          <div style="display: flex; gap: 6px; margin-left: 8px;">
            <button class="preset-cam-btn active" data-cam="overview">OVERVIEW</button>
            <button class="preset-cam-btn" data-cam="earth">EARTH FOCUS</button>
            <button class="preset-cam-btn" data-cam="moon">MOON FLYBY</button>
            <button class="preset-cam-btn" data-cam="spacecraft">ORION CHASE CAM</button>
          </div>
        </div>
      </div>

      <div class="canvas-3d-wrapper" style="flex: 1; position: relative; min-height: 0; overflow: hidden; background: #02050e; border-radius: 4px;">
        <canvas id="theaterCanvas" style="width: 100%; height: 100%; display: block;"></canvas>

        <!-- 3D Callout Overlays -->
        <div class="callout callout-earth"><strong>Earth</strong><br>R = 6,378 km</div>
        <div class="callout callout-tli"><strong>TLI BURN</strong><br>T+ 01:42:00</div>
        <div class="callout callout-moon"><strong>Moon</strong><br>R = 1,737 km</div>
        <div class="callout callout-flyby"><strong>Lunar Flyby</strong><br>T+ 71:00:00</div>
        <div class="callout callout-return"><strong>Return Trajectory</strong><br>T+ 72:30:00</div>

        <!-- Theater Viewport Controls -->
        <div class="vp-controls-bottom">
          <div class="mode-toggles">
            <button id="btnTheater3D" class="btn-mode active">3D</button>
            <button id="btnTheater2D" class="btn-mode">2D</button>
          </div>
          <div style="font-size: 9.5px; color: var(--accent-cyan); font-family: var(--font-mono); font-weight: 700; background: rgba(5,14,28,0.7); padding: 3px 8px; border-radius: 3px; border: 1px solid rgba(0,102,204,0.3);">
            L-CLICK: ROTATE &bull; R-CLICK: PAN &bull; SCROLL: ZOOM
          </div>
        </div>
      </div>
    </div>
  </div>"""

html_text = re.sub(r'  <div id="view3DPanel".*?</div>\s*</div>\s*</div>', theater_markup, html_text, flags=re.DOTALL)

# 8. Add full inline global functions for switchTab and executeGmatBenchmark right before </body>
global_scripts = """  <script>
    // Global tab switching handler ensuring 100% responsiveness on any click
    function switchTab(tabName) {
      console.log('[*] Tab selected:', tabName);
      document.querySelectorAll('.nav-tab').forEach(function(b) {
        b.classList.remove('active');
      });
      var activeBtn = document.querySelector('.nav-tab[data-tab="' + tabName + '"]');
      if (activeBtn) activeBtn.classList.add('active');

      var views = {
        mission: document.getElementById('missionView'),
        trajectory: document.getElementById('trajectoryView'),
        telemetry: document.getElementById('telemetryView'),
        systems: document.getElementById('systemsView'),
        '3dview': document.getElementById('view3DPanel'),
        data: document.getElementById('dataValidationView'),
        settings: document.getElementById('settingsView')
      };

      Object.keys(views).forEach(function(key) {
        var el = views[key];
        if (!el) return;
        if (key === tabName) {
          el.style.setProperty('display', key === 'mission' ? 'grid' : 'flex', 'important');
        } else {
          el.style.setProperty('display', 'none', 'important');
        }
      });

      if (tabName === 'mission') {
        setTimeout(function() {
          if (window.orbitViewer && typeof window.orbitViewer._onWindowResize === 'function') {
            window.orbitViewer._onWindowResize();
          }
          if (window.spacecraftViewer && typeof window.spacecraftViewer._onWindowResize === 'function') {
            window.spacecraftViewer._onWindowResize();
          }
        }, 50);
      } else if (tabName === '3dview') {
        setTimeout(function() {
          if (window.theaterViewer && typeof window.theaterViewer._onWindowResize === 'function') {
            window.theaterViewer._onWindowResize();
          }
        }, 50);
        setTimeout(function() {
          if (window.theaterViewer && typeof window.theaterViewer._onWindowResize === 'function') {
            window.theaterViewer._onWindowResize();
          }
        }, 200);
      }
    }

    // Global GMAT live benchmark runner
    function executeGmatBenchmark() {
      var btn = document.getElementById('btnRunGmatLive');
      var out = document.getElementById('gmatLiveOutput');
      if (!btn || !out) return;

      btn.disabled = true;
      btn.innerHTML = '&#9203; EXECUTING NASA GMAT R2026a BENCHMARK...';
      out.style.display = 'block';
      out.textContent = '[*] Spawning E:\\\\NASA\\\\GMAT-R2026a\\\\bin\\\\GmatConsole.exe ...\\n[*] Propagating 24-hr Translunar Arc in GMAT & Python DP5(4) ...\\n';

      fetch('/api/validation/run')
        .then(function(res) { return res.json(); })
        .then(function(data) {
          btn.disabled = false;
          btn.innerHTML = '&#9654; EXECUTE LIVE GMAT BENCHMARK';
          out.textContent = data.output || data.error || 'Execution completed with no output.';
        })
        .catch(function(err) {
          btn.disabled = false;
          btn.innerHTML = '&#9654; EXECUTE LIVE GMAT BENCHMARK';
          out.textContent = '[ERROR] Failed to execute live GMAT benchmark: ' + err;
        });
    }
  </script>
</body>"""

html_text = html_text.replace('</body>', global_scripts)

with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_text)

print("[+] Successfully embedded CSS, 3D Theater Canvas, and tab switching handlers into index.html!")
