from supabase_client import supabase

def update_room(room_id: str, data: dict):
    supabase.table("rooms").update(data).eq("id", room_id).execute()