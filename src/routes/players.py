from fastapi import APIRouter
from models import Player, ConnectionManager, GameState
import uuid
from supabase_client import supabase
from helpers import get_room_or_404, update_room, all_ready, run_countdown
import asyncio

router = APIRouter(prefix="/players")
manager = ConnectionManager()

@router.post("/create")
def create_player(player: Player):
    player.id = str(uuid.uuid4())
    supabase.table("players").insert({
        "id": player.id,
        "name": player.name
    }).execute()
    return player

# -------------------------
# Player ready
# -------------------------

@router.post("/{room_id}/players/{player_id}/ready")
async def set_player_ready(room_id: str, player_id: str, value: bool):
    room = get_room_or_404(room_id)

    room_state = GameState(room["state"])

    ready_players = room.get("ready_players", {})
    ready_players[player_id] = value

    update_room(room_id, {"ready_players": ready_players})

    await manager.broadcast(room_id, {
        "event": "player_ready",
        "player_id": player_id,
        "value": value,
        "ready_players": ready_players
    })

    if value is False:
        update_room(room_id, {"state": GameState.LOBBY.value})

        await manager.broadcast(room_id, {"event": "countdown_stopped"})

        return {
            "message": f"Player {player_id} is now not ready",
            "state": GameState.Lobby.value,
            "ready_players": ready_players
        }

    if all_ready(room):
        update_room(room_id, {"state": GameState.COUNTDOWN.value})
        asyncio.create_task(run_countdown(room_id))

        await manager.broadcast(room_id, {
            "event": "countdown_started"
        })

        return {
            "message": "Countdown started",
            "state": GameState.COUNTDOWN.value,
            "ready-players": ready_players
        }

    return {
        "message": f"Player {player_id} is now {'ready' if value else 'not ready'}",
        "ready_players": ready_players,
        "state": room_state.value
    }