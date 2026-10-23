import subprocess
import time
import urllib.request
import json
import base64
import asyncio
import websockets
from pathlib import Path

ARTIFACT_DIR = Path(r"C:\Users\user\.gemini\antigravity\brain\bd4d2104-51f7-4d68-b523-07c931a12cbb")
req_id = 100

async def send_cmd(ws, method, params=None, timeout=20.0):
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

async def main():
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_data_gmat_profile")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9223",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "--window-size=1920,1080",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
    
    try:
        await asyncio.sleep(2.5)
        resp = urllib.request.urlopen("http://localhost:9223/json")
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

            # 1. Switch to Data & Validation tab
            print("Switching to Data & Validation...")
            await eval_js("switchTab('data');")
            await asyncio.sleep(1.5)
            await take_shot("data_validation_benchmarks.png")

            # 2. Trigger Live GMAT Benchmark
            print("Triggering executeGmatBenchmark()...")
            await eval_js("executeGmatBenchmark();")
            # Wait for backend GMAT execution
            await asyncio.sleep(5.0)
            await take_shot("data_validation_live_gmat_result.png")

            # 3. Switch to Trajectory tab
            print("Switching to Trajectory...")
            await eval_js("switchTab('trajectory');")
            await asyncio.sleep(1.5)
            await take_shot("tab_trajectory_overview.png")

            # 4. Switch to Systems tab
            print("Switching to Systems...")
            await eval_js("switchTab('systems');")
            await asyncio.sleep(1.5)
            await take_shot("tab_systems_overview.png")

            # 5. Switch to 3D View (Theater)
            print("Switching to 3D View (Theater)...")
            await eval_js("switchTab('3dview');")
            await asyncio.sleep(1.5)
            await take_shot("tab_3d_theater_view.png")

            print("\n[+] All Validation, GMAT, and Tab Screenshots captured successfully!")

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(main())
