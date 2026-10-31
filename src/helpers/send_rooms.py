from supabase_client import supabase
from fastapi import WebSocket
from .managers import room_manager, connection_manager


async def send_room_list(websocket: WebSocket):
    result = supabase.table("rooms").select("*").execute()
    await websocket.send_json(result.data)

async def send_rooms():
    rooms = supabase.table("rooms").select("*").execute().data
    await room_manager.broadcast(rooms)

async def update_room(room_id):
    room = supabase.table("rooms").select("*").eq("id", room_id).single().execute().data;
    await connection_manager.broadcast(room_id, {
        "message": "Room updated",
        "room": room
    })
    
