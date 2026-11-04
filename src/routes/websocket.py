from fastapi import WebSocket, WebSocketDisconnect, HTTPException, APIRouter
from helpers import get_room_or_404, send_room_list, room_manager, connection_manager
from supabase_client import supabase


manager = connection_manager
router = APIRouter(prefix="/ws")

# -------------------------
# Room WebSocket endpoint
# -------------------------

@router.websocket("/rooms/{room_id}")
async def room_websocket(websocket: WebSocket, room_id: str):
    player_id = websocket.query_params.get("player_id")
    await manager.connect(room_id, websocket, player_id)
    room = get_room_or_404(room_id)

    await manager.broadcast(room_id, {
        "event": "New Connection",
        "room": room,
        })

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(room_id, websocket)

# -------------------------
# Room List WebSocket endpoint
# -------------------------

@router.websocket("/rooms")
async def rooms_ws(websocket: WebSocket):

    await room_manager.connect(websocket)

    await send_room_list(websocket);

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        room_manager.disconnect(websocket)

