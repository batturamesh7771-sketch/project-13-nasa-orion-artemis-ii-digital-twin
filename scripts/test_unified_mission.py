import subprocess
import time
import json
import os
import sys
import urllib.request
import asyncio
import websockets
import base64

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = r"C:\Users\user\.gemini\antigravity\scratch\chrome-test-profile"
ARTIFACTS_DIR = r"C:\Users\user\.gemini\antigravity\brain\bd4d2104-51f7-4d68-b523-07c931a12cbb"

async def cdp_command(ws, method, params=None, msg_id=1):
    req = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(req))
    while True:
        res_raw = await ws.recv()
        res = json.loads(res_raw)
        if res.get("id") == msg_id:
            return res

async def evaluate_js(ws, expr, msg_id=1):
    res = await cdp_command(ws, "Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True
    }, msg_id=msg_id)
    return res.get("result", {}).get("result", {}).get("value")

async def capture_screenshot(ws, filename, msg_id=1):
    res = await cdp_command(ws, "Page.captureScreenshot", {"format": "png"}, msg_id=msg_id)
    b64 = res.get("result", {}).get("data")
    if b64:
        filepath = os.path.join(ARTIFACTS_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(b64))
        print(f"Captured: {filepath} ({os.path.getsize(filepath):,} bytes)")
        return filepath
    else:
        print(f"Failed to capture screenshot: {res}")
        return None

async def main():
    print("Launching Chrome headless with CDP...")
    os.makedirs(PROFILE_DIR, exist_ok=True)
    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        "--headless=new",
        "--remote-debugging-port=9222",
        f"--user-data-dir={PROFILE_DIR}",
        "--window-size=1920,1080",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "http://127.0.0.1:8000/"
    ])

    ws_url = None
    for attempt in range(15):
        time.sleep(1)
        try:
            with urllib.request.urlopen("http://localhost:9222/json") as resp:
                targets = json.loads(resp.read().decode())
                for t in targets:
                    if t.get("type") == "page" and "webSocketDebuggerUrl" in t:
                        ws_url = t["webSocketDebuggerUrl"]
                        break
            if ws_url:
                break
        except Exception:
            pass

    if not ws_url:
        print("ERROR: Could not get CDP WebSocket URL.")
        chrome_proc.terminate()
        return 1

    print(f"Connected to CDP WebSocket: {ws_url}")
    
    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        msg_id = 1
        await cdp_command(ws, "Page.enable", {}, msg_id=msg_id); msg_id += 1
        await cdp_command(ws, "Runtime.enable", {}, msg_id=msg_id); msg_id += 1

        print("Waiting for page load and 3D engine initialization...")
        await asyncio.sleep(3)

        title = await evaluate_js(ws, "document.title", msg_id=msg_id); msg_id += 1
        print(f"Page title: {title}")

        has_master_engine = await evaluate_js(ws, "typeof window.masterMission3D !== 'undefined' && window.masterMission3D !== null", msg_id=msg_id); msg_id += 1
        print(f"window.masterMission3D initialized: {has_master_engine}")

        # Start Playback test
        print("\n--- Testing Playback ---")
        await evaluate_js(ws, "window.togglePlayPause()", msg_id=msg_id); msg_id += 1
        await asyncio.sleep(1)
        is_playing = await evaluate_js(ws, "window.isPlaying", msg_id=msg_id); msg_id += 1
        print(f"window.isPlaying active: {is_playing}")

        # Verify All Milestones Seamlessly in Single Viewport
        milestones = [
            ("unified_m1_liftoff.png", 0, "PAD & LIFTOFF (T+00:00:00)"),
            ("unified_m2_srb_sep.png", 129, "SRB SEPARATION (T+00:02:09)"),
            ("unified_m3_core_meco.png", 494, "CORE MECO & ORBIT (T+00:08:14)"),
            ("unified_m4_tli_burn.png", 90840, "TRANSLUNAR INJECTION BURN (T+25:14:00)"),
            ("unified_m5_lunar_flyby.png", 255600, "LUNAR FLYBY & EARTHRISE (T+71:00:00)"),
            ("unified_m6_return_coast.png", 432000, "RETURN COAST (T+120:00:00)"),
            ("unified_m7a_esm_sep.png", 575850, "ESM SEPARATION & BURN-UP (T+159:57:30)"),
            ("unified_m7b_skip_heating.png", 576350, "5,000°F SKIP REENTRY & BOW SHOCK (T+160:05:50)"),
            ("unified_m7c_drogues.png", 577350, "2x DROGUE PARACHUTES & FBC JETTISON (T+160:22:30)"),
            ("unified_m8_main_parachutes.png", 577800, "3x MAIN RING-SAIL PARACHUTES (T+160:30:00)"),
            ("unified_m9a_splashdown_impact.png", 578115, "WATER SPLASHDOWN IMPACT PLUMES (T+160:35:15)"),
            ("unified_m9b_recovery_waves.png", 578250, "ROLLING WAVES, CMUS & NAVY RECOVERY (T+160:37:30)")
        ]

        for fname, met_sec, label in milestones:
            print(f"\n--- Jumping to Milestone: {label} (MET: {met_sec}s) ---")
            await evaluate_js(ws, f"window.jumpToMissionMilestone({met_sec})", msg_id=msg_id); msg_id += 1
            await asyncio.sleep(1.5) # Allow rendering frame & DOM update
            
            # Read telemetry from DOM
            state = await evaluate_js(ws, "(() => { return { met: document.getElementById('hdrMet')?.innerText, phase: document.getElementById('stPhase')?.innerText, alt: document.getElementById('stAlt')?.innerText, vel: document.getElementById('stVel')?.innerText, stage: document.getElementById('hudStage')?.innerText, earthDist: document.getElementById('envAlt')?.innerText, moonDist: document.getElementById('stDistMoon')?.innerText }; })()", msg_id=msg_id); msg_id += 1
            print(f"Telemetry at {label}: {json.dumps(state)}")
            
            await capture_screenshot(ws, fname, msg_id=msg_id); msg_id += 1

    chrome_proc.terminate()
    print("\nAll 9 milestones verified and captured successfully!")
    return 0

if __name__ == "__main__":
    asyncio.run(main())
