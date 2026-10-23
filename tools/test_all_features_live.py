import subprocess
import time
import urllib.request
import json
import base64
import asyncio
import websockets
from pathlib import Path

ARTIFACT_DIR = Path(r"C:\Users\user\.gemini\antigravity\brain\bd4d2104-51f7-4d68-b523-07c931a12cbb")

class ChromeCDP:
    def __init__(self, ws):
        self.ws = ws
        self.msg_id = 0
        self.pending = {}
        self.events = []
        self._listener_task = asyncio.create_task(self._listen())

    async def _listen(self):
        try:
            while True:
                msg = await self.ws.recv()
                data = json.loads(msg)
                if "id" in data:
                    req_id = data["id"]
                    if req_id in self.pending:
                        self.pending[req_id].set_result(data)
                else:
                    self.events.append(data)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def call(self, method, params=None, timeout=25.0):
        self.msg_id += 1
        cid = self.msg_id
        fut = asyncio.get_event_loop().create_future()
        self.pending[cid] = fut
        req = {"id": cid, "method": method}
        if params:
            req["params"] = params
        await self.ws.send(json.dumps(req))
        try:
            res = await asyncio.wait_for(fut, timeout=timeout)
            return res
        finally:
            self.pending.pop(cid, None)

    async def eval_js(self, expression, timeout=15.0):
        res = await self.call("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        }, timeout=timeout)
        val = res.get("result", {}).get("result", {}).get("value")
        return val

    async def save_screenshot(self, filepath):
        shot_res = await self.call("Page.captureScreenshot", {"format": "png"})
        png_b64 = shot_res.get("result", {}).get("data", "")
        if png_b64:
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(png_b64))
            print(f"   [+] Saved screenshot: {Path(filepath).name}")

    def close(self):
        self._listener_task.cancel()

async def run_full_suite():
    print("=" * 70)
    print("   ARTEMIS II DIGITAL TWIN — FULL BROWSER VERIFICATION SUITE   ")
    print("=" * 70)

    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_cdp_profile_suite")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9225",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "--window-size=1440,900",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
    try:
        await asyncio.sleep(2.5)
        resp = urllib.request.urlopen("http://localhost:9225/json")
        targets = json.loads(resp.read().decode())
        page_target = next((t for t in targets if t.get("type") == "page" and "127.0.0.1:8000" in t.get("url", "")), None)
        if not page_target:
            print("ERROR: Target page not found")
            return

        ws_url = page_target["webSocketDebuggerUrl"]
        print(f"Connected to Chrome CDP: {ws_url}")

        async with websockets.connect(ws_url) as raw_ws:
            cdp = ChromeCDP(raw_ws)
            await cdp.call("Page.enable")
            await cdp.call("Runtime.enable")
            await cdp.call("Emulation.setDeviceMetricsOverride", {
                "width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False
            })

            # Wait 1.5s for initial telemetry websocket packet
            await asyncio.sleep(1.5)

            # -------------------------------------------------------------
            # TEST 1: All 7 Navigation Tabs Switching & Responsiveness
            # -------------------------------------------------------------
            print("\n[TEST 1] Verifying all 7 Navigation Tabs...")
            tabs = ['mission', 'trajectory', 'telemetry', 'systems', '3dview', 'data', 'settings']
            view_ids = {
                'mission': 'missionView',
                'trajectory': 'trajectoryView',
                'telemetry': 'telemetryView',
                'systems': 'systemsView',
                '3dview': 'view3DPanel',
                'data': 'dataValidationView',
                'settings': 'settingsView'
            }

            for tab in tabs:
                res = await cdp.eval_js(f"""
                    (() => {{
                        switchTab('{tab}');
                        const el = document.getElementById('{view_ids[tab]}');
                        return {{
                            tab: '{tab}',
                            display: el ? window.getComputedStyle(el).display : 'NOT_FOUND',
                            activeClass: document.querySelector('.nav-tab[data-tab="{tab}"]').classList.contains('active')
                        }};
                    }})()
                """)
                print(f"   Tab '{tab}': Display = {res.get('display')}, Active = {res.get('activeClass')}")
                assert res.get('display') in ['grid', 'flex'], f"Tab {tab} did not display correctly!"

                if tab in ['trajectory', 'telemetry', 'systems', '3dview', 'settings']:
                    await cdp.save_screenshot(ARTIFACT_DIR / f"browser_tab_{tab}.png")

            # -------------------------------------------------------------
            # TEST 2: 3D Theater Mode and Camera Presets
            # -------------------------------------------------------------
            print("\n[TEST 2] Testing 3D Theater Mode and Camera Presets...")
            theater_check = await cdp.eval_js("""
                (() => {
                    switchTab('3dview');
                    const canvas = document.getElementById('theaterCanvas');
                    return {
                        hasCanvas: !!canvas,
                        theaterCanvasWidth: canvas ? canvas.clientWidth : 0,
                        theaterCanvasHeight: canvas ? canvas.clientHeight : 0,
                        hasTheaterViewer: !!window.theaterViewer
                    };
                })()
            """)
            print("   3D Theater Sizing Check:", theater_check)
            await asyncio.sleep(0.6)
            await cdp.save_screenshot(ARTIFACT_DIR / "browser_tab_3dview_rendered.png")

            # Test camera presets
            for cam in ['earth', 'moon', 'spacecraft', 'overview']:
                cam_res = await cdp.eval_js(f"""
                    (() => {{
                        const btn = document.querySelector('.preset-cam-btn[data-cam="{cam}"]');
                        if (btn) btn.click();
                        return {{
                            cam: '{cam}',
                            clicked: !!btn,
                            hasViewer: !!window.orbitViewer
                        }};
                    }})()
                """)
                print(f"   Camera preset '{cam}': {cam_res}")

            # -------------------------------------------------------------
            # TEST 3: Return to Mission Control Dashboard & Verify Live Telemetry
            # -------------------------------------------------------------
            print("\n[TEST 3] Returning to MISSION view and verifying live telemetry fields...")
            await cdp.eval_js("switchTab('mission');")
            await asyncio.sleep(0.5)

            live_readouts = await cdp.eval_js("""
                (() => {
                    return {
                        met: document.getElementById('metClock').textContent,
                        utc: document.getElementById('utcClock').textContent,
                        alt: document.getElementById('valAltitude').textContent,
                        vel: document.getElementById('valVelocity').textContent,
                        distMoon: document.getElementById('valDistMoon').textContent,
                        propPct: document.getElementById('valPropPct').textContent,
                        powerPct: document.getElementById('valPowerPct').textContent,
                        thermalPct: document.getElementById('valThermalPct').textContent,
                        commPct: document.getElementById('valCommPct').textContent,
                        atmoAlt: document.getElementById('valAtmoAlt').textContent,
                        q: document.getElementById('valQ').textContent,
                        tempExt: document.getElementById('valTempExt').textContent,
                        solarFlux: document.getElementById('valSolarFlux').textContent,
                        radiation: document.getElementById('valRadiation').textContent,
                        gravity: document.getElementById('valGravity').textContent,
                        fuelPct: document.getElementById('valFuelPct').textContent,
                        currentMass: document.getElementById('valCurrentMass').textContent,
                        fuelKg: document.getElementById('valFuelKg').textContent,
                        sma: document.getElementById('valSMA').textContent,
                        ecc: document.getElementById('valEcc').textContent,
                        inc: document.getElementById('valInc').textContent,
                        eventsDoneCount: document.querySelectorAll('.event-item.done').length,
                        eventsActiveCount: document.querySelectorAll('.event-item.active').length,
                        eventsPendingCount: document.querySelectorAll('.event-item.pending').length
                    };
                })()
            """)
            print("\n=== Live Dashboard Readouts ===")
            print(json.dumps(live_readouts, indent=2))
            await cdp.save_screenshot(ARTIFACT_DIR / "browser_live_mission_readouts.png")

            # -------------------------------------------------------------
            # TEST 4: Performance Graph Interactive Tabs
            # -------------------------------------------------------------
            print("\n[TEST 4] Testing Trajectory & Performance Graph Tabs (Altitude, Velocity, Distance)...")
            for gtype in ['altitude', 'velocity', 'distance']:
                tab_stat = await cdp.eval_js(f"""
                    (() => {{
                        const tab = document.querySelector('.card-performance .mini-tab[data-graph="{gtype}"]');
                        if (tab) tab.click();
                        return {{
                            type: '{gtype}',
                            active: tab ? tab.classList.contains('active') : false,
                            canvasWidth: document.getElementById('perfGraphCanvas').width,
                            canvasHeight: document.getElementById('perfGraphCanvas').height
                        }};
                    }})()
                """)
                print(f"   Graph tab '{gtype}':", tab_stat)
                await asyncio.sleep(0.3)

            # -------------------------------------------------------------
            # TEST 5: Trajectory Timeline Scrubbing & Physics Verification
            # -------------------------------------------------------------
            print("\n[TEST 5] Testing Artemis II 168-Hour Trajectory Scrubbing & ESM Jettison...")
            # Check lunar flyby (T+71h -> tFrac ~ 0.49)
            flyby_state = await cdp.eval_js("""
                (() => {
                    const viewer = window.orbitViewer;
                    if (!viewer) return { error: 'No orbitViewer' };
                    const state71 = viewer.getMissionPositionAndTangent(0.49);
                    return {
                        stage: state71.stage,
                        esmAttached: state71.esmAttached,
                        posX: state71.pos.x.toFixed(2),
                        posY: state71.pos.y.toFixed(2),
                        posZ: state71.pos.z.toFixed(2)
                    };
                })()
            """)
            print("   Lunar Flyby (T+71h) State:", flyby_state)

            # Check Trans-Earth Return (T+120h -> tFrac ~ 0.75)
            return_state = await cdp.eval_js("""
                (() => {
                    const viewer = window.orbitViewer;
                    if (!viewer) return { error: 'No orbitViewer' };
                    const state120 = viewer.getMissionPositionAndTangent(0.75);
                    return {
                        stage: state120.stage,
                        esmAttached: state120.esmAttached,
                        posX: state120.pos.x.toFixed(2),
                        posY: state120.pos.y.toFixed(2),
                        posZ: state120.pos.z.toFixed(2)
                    };
                })()
            """)
            print("   Trans-Earth Return (T+120h) State:", return_state)

            # Check Reentry & Splashdown (T+165h -> tFrac ~ 0.98)
            reentry_state = await cdp.eval_js("""
                (() => {
                    const viewer = window.orbitViewer;
                    if (!viewer) return { error: 'No orbitViewer' };
                    viewer.updateSpacecraftPosition(0.98);
                    const stateReentry = viewer.getMissionPositionAndTangent(0.98);
                    return {
                        stage: stateReentry.stage,
                        esmAttached: stateReentry.esmAttached,
                        esmGroupVisible: viewer.esmGroup.visible,
                        posX: stateReentry.pos.x.toFixed(2),
                        posY: stateReentry.pos.y.toFixed(2),
                        posZ: stateReentry.pos.z.toFixed(2)
                    };
                })()
            """)
            print("   Reentry & Splashdown (T+165h) State:", reentry_state)
            assert reentry_state.get('esmAttached') is False, "ESM should be jettisoned before atmospheric entry!"
            assert reentry_state.get('esmGroupVisible') is False, "ESM 3D group should be hidden during reentry!"
            print("   [+] Verified: ESM successfully jettisoned before atmospheric reentry!")

            await cdp.save_screenshot(ARTIFACT_DIR / "browser_reentry_splashdown_state.png")

            print("\n[+] ALL FULL-STACK BROWSER ACCEPTANCE TESTS PASSED NOMINALLY!")
            cdp.close()

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(run_full_suite())
