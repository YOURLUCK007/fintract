"""WebSocket endpoint for real-time notifications."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from ..config import settings
from ..realtime import manager

router = APIRouter(tags=["realtime"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    """Authenticated WebSocket. Client connects to /ws?token=<JWT>."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        await websocket.close(code=1008)
        return

    await manager.connect(user_id, websocket)
    try:
        await websocket.send_json({"type": "connected", "user_id": user_id})
        while True:
            # Keep the connection alive; ignore inbound content (heartbeats).
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(user_id, websocket)
