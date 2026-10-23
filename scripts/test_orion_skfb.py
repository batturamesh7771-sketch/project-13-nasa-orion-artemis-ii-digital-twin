import subprocess
import time
import json
import urllib.request
import asyncio
import websockets

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = r"C:\Users\user\.gemini\antigravity\scratch\chrome-test-profile"

html_content = """<!DOCTYPE html>
<html>
<head>
  <script src="https://static.sketchfab.com/api/sketchfab-viewer-1.12.1.js"></script>
</head>
<body>
  <iframe id="api-frame" style="width:800px; height:600px;" src="https://sketchfab.com/models/9279b0672f15454b9320a31fceb65508/embed"></iframe>
  <script>
    window.sketchfabNodes = null;
    window.sketchfabReady = false;
    const iframe = document.getElementById('api-frame');
    const client = new Sketchfab('1.12.1', iframe);
    client.init('9279b0672f15454b9320a31fceb65508', {
      success: function(api) {
        window.api = api;
        api.start();
        api.addEventListener('viewerready', function() {
          window.sketchfabReady = true;
          api.getNodeMap(function(err, nodes) {
            window.sketchfabNodes = nodes;
          });
        });
      },
      error: function() {
        window.sketchfabError = true;
      }
    });
  </script>
</body>
</html>
"""

async def run_test():
    with open("web/static/test_orion_skfb.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("Launching Chrome to inspect Orion Sketchfab API...")
    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        "--headless=new",
        "--remote-debugging-port=9222",
        f"--user-data-dir={PROFILE_DIR}",
        "http://127.0.0.1:8000/static/test_orion_skfb.html"
    ])

    await asyncio.sleep(2)
    try:
        with urllib.request.urlopen("http://localhost:9222/json") as r:
            targets = json.loads(r.read().decode())
        ws_url = [t['webSocketDebuggerUrl'] for t in targets if t.get('type') == 'page'][0]
        
        async with websockets.connect(ws_url) as ws:
            for attempt in range(20):
                await asyncio.sleep(1)
                await ws.send(json.dumps({
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": "(() => { return { ready: window.sketchfabReady, hasNodes: !!window.sketchfabNodes, count: window.sketchfabNodes ? Object.keys(window.sketchfabNodes).length : 0 }; })()",
                        "returnByValue": True
                    }
                }))
                res = json.loads(await ws.recv())
                val = res.get("result", {}).get("result", {}).get("value")
                print(f"Attempt {attempt+1}: {val}")
                if val and val.get("ready") and val.get("hasNodes"):
                    await ws.send(json.dumps({
                        "id": 2,
                        "method": "Runtime.evaluate",
                        "params": {
                            "expression": "(() => { const names = {}; Object.values(window.sketchfabNodes).forEach(n => { if (n.name) names[n.instanceID] = { name: n.name, type: n.type }; }); return names; })()",
                            "returnByValue": True
                        }
                    }))
                    res2 = json.loads(await ws.recv())
                    print("Orion Nodes:", json.dumps(res2.get("result", {}).get("result", {}).get("value"), indent=2))
                    break
    finally:
        chrome_proc.terminate()

if __name__ == "__main__":
    asyncio.run(run_test())
