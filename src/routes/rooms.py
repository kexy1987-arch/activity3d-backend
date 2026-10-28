from fastapi import APIRouter
from models import GameState, ConnectionManager, RoomListConnectionManager
import uuid
from supabase_client import supabase
from models.requests import RoomCreateRequest
import uuid
from dotenv import load_dotenv
load_dotenv()
from helpers import get_room_or_404, update_room, all_ready, room_manager

router = APIRouter(prefix="/rooms")
manager = ConnectionManager()

@router.get("")
def list_rooms():
    results = supabase.table("rooms").select("*").execute()
    return results.data


@router.post("/create")
async def create_room(data: RoomCreateRequest):
    room_id = str(uuid.uuid4())
    room = {
        "id": room_id,
        "name": data.name,
        "creator_id": data.creator.id,
        "state": GameState.LOBBY.value,
        "teams": [],
        "lobby": [],
        "ready_players": {},
        "countdown_seconds": 5
    }

    supabase.table("rooms").insert(room).execute()

    rooms = supabase.table("rooms").select("*").execute().data
    await room_manager.broadcast(rooms)
    

    return {
        "message": "Room created",
        "room": room
    }


@router.get("/{room_id}")
def get_room(room_id: str):
    room = get_room_or_404(room_id)
    room["state"] = GameState(room["state"])
    return room

# -------------------------
# Delete room
# -------------------------


@router.delete("/{room_id}")
async def delete_room(room_id: str):

    room = get_room_or_404(room_id)

    supabase.table("rooms").delete().eq("id", room_id).execute()    

    rooms = supabase.table("rooms").select("*").execute().data
    await room_manager.broadcast(rooms)

    return {
        "message": f"Room {room_id} deleted",
        "room_id" : room_id
    }





# -------------------------
# Clean up
# -------------------------

@router.post("/{room_id}/cleanup")
async def cleanup_room(room_id: str):
    room = get_room_or_404(room_id)

    lobby = room.get("lobby", [])
    teams = room.get("teams", [])
    ready_players = room.get("ready_players", {})

    removed_players = []
    removed_teams = []

    valid_players = {
        p["id"]
        for p in supabase.table("players").select("id").execute().data
    }

    new_lobby = []
    for p in lobby:
        if p["id"] not in valid_players:
            removed_players.append(p)
        else:
            new_lobby.append(p)
    lobby = new_lobby

    new_teams = []
    for team in teams:
        team_players = team.get("players", [])
        filtered_players = [tp for tp in team_players if tp["id"] in valid_players]

        if len(filtered_players) == 0:
            removed_teams.append(team)
            continue

        team["players"] = filtered_players
        new_teams.append(team)

    teams == new_teams

    for pid in list(ready_players.keys()):
        if pid not in valid_players:
            ready_players.pop(pid)
        else:
            ready_players[pid] = False

    for t in teams:
        t["ready"] = False

    if len(lobby) == 0 and len(teams) == 0:
        await manager.broadcast(room_id, {
            "event": "room_deleted",
            "reason": "empty_after_cleanup"
        })

        for ws in manager.rooms.get(room_id, []):
            try:
                await ws.close()
            except:
                pass

        manager.rooms.pop(room_id, None)

        supabase.table("rooms").delete().eq("id", room_id).execute()

        return {
            "message": "Room deleted because it became empty.",
            "room_id": room_id
        }

    update_room(room_id, {
        "lobby": lobby,
        "teams": teams,
        "ready_players": ready_players,
        "state": GameState.LOBBY.value,
    })

    await manager.broadcast(room_id, {
        "event": "room_cleaned",
        "removed_players": removed_players,
        "removed_teams": removed_teams,
        "room": {
            "id": room["id"],
            "name": room["name"],
            "lobby": lobby,
            "teams": teams,
            "state": GameState.LOBBY.value
        }
    })

    return {
        "message": "Room cleaned",
        "removed_players": removed_players,
        "removed_teams": removed_teams,
        "room": {
            "id": room["id"],
            "name": room["name"],
            "lobby": lobby,
            "teams": teams,
            "state": GameState.LOBBY.value
        }
    }

# -------------------------
# Start game
# -------------------------

@router.post("/{room_id}/start")
async def start_game(room_id: str):
    room = get_room_or_404(room_id)

    room_state = GameState(room["state"])

    if room_state not in [GameState.LOBBY, GameState.COUNTDOWN]:
        return {
            "error": "Game cannot be started from the current state",
            "state": room_state.value
        }

    if not all_ready(room):
        return {
            "error": "Not all teams/players are ready",
            "state": room_state.value
        }
    
    update_room(room_id, {"state": GameState.PLAYING.value})

    await manager.broadcast(room_id, {
        "event": "game_start",
        "room": {**room, "state": GameState.PLAYING}
    })

    return {"message": "Game started", "room": {**room, "state": GameState.PLAYING}}