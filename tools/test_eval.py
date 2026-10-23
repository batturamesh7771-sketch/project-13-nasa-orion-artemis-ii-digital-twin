import urllib.request, json, asyncio, websockets

async def check():
    resp = urllib.request.urlopen('http://localhost:9235/json')
    targets = json.loads(resp.read().decode())
    ws_url = [t['webSocketDebuggerUrl'] for t in targets if t.get('type') == 'page'][0]
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': 'setReentryMode("peak_heating")', 'returnByValue': True}}))
        msg = await ws.recv()
        print('RES:', msg)

asyncio.run(check())
