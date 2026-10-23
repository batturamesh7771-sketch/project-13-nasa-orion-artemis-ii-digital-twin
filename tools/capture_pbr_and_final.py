import subprocess
import time
import urllib.request
import json
import base64
import asyncio
import websockets
from pathlib import Path

ARTIFACT_DIR = Path(r"C:\Users\user\.gemini\antigravity\brain\bd4d2104-51f7-4d68-b523-07c931a12cbb")
req_id = 200
responses = {}

async def reader(ws):
    try:
        async for msg in ws:
            data = json.loads(msg)
            if "id" in data:
                responses[data["id"]] = data
    except Exception:
        pass

async def send_cmd(ws, method, params=None, timeout=25.0):
    global req_id
    req_id += 1
    cid = req_id
    msg = {"id": cid, "method": method}
    if params:
        msg["params"] = params
    await ws.send(json.dumps(msg))
    
    start = time.time()
    while time.time() - start < timeout:
        if cid in responses:
            return responses.pop(cid)
        await asyncio.sleep(0.05)
    raise TimeoutError(f"Timed out on {method} (id={cid})")

async def main():
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_pbr_final_profile")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9225",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "--window-size=1920,1080",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
    
    try:
        await asyncio.sleep(2.5)
        resp = urllib.request.urlopen("http://localhost:9225/json")
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
            asyncio.create_task(reader(ws))

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
                await asyncio.sleep(0.6)
                res = await send_cmd(ws, "Page.captureScreenshot", {"format": "png"})
                data = res.get("result", {}).get("data", "")
                if data:
                    out_path = ARTIFACT_DIR / filename
                    with open(out_path, "wb") as f:
                        f.write(base64.b64decode(data))
                    print(f"[+] Saved {filename} ({len(data)} bytes, {width}x{height})")
                else:
                    print(f"[-] Failed to get data for {filename}")

            await asyncio.sleep(2.0)

            # 1. Main Dashboard at 1920x1080
            print("\n--- 1. Capturing Main Dashboard at 1920x1080 ---")
            await eval_js("switchTab('mission'); setAimViewport(1);")
            await asyncio.sleep(1.5)
            await take_shot("dashboard_desktop_1920x1080.png", 1920, 1080)

            # 2. Main Dashboard at 1366x768
            print("\n--- 2. Capturing Main Dashboard at 1366x768 ---")
            await asyncio.sleep(1.0)
            await take_shot("dashboard_desktop_1366x768.png", 1366, 768)

            # Revert viewport to 1920x1080
            await send_cmd(ws, "Emulation.setDeviceMetricsOverride", {
                "width": 1920,
                "height": 1080,
                "deviceScaleFactor": 1,
                "mobile": False
            })

            # 3. 3D CAD: Orion PBR 3D (Sketchfab Embed)
            print("\n--- 3. Capturing CAD Suite: Orion PBR 3D Model ---")
            await eval_js("switchTab('cad'); switchCadModel('orion_pbr');")
            await asyncio.sleep(2.5)
            await take_shot("cad_orion_pbr_sketchfab.png", 1920, 1080)

            # 4. 3D CAD: SLS Rocket 3D (Sketchfab Embed)
            print("\n--- 4. Capturing CAD Suite: SLS Rocket 3D Model ---")
            await eval_js("switchTab('cad'); switchCadModel('sls_pbr');")
            await asyncio.sleep(2.5)
            await take_shot("cad_sls_sketchfab.png", 1920, 1080)

            # 5. 3D View (Theater): Orion PBR 3D
            print("\n--- 5. Capturing 3D View (Theater): Orion PBR 3D ---")
            await eval_js("switchTab('3dview'); setTheaterMode('orion');")
            await asyncio.sleep(2.5)
            await take_shot("theater_orion_pbr.png", 1920, 1080)

            # 6. 3D View (Theater): SLS Rocket 3D
            print("\n--- 6. Capturing 3D View (Theater): SLS Rocket 3D ---")
            await eval_js("switchTab('3dview'); setTheaterMode('sls');")
            await asyncio.sleep(2.5)
            await take_shot("theater_sls_sketchfab.png", 1920, 1080)

            # 7. Data & Validation Tab (with NASA API Key verification)
            print("\n--- 7. Capturing Data & Validation View ---")
            await eval_js("switchTab('data');")
            await asyncio.sleep(1.5)
            await take_shot("data_validation_benchmarks.png", 1920, 1080)

            # 8. Return to Main Mission View
            print("\n--- 8. Return to Mission View ---")
            await eval_js("switchTab('mission');")
            await asyncio.sleep(1.0)

            print("\n[+] Verification and Final Screenshots Complete!")

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(main())
