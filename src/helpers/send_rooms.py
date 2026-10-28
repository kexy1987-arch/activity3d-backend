from supabase_client import supabase
from fastapi import WebSocket

async def send_rooms(websocket: WebSocket):
    result = supabase.table("rooms").select("*").execute()
    await websocket.send_json(result.data)

