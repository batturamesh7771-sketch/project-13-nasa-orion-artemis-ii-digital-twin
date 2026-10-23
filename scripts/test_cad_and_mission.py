import subprocess
import time
import json
import urllib.request
import asyncio
import websockets
import os
import base64

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = r"C:\Users\user\.gemini\antigravity\scratch\chrome-test-profile"
ARTIFACTS_DIR = r"C:\Users\user\.gemini\antigravity\brain\bd4d2104-51f7-4d68-b523-07c931a12cbb"

async def test_cad_and_mission():
    print("Launching Chrome headless for CAD explosion and mission verification...")
    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        "--headless=new",
        "--remote-debugging-port=9222",
        f"--user-data-dir={PROFILE_DIR}",
        "--window-size=1600,1000",
        "http://127.0.0.1:8000"
    ])

    await asyncio.sleep(3)
    try:
        with urllib.request.urlopen("http://localhost:9222/json") as r:
            targets = json.loads(r.read().decode())
        ws_url = [t['webSocketDebuggerUrl'] for t in targets if t.get('type') == 'page'][0]

        async with websockets.connect(ws_url, max_size=20000000) as ws:
            async def eval_js(expr):
                await ws.send(json.dumps({
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {"expression": expr, "returnByValue": True}
                }))
                res = json.loads(await ws.recv())
                return res.get("result", {}).get("result", {}).get("value")

            async def capture_screen(filename):
                await ws.send(json.dumps({
                    "id": 2,
                    "method": "Page.captureScreenshot",
                    "params": {"format": "png"}
                }))
                res = json.loads(await ws.recv())
                img_data = res["result"]["data"]
                filepath = os.path.join(ARTIFACTS_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(img_data))
                print(f"Captured {filename} -> {filepath}")

            await asyncio.sleep(2)

            # 1. TEST CAD VIEW: MOBILE LAUNCHER & LC-39B WITH EXPLODED VIEW
            print("1. Testing 3D CAD: Launch Pad with Exploded View...")
            await eval_js("switchTab('cad')")
            await asyncio.sleep(1)
            await eval_js("switchCadModel('launch_pad')")
            await asyncio.sleep(1)
            await eval_js("setCadExplodeSlider(65)")
            await asyncio.sleep(1)

            # Check explosion values on pad assembly
            pad_exp_state = await eval_js("""(() => {
                const viewer = window.cadViewer;
                if (!viewer) return { error: 'No cadViewer' };
                const asm = viewer.padSlsAssembly;
                return {
                    activeModel: viewer.activeModel,
                    isExploded: viewer.isExploded,
                    frac: viewer.explodedFrac,
                    srbLeftX: asm ? asm.srbLeft.position.x : null,
                    srbRightX: asm ? asm.srbRight.position.x : null,
                    lasY: asm ? asm.las.position.y : null,
                    enginesY: asm ? asm.engines.position.y : null,
                    icpsY: asm ? asm.icps.position.y : null,
                    armCount: viewer.padArms ? viewer.padArms.length : 0,
                    arm0RotY: viewer.padArms && viewer.padArms[0] ? viewer.padArms[0].rotation.y : null
                };
            })()""")
            print("Pad Exploded State:", json.dumps(pad_exp_state, indent=2))
            await capture_screen("cad_pad_exploded_65pct.png")

            # 2. TEST CAD VIEW: SLS BLOCK 1 WITH 80% EXPLOSION
            print("2. Testing 3D CAD: SLS Block 1 Exploded...")
            await eval_js("switchCadModel('sls')")
            await asyncio.sleep(1)
            await eval_js("setCadExplodeSlider(80)")
            await asyncio.sleep(1)
            sls_exp_state = await eval_js("""(() => {
                const viewer = window.cadViewer;
                const asm = viewer.slsAssembly;
                return {
                    activeModel: viewer.activeModel,
                    srbLeftX: asm ? asm.srbLeft.position.x : null,
                    srbRightX: asm ? asm.srbRight.position.x : null,
                    lasY: asm ? asm.las.position.y : null,
                    icpsY: asm ? asm.icps.position.y : null
                };
            })()""")
            print("SLS Exploded State:", json.dumps(sls_exp_state, indent=2))
            await capture_screen("cad_sls_exploded_80pct.png")

            # 3. TEST CAD VIEW: ORION MPCV WITH 70% EXPLOSION
            print("3. Testing 3D CAD: Orion MPCV Exploded...")
            await eval_js("switchCadModel('orion')")
            await asyncio.sleep(1)
            await eval_js("setCadExplodeSlider(70)")
            await asyncio.sleep(1)
            await capture_screen("cad_orion_exploded_70pct.png")

            # 4. TEST MISSION VIEW: AIM 2 TLI BURN WITH ENERGETIC OMS EXHAUST PLUME
            print("4. Testing Mission: AIM 2 TLI Burn with OMS Flame Plume...")
            await eval_js("switchTab('mission')")
            await asyncio.sleep(1)
            await eval_js("jumpToMissionMilestone(90840)")
            await asyncio.sleep(2)
            aim2_state = await eval_js("""(() => {
                const m = window.masterMission3D;
                return {
                    met: m.currentMet,
                    flameOpacity: m.insituCoreFlameMat ? m.insituCoreFlameMat.opacity : null,
                    mantleOpacity: m.insituMantleFlameMat ? m.insituMantleFlameMat.opacity : null,
                    sparkOpacity: m.insituSparkMat ? m.insituSparkMat.opacity : null,
                    pos: m.insituOrionGroup.position
                };
            })()""")
            print("AIM 2 TLI Burn State:", json.dumps(aim2_state, indent=2))
            await capture_screen("aim2_tli_burn_plume.png")

            # 5. TEST MISSION VIEW: AIM 3 3x MAIN PARACHUTES
            print("5. Testing Mission: AIM 3 3x Main Parachutes...")
            await eval_js("jumpToMissionMilestone(577500)")
            await asyncio.sleep(2)
            await capture_screen("aim3_main_parachutes.png")

            # 6. TEST MISSION VIEW: AIM 3 SPLASHDOWN & BUOYANT WAVES
            print("6. Testing Mission: AIM 3 Splashdown & Waves...")
            await eval_js("jumpToMissionMilestone(578160)")
            await asyncio.sleep(2)
            await capture_screen("aim3_splashdown_waves.png")

    finally:
        chrome_proc.terminate()
        print("Chrome process terminated.")

if __name__ == "__main__":
    asyncio.run(test_cad_and_mission())
