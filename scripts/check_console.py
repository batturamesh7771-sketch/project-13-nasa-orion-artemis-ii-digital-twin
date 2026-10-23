import subprocess
import time
import json
import os
import urllib.request
import asyncio
import websockets

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = r"C:\Users\user\.gemini\antigravity\scratch\chrome-test-profile"

async def check():
    os.makedirs(PROFILE_DIR, exist_ok=True)
    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        "--headless=new",
        "--remote-debugging-port=9222",
        f"--user-data-dir={PROFILE_DIR}",
        "--window-size=1920,1080",
        "http://127.0.0.1:8000/"
    ])
    await asyncio.sleep(2)

    try:
        with urllib.request.urlopen("http://localhost:9222/json") as r:
            targets = json.loads(r.read().decode())
        ws_url = [t['webSocketDebuggerUrl'] for t in targets if t.get('type') == 'page'][0]
        print(f"Connecting to {ws_url}")
        
        async with websockets.connect(ws_url) as ws:
            # Enable Log and Runtime
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            await ws.send(json.dumps({"id": 2, "method": "Log.enable"}))
            await asyncio.sleep(1)

            # Check globals
            expr = """
            (() => {
                return {
                    hasThree: typeof THREE !== 'undefined',
                    hasOrbitControls: typeof THREE !== 'undefined' && typeof THREE.OrbitControls !== 'undefined',
                    hasArtemisMasterClass: typeof ArtemisMasterMission3D !== 'undefined',
                    hasMasterInstance: typeof window.masterMission3D !== 'undefined' && window.masterMission3D !== null,
                    hasTogglePlayPause: typeof window.togglePlayPause !== 'undefined',
                    hasJumpToMissionMilestone: typeof window.jumpToMissionMilestone !== 'undefined'
                };
            })()
            """
            await ws.send(json.dumps({
                "id": 3,
                "method": "Runtime.evaluate",
                "params": {"expression": expr, "returnByValue": True}
            }))
            res = await ws.recv()
            while True:
                msg = json.loads(res)
                if msg.get("id") == 3:
                    print("Global status:", msg.get("result", {}).get("result", {}).get("value"))
                    break
                res = await ws.recv()

            # Now test instantiating ArtemisMasterMission3D if not already
            test_inst = """
            (() => {
                try {
                    const inst = new ArtemisMasterMission3D('mainMissionCanvas');
                    return 'Success: ' + (inst ? 'instantiated' : 'null');
                } catch(e) {
                    return 'Error: ' + e.toString() + '\\n' + e.stack;
                }
            })()
            """
            await ws.send(json.dumps({
                "id": 4,
                "method": "Runtime.evaluate",
                "params": {"expression": test_inst, "returnByValue": True}
            }))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == 4:
                    print("Instantiation result:", msg.get("result", {}).get("result", {}).get("value"))
                    break

    finally:
        chrome_proc.terminate()

if __name__ == "__main__":
    asyncio.run(check())
