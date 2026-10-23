import asyncio
import websockets
import json
import subprocess
import urllib.request
import time
from pathlib import Path

async def debug_gmat():
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_debug_profile")
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
        target = next(t for t in targets if "127.0.0.1:8000" in t.get("url", ""))
        async with websockets.connect(target["webSocketDebuggerUrl"]) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
            await ws.send(json.dumps({"id": 2, "method": "Runtime.enable"}))
            await ws.send(json.dumps({"id": 3, "method": "Console.enable"}))
            
            # Click DATA tab and trigger GMAT button
            print("[+] Clicking DATA tab and GMAT live button...")
            await ws.send(json.dumps({
                "id": 4,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "window.switchTab('data'); document.getElementById('btnRunGmatLive').click(); 'Triggered';",
                    "returnByValue": True
                }
            }))
            
            # Listen to events for 10 seconds
            start_t = time.time()
            while time.time() - start_t < 10.0:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(msg)
                    if "method" in data:
                        method = data["method"]
                        if "console" in method.lower() or "exception" in method.lower():
                            print(f"EVENT [{method}]:", json.dumps(data.get("params", {})))
                    elif data.get("id") == 4:
                        print("TRIGGER EVAL RESULT:", data)
                except asyncio.TimeoutError:
                    pass

            # Check output DOM state
            await ws.send(json.dumps({
                "id": 5,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "JSON.stringify({ disabled: document.getElementById('btnRunGmatLive').disabled, len: document.getElementById('gmatLiveOutput').textContent.length, text: document.getElementById('gmatLiveOutput').textContent })",
                    "returnByValue": True
                }
            }))
            res = await ws.recv()
            print("\nFINAL OUTPUT STATE:")
            print(res)
    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(debug_gmat())
