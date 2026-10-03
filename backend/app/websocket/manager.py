import json
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active: dict[int, list[WebSocket]] = {}  # user_id -> sockets
        self.by_role: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, role: str):
        await websocket.accept()
        self.active.setdefault(user_id, []).append(websocket)
        self.by_role.setdefault(role, []).append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int, role: str):
        if user_id in self.active and websocket in self.active[user_id]:
            self.active[user_id].remove(websocket)
        if role in self.by_role and websocket in self.by_role[role]:
            self.by_role[role].remove(websocket)

    async def send_to_user(self, user_id: int, event: str, payload: dict):
        for ws in self.active.get(user_id, []):
            await ws.send_text(json.dumps({"event": event, "data": payload}))

    async def broadcast_to_role(self, role: str, event: str, payload: dict):
        for ws in self.by_role.get(role, []):
            await ws.send_text(json.dumps({"event": event, "data": payload}))

    async def broadcast_all(self, event: str, payload: dict):
        message = json.dumps({"event": event, "data": payload})
        for sockets in self.active.values():
            for ws in sockets:
                await ws.send_text(message)


manager = ConnectionManager()
