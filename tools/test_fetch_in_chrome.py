import asyncio
import websockets
import json
import subprocess
import urllib.request
import time
from pathlib import Path

async def test_fetch():
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_fetch_test")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9226",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "--window-size=1440,900",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
    try:
        await asyncio.sleep(2.5)
        resp = urllib.request.urlopen("http://localhost:9226/json")
        targets = json.loads(resp.read().decode())
        target = next(t for t in targets if "127.0.0.1:8000" in t.get("url", ""))
        async with websockets.connect(target["webSocketDebuggerUrl"]) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            await ws.recv()
            
            expr = """
            (async () => {
                const t0 = performance.now();
                const res = await fetch('/api/validation/run');
                const t1 = performance.now();
                const json = await res.json();
                return {
                    status: res.status,
                    ok: res.ok,
                    durationMs: Math.round(t1 - t0),
                    success: json.success,
                    outLen: json.output ? json.output.length : 0,
                    outPreview: json.output ? json.output.substring(0, 150) : null
                };
            })()
            """
            await ws.send(json.dumps({
                "id": 2,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": expr,
                    "awaitPromise": True,
                    "returnByValue": True
                }
            }))
            res = await ws.recv()
            print("FETCH EVALUATION IN BROWSER:")
            print(res)
    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(test_fetch())
