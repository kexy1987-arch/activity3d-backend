from supabase_client import supabase
from fastapi import HTTPException

def get_room_or_404(room_id: str) -> dict:
    result = supabase.table("rooms").select("*").eq("id", room_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Room not found")
    return result.data[0]