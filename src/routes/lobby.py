from fastapi import APIRouter
from models import Player, GameState, ConnectionManager
from dotenv import load_dotenv
load_dotenv()
from helpers import get_room_or_404, update_room

router = APIRouter(prefix="/lobby")
manager = ConnectionManager()

# -------------------------
# Lobby join
# -------------------------

@router.post("/{room_id}/join")
async def join_lobby(room_id: str, player: Player):
    room = get_room_or_404(room_id)

    room_state = GameState(room["state"])
    
    lobby = room.get("lobby", [])
    teams = room.get("teams")
    ready_players = room.get("ready_players", {})

    if any(p["id"] == player.id for p in lobby):
        return {"message": f"{player.name} is already in the lobby"}

    if any (player.id in [tp["id"] for tp in t.get("players", [])] for t in teams):
        return {"message": f"{player.name} is already in the team"}

    lobby.append(player.model_dump())

    ready_players[player.id] = False

    for t in teams:
        t["ready"] = False


    update_room(room_id, {
        "lobby": lobby,
        "teams": teams,
        "ready_players": ready_players,
        "state": GameState.LOBBY.value
        })

    await manager.broadcast(room_id, {
        "event": "player_joined_lobby",
        "player": player.model_dump(),
        "room": {
            "id": room["id"],
            "name": room["name"],
            "lobby": lobby,
            "teams": teams,
            "state": GameState.LOBBY.value
        }
    })

    return {
        "message": f"{player.name} joined the lobby",
        "room":
        {"id": room["id"],
            "name": room["name"],
            "lobby": lobby,
            "teams": teams,
            "state": GameState.LOBBY.value}
        }

# -------------------------
# Player leave room
# -------------------------


@router.post("/{room_id}/leave")
async def leave_room(room_id: str, player: Player):
    room = get_room_or_404(room_id)

    lobby = room.get("lobby", [])
    teams = room.get("teams", [])
    ready_players = room.get("ready_players", {})

    player_id = player.id

    lobby = [p for p in lobby if p["id"] != player_id]

    for team in teams:
        team_players = team.get("players", [])
        new_players = [tp for tp in team_players if tp["id"] != player_id]

        if len(new_players) != len(team_players):
            removed_from_team = team["id"]
            team["players"] = new_players

    teams = [t for t in teams if len(t.get("players", [])) > 0]

    ready_players[player_id] = False

    update_room(room_id, {
        "lobby": lobby,
        "teams": teams,
        "state": GameState.LOBBY.value,
        "ready_players": ready_players
    })

    await manager.broadcast(room_id, {
        "event": "counter_stopped"
    })

    await manager.broadcast(room_id, {
        "event": "player_left",
        "player": player.model_dump(),
        "removed_from_team": removed_from_team,
        "room": {
            "id": room["id"],
            "name": room["name"],
            "lobby": lobby,
            "teams": teams,
            "state": GameState.LOBBY.value,
        }
    })

    return {
        "message": f"{player.name} left the room",
        "removed_from_team": removed_from_team,
        "room": {
            "id": room["id"],
            "name": room["name"],
            "lobby": lobby,
            "teams": teams,
            "state": GameState.LOBBY.value,
        }
    }

# -------------------------
# Kick player
# -------------------------

@router.post("/{room_id}/kick/{player_id}")
async def kick_player(room_id: str, player_id: str):
    room = get_room_or_404(room_id)

    room_state = GameState(room["state"])
    lobby = room.get("lobby", [])
    teams = room.get("teams", [])
    ready_players = room.get("ready-players", {})

    kicked_player = None

    new_lobby = []
    for p in lobby:
        if p["id"] == player_id:
            kicked_player = p
        else:
            new_lobby.append(p)

    lobby = new_lobby

    removed_from_team = None

    for team in teams:
        team_players = team.get("players", [])
        new_players = []

        for tp in team_players:
            if tp["id"] == player_id:
                kicked_player = player_id
                removed_from_team = team["id"]
            else:
                new_players.append(tp)

        team["players"] = new_players

    teams = [t for t in teams if len(t.get("players", []))> 0]

    if player_id in ready_players:
        ready_players[player_id] = False

    for t in teams:
        t["ready"] = False

    update_room(room_id, {
        "lobby": lobby,
        "teams": teams,
        "ready-players": ready_players,
        "state": GameState.LOBBY.value
    })

    await manager.broadcast(room_id, {
        "event": "player_kicked",
        "player_id": player_id,
        "removed-from_team": removed_from_team,
        "player": kicked_player,
        "room": {
            "id": room["id"],
            "name": room["name"],
            "lobby": lobby,
            "teams": teams,
            "state": GameState.LOBBY.value
        }
    })

    return {
        "message": f"Player {player_id} was kicked",
        "removed_from_team": removed_from_team,
        "player": kicked_player,
        "room": {
            "id": room["id"],
            "name": room["name"],
            "lobby": lobby,
            "state": GameState.LOBBY.value,
            "teams": teams,
        }
    }

# -------------------------
# Reset
# -------------------------

@router.post("/{room_id}/reset")
async def reset_room(room_id):
    room = get_room_or_404(room_id)

    reset_data = {
        "teans": [],
        "lobby": [],
        "ready_players": {},
        "state": GameState.LOBBY.value
    }

    update_room(room_id, reset_data)

    await manager.broadcast(room_id, {
        "event": "room_reset",
        "room": {
            "id": room["id"],
            "name": room["name"],
            "teams": [],
            "lobby": [],
            "ready_players": {},
            "state": GameState.LOBBY.value
        }
    })

    return {
        "message": "Room has been reset",
        "room": {
            "id": room["id"],
            "name": room["name"],
            "teams": [],
            "lobby": [],
            "ready_players": {},
            "state": GameState.LOBBY.value
        }
    }