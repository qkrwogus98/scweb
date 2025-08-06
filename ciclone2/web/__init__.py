
try:
    from fastapi import FastAPI
except ImportError:
    raise ModuleNotFoundError("To use the web GUI feature, 'fastapi' is required")

from fastapi import WebSocket
from fastapi.responses import HTMLResponse


app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                const data = JSON.parse(event.data)
                console.log(data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

import ciclone as c

@app.get("/")
async def root():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        msg = await websocket.receive_text()
        if msg != 'test':
            continue

        my = c.Model()

        my.debug = True  # set False for brief trace

        comm = {
            1: c.Queue('LoaderQ', 1),  # length
            2: c.Combi('Load', [1, 3], [1, 4], 4),
            3: c.Queue('TruckQ', 2, start=True),
            4: c.Normal('Haul', 5, 7),
            5: c.Normal('Dump', 6, 5),
            6: c.Count('Production', 7),
            7: c.Normal('Return', 3, 6),
        }

        my.add(comm)
        my.until(Count6=5)

        async def f(data):
            await websocket.send_json(data)

        my.simulate(fn=f)
