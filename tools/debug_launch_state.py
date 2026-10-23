import subprocess
import time
import urllib.request
import json
import asyncio
import websockets
from pathlib import Path

async def debug_launch():
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_debug_profile")
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
        await asyncio.sleep(2.0)
        resp = urllib.request.urlopen("http://localhost:9222/json")
        targets = json.loads(resp.read().decode())
        ws_url = [t["webSocketDebuggerUrl"] for t in targets if "127.0.0.1:8000" in t.get("url", "")][0]
        async with websockets.connect(ws_url) as ws:
            async def send_req(method, params=None):
                await ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
                while True:
                    r = json.loads(await ws.recv())
                    if r.get("id") == 1:
                        return r

            await send_req("Runtime.enable")
            await asyncio.sleep(1.0)
            res = await send_req("Runtime.evaluate", {
                "expression": """
                (function() {
                    try {
                        var c = document.getElementById('launchCanvas');
                        if (!c) return 'launchCanvas not found';
                        var v = new SLSLaunchViewer3D('launchCanvas');
                        window.launchViewer = v;
                        return 'SUCCESS created SLSLaunchViewer3D';
                    } catch(e) {
                        return 'ERROR: ' + e.name + ' - ' + e.message + ' Stack: ' + e.stack;
                    }
                })()
                """,
                "returnByValue": True
            })
            val = res.get("result", {}).get("result", {}).get("value")
            print("LAUNCH VIEWER INSTANTIATION RESULT:", val)
    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(debug_launch())
