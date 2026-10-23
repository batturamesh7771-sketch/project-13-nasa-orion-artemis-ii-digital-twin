import subprocess
import time
import urllib.request
import json
import base64
import asyncio
import websockets
from pathlib import Path

ARTIFACT_DIR = Path(r"C:\Users\user\.gemini\antigravity\brain\bd4d2104-51f7-4d68-b523-07c931a12cbb")
req_id = 0

async def send_cmd(ws, method, params=None, timeout=15.0):
    global req_id
    req_id += 1
    current_id = req_id
    msg = {"id": current_id, "method": method}
    if params:
        msg["params"] = params
    await ws.send(json.dumps(msg))
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        res_raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        res = json.loads(res_raw)
        if res.get("id") == current_id:
            return res
    raise TimeoutError(f"Timed out waiting for response to id {current_id}")

async def capture_all():
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_artemis_verify_profile")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "--window-size=1920,1080",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
    console_errors = []
    
    try:
        await asyncio.sleep(2.5)
        resp = urllib.request.urlopen("http://localhost:9222/json")
        targets = json.loads(resp.read().decode())
        page_target = None
        for t in targets:
            if t.get("type") == "page" and "127.0.0.1:8000" in t.get("url", ""):
                page_target = t
                break
        if not page_target:
            print("ERROR: Page target not found in Chrome!")
            return

        ws_url = page_target["webSocketDebuggerUrl"]
        print(f"Connecting to Chrome CDP: {ws_url}")

        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
            await send_cmd(ws, "Page.enable")
            await send_cmd(ws, "Runtime.enable")

            async def eval_js(expr):
                res = await send_cmd(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
                return res.get("result", {}).get("result", {}).get("value")

            async def take_shot(filename, width=1920, height=1080):
                await send_cmd(ws, "Emulation.setDeviceMetricsOverride", {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 1,
                    "mobile": False
                })
                await asyncio.sleep(0.5)
                res = await send_cmd(ws, "Page.captureScreenshot", {"format": "png"})
                data = res.get("result", {}).get("data", "")
                if data:
                    out_path = ARTIFACT_DIR / filename
                    with open(out_path, "wb") as f:
                        f.write(base64.b64decode(data))
                    print(f"[+] Saved {filename} ({len(data)} bytes, {width}x{height})")
                else:
                    print(f"[-] Failed to get data for {filename}")

            await asyncio.sleep(3.0)

            # 1. Main Dashboard at 1920x1080 (AIM 1 Pad/Launch View)
            print("\n--- 1. Capturing Main Dashboard at 1920x1080 ---")
            await eval_js("switchTab('mission'); setAimViewport(1); setLaunchScene('liftoff');")
            await asyncio.sleep(2.0)
            await take_shot("dashboard_desktop_1920x1080.png", 1920, 1080)

            # 2. Main Dashboard at 1366x768 (Desktop Standard Resolution)
            print("\n--- 2. Capturing Main Dashboard at 1366x768 ---")
            await asyncio.sleep(1.0)
            await take_shot("dashboard_desktop_1366x768.png", 1366, 768)

            # Revert viewport to 1920x1080 for subsequent views
            await send_cmd(ws, "Emulation.setDeviceMetricsOverride", {
                "width": 1920,
                "height": 1080,
                "deviceScaleFactor": 1,
                "mobile": False
            })

            # 3. AIM 2: Earth-Moon Lunar Trajectory Viewport
            print("\n--- 3. Capturing AIM 2: Earth-Moon Trajectory View ---")
            await eval_js("switchTab('mission'); setAimViewport(2);")
            await asyncio.sleep(2.0)
            await take_shot("aim2_earth_moon_lunar_orbit.png", 1920, 1080)

            # 4. AIM 3: Reentry & Recovery Viewport
            print("\n--- 4. Capturing AIM 3: Reentry & Recovery View ---")
            await eval_js("switchTab('mission'); setAimViewport(3); setReentryMode('entry_interface');")
            await asyncio.sleep(2.0)
            await take_shot("aim3_reentry_parachutes.png", 1920, 1080)

            # 5. Dedicated 3D CAD & Vehicle Assembly Suite
            print("\n--- 5. Capturing 3D CAD & Vehicle Assembly Suite ---")
            await eval_js("switchTab('cad'); switchCadModel('sls');")
            await asyncio.sleep(2.0)
            await take_shot("cad_assembly_suite.png", 1920, 1080)

            # 6. Tab: DATA & VALIDATION
            print("\n--- 6. Capturing DATA & VALIDATION Tab ---")
            await eval_js("switchTab('data');")
            await asyncio.sleep(1.5)
            await take_shot("data_validation_benchmarks.png", 1920, 1080)

            # 7. Execute Live GMAT Benchmark
            print("\n--- 7. Executing Live GMAT Benchmark and Capturing Results ---")
            await eval_js("executeGmatBenchmark();")
            # Wait for GMAT execution to finish (takes ~3s)
            await asyncio.sleep(4.5)
            await take_shot("data_validation_live_gmat_result.png", 1920, 1080)

            # 8. Tab: TRAJECTORY
            print("\n--- 8. Capturing TRAJECTORY Tab ---")
            await eval_js("switchTab('trajectory');")
            await asyncio.sleep(1.5)
            await take_shot("tab_trajectory_overview.png", 1920, 1080)

            # 9. Return to Main Mission View and Validate Telemetry Elements
            print("\n--- 9. Verifying Live Synchronized Mission Elements ---")
            await eval_js("switchTab('mission'); setAimViewport(1);")
            await asyncio.sleep(1.5)

            status = await eval_js("""
                JSON.stringify({
                    hasLaunchViewer: !!window.launchViewer,
                    hasOrbitViewer: !!window.orbitViewer,
                    hasSpacecraftViewer: !!window.spacecraftViewer,
                    hasCadViewer: !!window.cadViewer,
                    title: document.title,
                    hdrMet: document.getElementById('hdrMet')?.textContent,
                    hdrMetSub: document.getElementById('hdrMetSub')?.textContent,
                    hdrUtc: document.getElementById('hdrUtc')?.textContent,
                    hudStage: document.getElementById('hudStage')?.textContent,
                    hudAlt: document.getElementById('hudAlt')?.textContent,
                    hudVel: document.getElementById('hudVel')?.textContent,
                    hudQ: document.getElementById('hudQ')?.textContent,
                    hudThrust: document.getElementById('hudThrust')?.textContent,
                    orbSMA: document.getElementById('orbSMA')?.textContent,
                    orbEcc: document.getElementById('orbEcc')?.textContent,
                    stPhase: document.getElementById('stPhase')?.textContent,
                    stAlt: document.getElementById('stAlt')?.textContent,
                    stVel: document.getElementById('stVel')?.textContent,
                    stDistMoon: document.getElementById('stDistMoon')?.textContent,
                    mfMass: document.getElementById('mfMass')?.textContent,
                    mfProp: document.getElementById('mfProp')?.textContent,
                    envAlt: document.getElementById('envAlt')?.textContent,
                    envTemp: document.getElementById('envTemp')?.textContent
                })
            """)
            print("\n=== LIVE VERIFIED TELEMETRY STATE ===")
            print(json.dumps(json.loads(status), indent=2))

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(capture_all())
