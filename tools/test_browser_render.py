import subprocess
import time
import urllib.request
import json
import base64
import asyncio
import websockets
from pathlib import Path

ARTIFACT_DIR = Path(r"C:\Users\user\.gemini\antigravity\brain\bd4d2104-51f7-4d68-b523-07c931a12cbb")
SCREENSHOT_PATH = ARTIFACT_DIR / "actual_browser_render.png"

async def capture():
    # 1. Start Chrome with remote debugging
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_cdp_profile")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "--window-size=1440,900",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
    try:
        await asyncio.sleep(2.5)
        # 2. Get target page ws url
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
        print(f"Connecting to CDP WebSocket: {ws_url}")

        async with websockets.connect(ws_url) as ws:
            # Enable Console, Runtime, Page
            await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
            await ws.send(json.dumps({"id": 2, "method": "Console.enable"}))
            await ws.send(json.dumps({"id": 3, "method": "Runtime.enable"}))
            
            # Set device metrics to 1440x900
            await ws.send(json.dumps({
                "id": 4,
                "method": "Emulation.setDeviceMetricsOverride",
                "params": {
                    "width": 1440,
                    "height": 900,
                    "deviceScaleFactor": 1,
                    "mobile": False
                }
            }))

            # Collect messages for 3 seconds to capture console errors and let Three.js render
            messages = []
            console_errors = []
            
            start_t = time.time()
            while time.time() - start_t < 3.5:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                    data = json.loads(msg)
                    if data.get("method") == "Console.messageAdded":
                        console_errors.append(data["params"]["message"])
                    elif data.get("method") == "Runtime.consoleAPICalled":
                        console_errors.append(data["params"])
                    elif data.get("method") == "Runtime.exceptionThrown":
                        console_errors.append(data["params"])
                except asyncio.TimeoutError:
                    pass

            print("\n=== BROWSER CONSOLE ERRORS & LOGS ===")
            for err in console_errors:
                print(err)

            # Query DOM metrics for layout verification
            eval_req = {
                "id": 10,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": """
                    JSON.stringify({
                        bodyWidth: document.body.clientWidth,
                        bodyHeight: document.body.clientHeight,
                        colLeftRect: document.querySelector('.col-left') ? document.querySelector('.col-left').getBoundingClientRect() : null,
                        colCenterRect: document.querySelector('.col-center') ? document.querySelector('.col-center').getBoundingClientRect() : null,
                        colRightRect: document.querySelector('.col-right') ? document.querySelector('.col-right').getBoundingClientRect() : null,
                        orbitCanvasRect: document.querySelector('#orbitCanvas') ? document.querySelector('#orbitCanvas').getBoundingClientRect() : null,
                        spacecraftCanvasRect: document.querySelector('#spacecraftCanvas') ? document.querySelector('#spacecraftCanvas').getBoundingClientRect() : null,
                        computedNavTabBg: document.querySelector('.nav-tab') ? window.getComputedStyle(document.querySelector('.nav-tab')).backgroundColor : null,
                        computedNavTabBorder: document.querySelector('.nav-tab') ? window.getComputedStyle(document.querySelector('.nav-tab')).border : null,
                        computedNavTabColor: document.querySelector('.nav-tab') ? window.getComputedStyle(document.querySelector('.nav-tab')).color : null
                    })
                    """
                }
            }
            await ws.send(json.dumps(eval_req))
            eval_resp = await ws.recv()
            print("\n=== DOM LAYOUT COMPUTED METRICS ===")
            eval_data = json.loads(eval_resp)
            dom_info = json.loads(eval_data.get("result", {}).get("result", {}).get("value", "{}"))
            print(json.dumps(dom_info, indent=2))

            # Take Screenshot
            shot_req = {"id": 20, "method": "Page.captureScreenshot", "params": {"format": "png"}}
            await ws.send(json.dumps(shot_req))
            shot_resp = await ws.recv()
            shot_data = json.loads(shot_resp)
            png_base64 = shot_data.get("result", {}).get("data", "")
            if png_base64:
                with open(SCREENSHOT_PATH, "wb") as f:
                    f.write(base64.b64decode(png_base64))
                print(f"\n[+] Successfully saved screenshot to: {SCREENSHOT_PATH}")
            else:
                print("\n[-] Failed to capture screenshot data.")

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(capture())
