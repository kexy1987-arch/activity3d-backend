from fastapi import APIRouter
from models import Player, ConnectionManager, GameState, PlayerCreate
import uuid
from supabase_client import supabase
from helpers import get_room_or_404, update_room, all_ready, run_countdown
import asyncio
from datetime import datetime, UTC
import bcrypt # type: ignore

router = APIRouter(prefix="/players")
manager = ConnectionManager()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# -------------------------
# Create player
# -------------------------

@router.post("/create-guest")
def create_guest(player: Player):
    player.id = str(uuid.uuid4())
    player.last_seen = datetime.now(UTC)
    player.auth_id = str(uuid.uuid4())

    supabase.table("players").insert({
        "id": player.id,
        "name": player.name,
        "is_guest": True,
        "auth_id": player.auth_id,
        "room_id": player.room_id,
        "last_seen": player.last_seen
    }).execute()
    
    return player

@router.post("/create-player")
def create_player(data: PlayerCreate):
    player = data.player
    account = data.account

    player.id = str(uuid.uuid4())
    player.last_seen = datetime.now(UTC)
    player.auth_id = str(uuid.uuid4())

    supabase.table("players").insert({
        "id": player.id,
        "name": player.name,
        "is_guest": False,
        "auth_id": player.auth_id,
        "room_id": player.room_id,
        "last_seen": player.last_seen
    }).execute()

    supabase.table("accounts").insert({
        "id": player.auth_id,
        "email": account.email,
        "password_hash": hash_password(account.password)
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