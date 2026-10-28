from fastapi import APIRouter, HTTPException
from models import Player, ConnectionManager, GameState, PlayerCreate, LoginReq
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
# Get player
# -------------------------

@router.get("/{player_id}")
def get_player(player_id: str):
    player_req = supabase.table("players").select("*").eq("id", player_id).execute()

    if not player_req.data:
        raise HTTPException(status_code=404, detail="Player not found")

    player = player_req.data[0]

    return player

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
        "last_seen": player.last_seen.isoformat()
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
        "last_seen": player.last_seen.isoformat()
    }).execute()

    supabase.table("accounts").insert({
        "id": player.auth_id,
        "email": account.email,
        "password_hash": hash_password(account.password)
    }).execute()
    
    return player

# -------------------------
# Player login
# -------------------------

@router.post("/login")
async def login_player(login_req: LoginReq):
    # 1. Find account by email
    resp = supabase.table("accounts").select("*").eq("email", login_req.email).execute()

    if not resp.data:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = resp.data[0]

    # 2. Verify password
    if not bcrypt.checkpw(login_req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid password")

    # 3. Find linked player
    player_resp = supabase.table("players").select("*").eq("auth_id", user["id"]).execute()

    if not player_resp.data:
        raise HTTPException(status_code=404, detail="Player not found")

    player = player_resp.data[0]

    # 4. Update first_login
    if not player["first_login"]:
        supabase.table("players").update({"first_login": True, "last_seen": datetime.now(UTC).isoformat()}).eq("auth_id", user["id"]).execute()
        player["first_login"] = True
    else:
        supabase.table("players").update({"first_login": False, "last_seen": datetime.now(UTC).isoformat()}).eq("auth_id", user["id"]).execute()
        player["first_login"] = False

    return {"player_id": player["id"]}




# -------------------------
# Player ready
# -------------------------

@router.post("/{room_id}/{player_id}/ready")
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