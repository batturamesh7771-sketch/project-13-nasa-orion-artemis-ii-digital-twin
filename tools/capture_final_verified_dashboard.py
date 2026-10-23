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

async def send_cmd(ws, method, params=None, timeout=10.0):
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
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_final_verified_profile")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "--window-size=1600,1000",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
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
        print(f"Connecting to CDP: {ws_url}")

        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
            await send_cmd(ws, "Page.enable")
            await send_cmd(ws, "Runtime.enable")
            await send_cmd(ws, "Emulation.setDeviceMetricsOverride", {
                "width": 1600,
                "height": 1000,
                "deviceScaleFactor": 1,
                "mobile": False
            })

            async def eval_js(expr):
                res = await send_cmd(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
                return res.get("result", {}).get("result", {}).get("value")

            async def take_shot(filename):
                res = await send_cmd(ws, "Page.captureScreenshot", {"format": "png"})
                data = res.get("result", {}).get("data", "")
                if data:
                    out_path = ARTIFACT_DIR / filename
                    with open(out_path, "wb") as f:
                        f.write(base64.b64decode(data))
                    print(f"[+] Saved {filename} ({len(data)} bytes)")
                else:
                    print(f"[-] Failed to get data for {filename}")

            await asyncio.sleep(3.0)

            # 1. Main Dashboard (AIM 1 Pad/Launch View matching media_1792495370384_068d0358.jpg)
            print("Capturing 1: Main Dashboard matching media_1792495370384_068d0358.jpg...")
            await eval_js("switchTab('mission'); selectAim(1); setLaunchScene('liftoff');")
            await asyncio.sleep(1.5)
            await take_shot("final_dashboard_aim1_main.png")

            # 2. Scene: Assembly (CAD / Exploded View)
            print("Capturing 2: Scene Assembly...")
            await eval_js("setLaunchScene('assembly')")
            await asyncio.sleep(1.0)
            await take_shot("final_scene_assembly.png")

            # 3. Scene: Booster Separation
            print("Capturing 3: Scene Booster Sep...")
            await eval_js("setLaunchScene('booster_sep')")
            await asyncio.sleep(1.0)
            await take_shot("final_scene_booster_sep.png")

            # 4. Tab: DATA & VALIDATION
            print("Capturing 4: Tab DATA & VALIDATION...")
            await eval_js("switchTab('data')")
            await asyncio.sleep(1.0)
            await take_shot("final_tab_data_validation.png")

            # 5. Tab: TRAJECTORY
            print("Capturing 5: Tab TRAJECTORY...")
            await eval_js("switchTab('trajectory')")
            await asyncio.sleep(1.0)
            await take_shot("final_tab_trajectory.png")

            # 6. Tab: 3D CAD / ASSEMBLY
            print("Capturing 6: Tab 3D CAD / ASSEMBLY...")
            await eval_js("switchTab('cad')")
            await asyncio.sleep(1.0)
            await take_shot("final_tab_cad_assembly.png")

            # Reset to Main Mission Dashboard
            await eval_js("switchTab('mission'); setLaunchScene('liftoff');")
            await asyncio.sleep(0.5)

            # 7. Check Console Errors and Status
            status = await eval_js("""
                JSON.stringify({
                    hasLaunchViewer: !!window.launchViewer,
                    hasOrbitViewer: !!window.orbitViewer,
                    title: document.title,
                    hdrMet: document.getElementById('hdrMet') ? document.getElementById('hdrMet').textContent : null,
                    hdrUtc: document.getElementById('hdrUtc') ? document.getElementById('hdrUtc').textContent : null,
                    rtAlt: document.getElementById('rtAlt') ? document.getElementById('rtAlt').textContent : null,
                    rtVelInertial: document.getElementById('rtVelInertial') ? document.getElementById('rtVelInertial').textContent : null
                })
            """)
            print("Verification Summary:", status)

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(capture_all())
