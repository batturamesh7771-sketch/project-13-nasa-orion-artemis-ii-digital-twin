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
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_aim1_profile2")
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

            # 1. Main Dashboard (AIM 1 Pad/Launch View)
            print("Capturing 1: Main Dashboard (AIM 1 Pad/Launch View)...")
            await eval_js("setAimViewport(1)")
            await asyncio.sleep(1.0)
            await take_shot("aim1_dashboard_main.png")

            # 2. Scene: PARTS
            print("Capturing 2: Scene PARTS...")
            await eval_js("setLaunchScene('parts')")
            await asyncio.sleep(1.0)
            await take_shot("aim1_scene_parts.png")

            # 3. Scene: VAB STACK
            print("Capturing 3: Scene VAB STACK...")
            await eval_js("setLaunchScene('vab_stack')")
            await asyncio.sleep(1.0)
            await take_shot("aim1_scene_vab.png")

            # 4. Scene: PAD READY
            print("Capturing 4: Scene PAD READY...")
            await eval_js("setLaunchScene('pad_ready')")
            await asyncio.sleep(1.0)
            await take_shot("aim1_scene_pad_ready.png")

            # 5. Scene: FLIGHT (ASCENT)
            print("Capturing 5: Scene FLIGHT (ASCENT)...")
            await eval_js("setLaunchScene('flight')")
            await asyncio.sleep(1.0)
            await take_shot("aim1_scene_flight.png")

            # 6. Viewport: AIM 2 EARTH-MOON TRAJECTORY
            print("Capturing 6: AIM 2 Earth-Moon Trajectory...")
            await eval_js("setAimViewport(2)")
            await asyncio.sleep(1.0)
            await take_shot("aim2_earth_moon_viewport.png")

            # 7. Viewport: AIM 3 REENTRY
            print("Capturing 7: AIM 3 Skip Reentry...")
            await eval_js("setAimViewport(3)")
            await asyncio.sleep(1.0)
            await take_shot("aim3_reentry_viewport.png")

            # 8. Reset to AIM 1 and open Vehicle Modal
            print("Capturing 8: Vehicle Modal...")
            await eval_js("setAimViewport(1); openVehicleModal();")
            await asyncio.sleep(1.0)
            await take_shot("aim1_vehicle_modal.png")

            # 9. Verify console status
            status = await eval_js("""
                JSON.stringify({
                    hasLaunchViewer: !!window.launchViewer,
                    hasOrbitViewer: !!window.orbitViewer,
                    hasSpacecraftViewer: !!window.spacecraftViewer
                })
            """)
            print("Viewer statuses:", status)

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(capture_all())
