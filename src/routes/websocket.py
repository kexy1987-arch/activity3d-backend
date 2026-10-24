from fastapi import WebSocket, WebSocketDisconnect, HTTPException, APIRouter
from models import ConnectionManager
from helpers import get_room_or_404

manager = ConnectionManager()
router = APIRouter(prefix="/ws")

# -------------------------
# WebSocket endpoint
# -------------------------

@router.websocket("/rooms/{room_id}")
async def room_websocket(websocket: WebSocket, room_id: str):
    try:
        get_room_or_404(room_id)
    except HTTPException:
        await websocket.close()
        return

    await manager.connect(room_id, websocket)

    try:
        while True:
            await websocket.receive_text()  # or JSON if you want
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)