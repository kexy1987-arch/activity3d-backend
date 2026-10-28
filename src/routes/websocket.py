from fastapi import WebSocket, WebSocketDisconnect, HTTPException, APIRouter
from models import ConnectionManager
from helpers import get_room_or_404, send_rooms, room_manager
from supabase_client import supabase


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

@router.websocket("/rooms")
async def rooms_ws(websocket: WebSocket):

    await room_manager.connect(websocket)

    await send_rooms(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        room_manager.disconnect(websocket)

