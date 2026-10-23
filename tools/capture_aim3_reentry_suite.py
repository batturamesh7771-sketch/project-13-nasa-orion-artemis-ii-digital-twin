import subprocess
import time
import urllib.request
import json
import base64
import asyncio
import websockets
from pathlib import Path

ARTIFACT_DIR = Path(r"C:\Users\user\.gemini\antigravity\brain\bd4d2104-51f7-4d68-b523-07c931a12cbb")
req_id = 400
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
    user_data = Path(rf"C:\Users\user\AppData\Local\Temp\chrome_reentry_{int(time.time())}")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9235",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "--disable-cache",
        "--window-size=1920,1080",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
    
    try:
        await asyncio.sleep(3.0)
        resp = urllib.request.urlopen("http://localhost:9235/json")
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
        print(f"Connecting to Chrome CDP on port 9235: {ws_url}")

        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
            asyncio.create_task(reader(ws))

            async def eval_js(expr):
                res = await send_cmd(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
                if "exceptionDetails" in res.get("result", {}):
                    print(f"[!] JS EXCEPTION on '{expr}': {res['result']['exceptionDetails']}")
                val = res.get("result", {}).get("result", {}).get("value")
                print(f"[eval] '{expr}' => {val}")
                return val

            async def take_shot(filename, width=1920, height=1080):
                await send_cmd(ws, "Emulation.setDeviceMetricsOverride", {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 1,
                    "mobile": False
                })
                await asyncio.sleep(1.0)
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

            # Switch to AIM 3 Viewport
            print("\n--- Switching to AIM 3: REENTRY & RECOVERY ---")
            await eval_js("switchTab('mission'); setAimViewport(3);")
            await asyncio.sleep(1.5)

            # 1. Entry Interface (25,000 MPH / Mach 32.4)
            print("\n--- 1. Capturing Entry Interface (25,000 MPH) ---")
            await eval_js("setReentryMode('entry_interface');")
            await asyncio.sleep(2.0)
            await take_shot("aim3_entry_interface_25k_mph.png", 1920, 1080)

            # 2. Peak Heating & Skip (5,000°F / 2,760°C)
            print("\n--- 2. Capturing Peak Heating & Skip (5,000°F) ---")
            await eval_js("setReentryMode('peak_heating');")
            await asyncio.sleep(2.0)
            await take_shot("aim3_peak_heating_5000f_skip.png", 1920, 1080)

            # 3. Drogue Parachutes
            print("\n--- 3. Capturing Drogue Parachutes ---")
            await eval_js("setReentryMode('drogue_chutes');")
            await asyncio.sleep(2.0)
            await take_shot("aim3_drogue_parachutes.png", 1920, 1080)

            # 4. Main Parachutes (Orange and White Striped Ring-Sail)
            print("\n--- 4. Capturing Main Parachutes (Orange & White) ---")
            await eval_js("setReentryMode('main_chutes');")
            await asyncio.sleep(2.0)
            await take_shot("aim3_main_parachutes_orange_white.png", 1920, 1080)

            # 5. Splashdown with 5 Orange CMUS Balloons
            print("\n--- 5. Capturing Splashdown with 5 Orange CMUS Balloons ---")
            await eval_js("setReentryMode('splashdown');")
            await asyncio.sleep(2.0)
            await take_shot("aim3_pacific_splashdown_cmus.png", 1920, 1080)

            # 6. Navy Recovery Operations (USS Portland & RHIB)
            print("\n--- 6. Capturing Navy Recovery Operations (USS Portland & RHIB) ---")
            await eval_js("setReentryMode('recovery_ops');")
            await asyncio.sleep(2.0)
            await take_shot("aim3_navy_recovery_uss_portland.png", 1920, 1080)

            print("\n[+] All AIM 3 Reentry & Recovery Suite Screenshots Successfully Captured!")

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(main())
