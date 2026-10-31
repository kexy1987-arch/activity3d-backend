from fastapi import WebSocket, WebSocketDisconnect, HTTPException, APIRouter
from helpers import get_room_or_404, send_room_list, room_manager, connection_manager
from supabase_client import supabase


manager = connection_manager
router = APIRouter(prefix="/ws")

# -------------------------
# WebSocket endpoint
# -------------------------

@router.websocket("/rooms/{room_id}")
async def room_websocket(websocket: WebSocket, room_id: str):
    await manager.connect(room_id, websocket)
    room = get_room_or_404(room_id)

    await manager.broadcast(room_id, {
        "event": "New Connection",
        "room": room
        })

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)

@router.websocket("/rooms")
async def rooms_ws(websocket: WebSocket):

    await room_manager.connect(websocket)

    await send_room_list(websocket);

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        room_manager.disconnect(websocket)

