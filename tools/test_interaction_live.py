import subprocess
import time
import urllib.request
import json
import base64
import asyncio
import websockets
from pathlib import Path

ARTIFACT_DIR = Path(r"C:\Users\user\.gemini\antigravity\brain\bd4d2104-51f7-4d68-b523-07c931a12cbb")
SCREENSHOT_DATA_PATH = ARTIFACT_DIR / "browser_after_gmat_benchmark.png"
SCREENSHOT_RETURN_PATH = ARTIFACT_DIR / "browser_after_return_to_mission.png"

class ChromeCDP:
    def __init__(self, ws):
        self.ws = ws
        self.msg_id = 0
        self.pending = {}
        self.events = []
        self._listener_task = asyncio.create_task(self._listen())

    async def _listen(self):
        try:
            while True:
                msg = await self.ws.recv()
                data = json.loads(msg)
                if "id" in data:
                    req_id = data["id"]
                    if req_id in self.pending:
                        self.pending[req_id].set_result(data)
                else:
                    self.events.append(data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            # WebSocket closed
            pass

    async def call(self, method, params=None, timeout=20.0):
        self.msg_id += 1
        cid = self.msg_id
        fut = asyncio.get_event_loop().create_future()
        self.pending[cid] = fut
        req = {"id": cid, "method": method}
        if params:
            req["params"] = params
        await self.ws.send(json.dumps(req))
        try:
            res = await asyncio.wait_for(fut, timeout=timeout)
            return res
        finally:
            self.pending.pop(cid, None)

    async def eval_js(self, expression, timeout=15.0):
        res = await self.call("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        }, timeout=timeout)
        val = res.get("result", {}).get("result", {}).get("value")
        return val

    def close(self):
        self._listener_task.cancel()

async def run_test():
    user_data = Path(r"C:\Users\user\AppData\Local\Temp\chrome_cdp_profile_test2")
    cmd = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--remote-debugging-port=9224",
        f"--user-data-dir={user_data}",
        "--disable-gpu",
        "--window-size=1440,900",
        "http://127.0.0.1:8000/"
    ]
    proc = subprocess.Popen(cmd)
    try:
        await asyncio.sleep(2.5)
        resp = urllib.request.urlopen("http://localhost:9224/json")
        targets = json.loads(resp.read().decode())
        page_target = next((t for t in targets if t.get("type") == "page" and "127.0.0.1:8000" in t.get("url", "")), None)
        if not page_target:
            print("ERROR: Target page not found")
            return

        ws_url = page_target["webSocketDebuggerUrl"]
        print(f"Connected to CDP: {ws_url}")

        async with websockets.connect(ws_url) as raw_ws:
            cdp = ChromeCDP(raw_ws)
            await cdp.call("Page.enable")
            await cdp.call("Runtime.enable")
            await cdp.call("Emulation.setDeviceMetricsOverride", {
                "width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False
            })

            # Check initial state
            nav_tabs = await cdp.eval_js("""
                Array.from(document.querySelectorAll('.nav-tab')).map(b => ({
                    tab: b.getAttribute('data-tab'),
                    text: b.textContent.trim(),
                    rect: b.getBoundingClientRect()
                }))
            """)
            print("\n=== Initial Nav Tabs Layout ===")
            print(json.dumps(nav_tabs, indent=2))

            # Step 1: Click DATA & VALIDATION tab
            print("\n[Step 1] Clicking DATA & VALIDATION tab...")
            data_tab_res = await cdp.eval_js("""
                (() => {
                    const btn = document.querySelector('.nav-tab[data-tab="data"]');
                    if (btn) btn.click();
                    return {
                        clicked: !!btn,
                        missionViewDisplay: window.getComputedStyle(document.getElementById('missionView')).display,
                        dataViewDisplay: window.getComputedStyle(document.getElementById('dataValidationView')).display
                    };
                })()
            """)
            print("After clicking DATA tab:", data_tab_res)

            # Step 2: Click EXECUTE LIVE GMAT BENCHMARK
            print("\n[Step 2] Clicking #btnRunGmatLive button...")
            gmat_click_res = await cdp.eval_js("""
                (() => {
                    const btn = document.getElementById('btnRunGmatLive');
                    if (btn) btn.click();
                    return {
                        clicked: !!btn,
                        btnDisabled: btn.disabled,
                        btnText: btn.textContent.trim(),
                        outDisplay: window.getComputedStyle(document.getElementById('gmatLiveOutput')).display
                    };
                })()
            """)
            print("After clicking GMAT button:", gmat_click_res)

            # Step 3: Poll until GMAT benchmark finishes
            print("\n[Step 3] Waiting for GMAT live execution to complete...")
            for i in range(20):
                await asyncio.sleep(1.0)
                status = await cdp.eval_js("""
                    (() => {
                        const btn = document.getElementById('btnRunGmatLive');
                        const out = document.getElementById('gmatLiveOutput');
                        return {
                            btnDisabled: btn.disabled,
                            btnText: btn.textContent.trim(),
                            outLen: out.textContent.length,
                            preview: out.textContent.substring(0, 180)
                        };
                    })()
                """)
                print(f"   [+{i+1}s] Disabled: {status.get('btnDisabled')}, Output length: {status.get('outLen')} chars")
                if not status.get("btnDisabled") and status.get("outLen", 0) > 300:
                    print("\n[+] GMAT Live Benchmark Finished! Output Preview:")
                    print(status.get("preview"))
                    break

            # Capture Screenshot of Data View with live GMAT output
            shot_res = await cdp.call("Page.captureScreenshot", {"format": "png"})
            png_b64 = shot_res.get("result", {}).get("data", "")
            if png_b64:
                with open(SCREENSHOT_DATA_PATH, "wb") as f:
                    f.write(base64.b64decode(png_b64))
                print(f"[+] Successfully saved DATA view screenshot to: {SCREENSHOT_DATA_PATH}")

            # Step 4: Click MISSION tab to return to 3D Flight Control
            print("\n[Step 4] Clicking MISSION tab to return to 3D flight control...")
            mission_tab_res = await cdp.eval_js("""
                (() => {
                    const btn = document.querySelector('.nav-tab[data-tab="mission"]');
                    if (btn) btn.click();
                    return {
                        clicked: !!btn,
                        missionViewDisplay: window.getComputedStyle(document.getElementById('missionView')).display,
                        dataViewDisplay: window.getComputedStyle(document.getElementById('dataValidationView')).display
                    };
                })()
            """)
            print("After clicking MISSION tab:", mission_tab_res)

            await asyncio.sleep(1.0)

            # Capture Screenshot of Mission View after returning
            shot_res2 = await cdp.call("Page.captureScreenshot", {"format": "png"})
            png_b64_2 = shot_res2.get("result", {}).get("data", "")
            if png_b64_2:
                with open(SCREENSHOT_RETURN_PATH, "wb") as f:
                    f.write(base64.b64decode(png_b64_2))
                print(f"[+] Successfully saved MISSION return screenshot to: {SCREENSHOT_RETURN_PATH}")

            cdp.close()

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(run_test())
