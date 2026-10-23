import subprocess
import time
import urllib.request
import json
import asyncio
import websockets
from pathlib import Path

async def main():
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_debug_profile")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9227",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
    try:
        await asyncio.sleep(2.5)
        resp = urllib.request.urlopen("http://localhost:9227/json")
        targets = json.loads(resp.read().decode())
        ws_url = targets[0]["webSocketDebuggerUrl"]
        
        async with websockets.connect(ws_url) as ws:
            responses = {}
            async def reader():
                async for msg in ws:
                    data = json.loads(msg)
                    if "method" in data and "console" in data["method"].lower():
                        print("[CONSOLE]", data.get("params", {}).get("message", {}).get("text", data))
                    elif "method" in data and data["method"] == "Runtime.exceptionThrown":
                        print("[EXCEPTION]", data.get("params", {}).get("exceptionDetails", {}))
                    elif "id" in data:
                        responses[data["id"]] = data

            asyncio.create_task(reader())
            
            async def send_cmd(method, params=None):
                nonlocal req_id
                req_id += 1
                cid = req_id
                await ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
                st = time.time()
                while time.time() - st < 5.0:
                    if cid in responses:
                        return responses.pop(cid)
                    await asyncio.sleep(0.05)
                return {}

            req_id = 10
            await send_cmd("Runtime.enable")
            await send_cmd("Console.enable")
            
            r3 = await send_cmd("Runtime.evaluate", {"expression": "window.spacecraftViewer !== undefined", "returnByValue": True})
            print("spacecraftViewer exists:", r3.get("result", {}).get("result", {}).get("value"))
            
            r4 = await send_cmd("Runtime.evaluate", {"expression": "try { window.spacecraftViewer.setReentryPhase('main_chutes'); 'SUCCESS'; } catch(e) { e.stack; }", "returnByValue": True})
            print("Call result:", r4.get("result", {}).get("result", {}).get("value"))

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(main())
