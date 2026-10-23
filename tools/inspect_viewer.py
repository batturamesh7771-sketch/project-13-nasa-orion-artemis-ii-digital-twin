import subprocess
import time
import urllib.request
import json
import asyncio
import websockets
from pathlib import Path

async def main():
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_inspect_profile")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9232",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
    try:
        await asyncio.sleep(2.5)
        resp = urllib.request.urlopen("http://localhost:9232/json")
        targets = json.loads(resp.read().decode())
        page_target = None
        for t in targets:
            if t.get("type") == "page" and "8000" in t.get("url", ""):
                page_target = t
                break
        if not page_target:
            for t in targets:
                if t.get("type") == "page":
                    page_target = t
                    break
        ws_url = page_target["webSocketDebuggerUrl"]
        
        async with websockets.connect(ws_url) as ws:
            responses = {}
            async def reader():
                async for msg in ws:
                    data = json.loads(msg)
                    if "id" in data:
                        responses[data["id"]] = data

            asyncio.create_task(reader())
            
            req_id = 500
            async def eval_js(expr):
                nonlocal req_id
                req_id += 1
                cid = req_id
                await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": expr, "returnByValue": True}}))
                st = time.time()
                while time.time() - st < 5.0:
                    if cid in responses:
                        return responses.pop(cid).get("result", {}).get("result", {}).get("value")
                    await asyncio.sleep(0.05)
                return "TIMEOUT"

            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            await asyncio.sleep(0.5)

            print("typeof window.spacecraftViewer:", await eval_js("typeof window.spacecraftViewer"))
            print("currentPhase before:", await eval_js("window.spacecraftViewer ? window.spacecraftViewer.currentPhase : 'none'"))
            print("calling setAimViewport(3):", await eval_js("setAimViewport(3); 'done'"))
            print("calling setReentryMode('splashdown'):", await eval_js("setReentryMode('splashdown'); 'done'"))
            print("currentPhase after:", await eval_js("window.spacecraftViewer ? window.spacecraftViewer.currentPhase : 'none'"))
            print("esmGroup.visible:", await eval_js("window.spacecraftViewer.esmGroup.visible"))
            print("recoveryGroup.visible:", await eval_js("window.spacecraftViewer.recoveryGroup.visible"))
            print("vpLaunch display:", await eval_js("document.getElementById('vpLaunchWrapper').style.display"))
            print("vpReentry display:", await eval_js("document.getElementById('vpReentryWrapper').style.display"))

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(main())
