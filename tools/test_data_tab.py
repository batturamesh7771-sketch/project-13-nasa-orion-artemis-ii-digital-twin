import subprocess
import time
import urllib.request
import json
import base64
import asyncio
import websockets
from pathlib import Path

ARTIFACT_DIR = Path(r"C:\Users\user\.gemini\antigravity\brain\bd4d2104-51f7-4d68-b523-07c931a12cbb")
SCREENSHOT_PATH = ARTIFACT_DIR / "actual_data_view_render.png"

async def test_data_tab():
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_data_test_profile")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9223",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "--window-size=1440,900",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
    try:
        await asyncio.sleep(2.5)
        resp = urllib.request.urlopen("http://localhost:9223/json")
        targets = json.loads(resp.read().decode())
        page_target = next(t for t in targets if t.get("type") == "page" and "127.0.0.1:8000" in t.get("url", ""))
        
        async with websockets.connect(page_target["webSocketDebuggerUrl"]) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
            await ws.send(json.dumps({"id": 2, "method": "Runtime.enable"}))
            
            # Set 1440x900 viewport
            await ws.send(json.dumps({
                "id": 3,
                "method": "Emulation.setDeviceMetricsOverride",
                "params": {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False}
            }))
            await asyncio.sleep(1.0)

            # Click DATA tab
            await ws.send(json.dumps({
                "id": 4,
                "method": "Runtime.evaluate",
                "params": {"expression": "document.querySelector('.nav-tab[data-tab=\"data\"]').click()"}
            }))
            await ws.recv()
            await asyncio.sleep(1.0)
            
            # Capture Screenshot of Data View
            await ws.send(json.dumps({"id": 5, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
            while True:
                shot_resp = await ws.recv()
                msg = json.loads(shot_resp)
                if msg.get("id") == 5:
                    data = msg["result"]["data"]
                    with open(SCREENSHOT_PATH, "wb") as f:
                        f.write(base64.b64decode(data))
                    print(f"[+] Successfully captured Data & Validation View screenshot to: {SCREENSHOT_PATH}")
                    break
    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(test_data_tab())
