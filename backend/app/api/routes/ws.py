from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4401)
        return
    db = SessionLocal()
    try:
        user = db.query(User).get(int(payload.get("sub")))
        if user is None:
            await websocket.close(code=4401)
            return
        role = user.role.name.value
        await manager.connect(websocket, user.id, role)
        try:
            while True:
                await websocket.receive_text()  # keep-alive / ignore inbound
        except WebSocketDisconnect:
            manager.disconnect(websocket, user.id, role)
    finally:
        db.close()
