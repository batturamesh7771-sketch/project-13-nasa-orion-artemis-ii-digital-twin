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
responses = {}

async def reader(ws):
    try:
        async for msg in ws:
            data = json.loads(msg)
            if "id" in data:
                responses[data["id"]] = data
    except Exception:
        pass

async def send_cmd(ws, method, params=None, timeout=30.0):
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
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_capture_views_profile")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9224",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "--window-size=1920,1080",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
    
    try:
        await asyncio.sleep(2.5)
        resp = urllib.request.urlopen("http://localhost:9224/json")
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
            # Start background reader task
            asyncio.create_task(reader(ws))

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

            await asyncio.sleep(2.0)

            # 1. Data & Validation Tab with Live GMAT Execution
            print("\n--- 1. Data & Validation Tab with Live GMAT Execution ---")
            await eval_js("switchTab('data');")
            await asyncio.sleep(1.0)
            print("Executing GMAT benchmark...")
            await eval_js("executeGmatBenchmark();")
            await asyncio.sleep(4.5)
            await take_shot("data_validation_live_gmat_result.png")

            # 2. Trajectory Full Tab
            print("\n--- 2. Trajectory Tab ---")
            await eval_js("switchTab('trajectory');")
            await asyncio.sleep(1.0)
            await take_shot("tab_trajectory_overview.png")

            # 3. Telemetry Full Tab
            print("\n--- 3. Telemetry Tab ---")
            await eval_js("switchTab('telemetry');")
            await asyncio.sleep(1.0)
            await take_shot("tab_telemetry_sensor_bus.png")

            # 4. Systems Full Tab
            print("\n--- 4. Systems Tab ---")
            await eval_js("switchTab('systems');")
            await asyncio.sleep(1.0)
            await take_shot("tab_systems_overview.png")

            # 5. 3D View (Theater) Full Tab
            print("\n--- 5. 3D View (Theater) Tab ---")
            await eval_js("switchTab('3dview');")
            await asyncio.sleep(1.0)
            await take_shot("tab_3d_theater_view.png")

            # 6. Return to Mission View
            print("\n--- 6. Return to Mission Dashboard ---")
            await eval_js("switchTab('mission');")
            await asyncio.sleep(1.0)

            print("\n[+] ALL TABS AND GMAT BENCHMARK RUN SUCCESSFULLY CAPTURED!")

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(main())
