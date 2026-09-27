import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from app.session.manager import session_manager

router = APIRouter(tags=["WebSocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send current session state immediately upon connection
        sess = session_manager.get_active_session()
        if sess:
            await websocket.send_text(json.dumps({
                "type": "SESSION_UPDATE",
                "data": sess.model_dump()
            }))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        text = json.dumps(message)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(text)
            except Exception:
                dead_connections.append(connection)
        for dc in dead_connections:
            self.disconnect(dc)

ws_manager = ConnectionManager()

# Hook session manager listener to broadcast
async def on_session_change(data: dict):
    await ws_manager.broadcast({
        "type": "SESSION_UPDATE",
        "data": data
    })

session_manager.add_listener(on_session_change)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming ping / messages if any
            try:
                msg = json.loads(data)
                if msg.get("action") == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
