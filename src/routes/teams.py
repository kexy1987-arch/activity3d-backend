from fastapi import APIRouter
from models import Player, Team, GameState
import uuid
import asyncio
from dotenv import load_dotenv
load_dotenv()
from helpers import all_ready, get_room_or_404, run_countdown, update_room, to_json_safe, connection_manager, find_player_team

manager = connection_manager
router = APIRouter(prefix="/teams")

# -------------------------
# Create team
# -------------------------

@router.post("/{room_id}/create_team")
async def create_team(room_id: str, color: str, player: Player):
    room = get_room_or_404(room_id)
    dump_player = player.model_dump(mode="json")

    teams = room.get("teams", [])
    
    lobby = room.get("lobby", [])

    team_id = str(uuid.uuid4())
    team = Team(
        id=team_id, 
        name=f"Team {len(teams) + 1}", 
        color= color,
        players=[dump_player],
        ready=False
    ).model_dump(mode="json")

    teams.append(team)

    lobby = [p for p in lobby if p["id"] != player.id]

    update_room(room_id, {
        "teams": teams, 
        "lobby": lobby,
        "state": GameState.LOBBY.value
        })

    print("ROOM: ",room["id"])

    broadcast = await manager.broadcast(room_id, to_json_safe({
        "event": "player_created_team",
        "room": room
    }))

    print("BROADCAST:", broadcast)

    return {
        "message": f"{player.name} created a team",
        "team": team,
        "room": {
            "id": room["id"],
            "name": room["name"],
            "teams": teams,
            "lobby": lobby,
            "state": GameState.LOBBY.value
        },
    }


# -------------------------
# Join team
# -------------------------

@router.post("/{room_id}/{team_id}/join")
async def join_team(room_id: str, team_id: str, player: Player):
    print("ROOMID", room_id)
    print("TEAMID", team_id)
    room = get_room_or_404(room_id)
    teams = room.get("teams", [])
    lobby = room.get("lobby", [])

    old_team = find_player_team(player.id, teams)

    if old_team:
        old_team["players"] = [
            p for p in old_team.get("players", [])
            if p["id"] != player.id
        ]

    team = next((t for t in teams if t["id"] == team_id), None)
    if not team:
        return {"error": "Team not found"}

    team_players = team.get("players", [])
    team_players.append(player.model_dump(mode="json"))
    team["players"] = team_players

    lobby = [p for p in lobby if p["id"] != player.id]

    for t in teams:
        t["ready"] = False

    ready_players = room.get("ready_players", {})
    ready_players[player.id] = False

    update_room(room_id, {
        "teams": teams, 
        "lobby": lobby,
        "ready_players": ready_players,
        "state": GameState.LOBBY.value
        })

    await manager.broadcast(room_id, {
        "event": "player_joined_team",
        "team": team,
        "player": player.model_dump(mode="json"),
        "room": {
            "id": room["id"],
            "name": room["name"],
            "teams": teams,
            "lobby": lobby,
            "state": GameState.LOBBY.value
        }
    })

    return {
        "message": f"{player.name} joined team {team.get('name', '')}",
        "team": team,
        "room": {
            "id": room["id"],
            "name": room["name"],
            "teams": teams,
            "lobby": lobby,
            "state": GameState.LOBBY.value
        }
    }

# -------------------------
# Team ready
# -------------------------

@router.post("/{room_id}/{team_id}/ready")
async def set_team_ready(room_id: str, team_id: str, value: bool):
    room = get_room_or_404(room_id)

    teams = room.get("teams", [])
    team = next((t for t in teams if t["id"] == team_id), None)
    if not team:
        return {"error": "Team not found"}

    team["ready"] = value

    update_room(room_id, {"teams": teams})

    await manager.broadcast(room_id, {
        "event": "team_ready",
        "team_id": team_id,
        "value": value
    })

    room_state = GameState(room["state"])

    if value is False:
        update_room(room_id, {"state": GameState.LOBBY.value})

        await manager.broadcast(room_id, {
            "event": "countdown_stopped"
        })

    if all_ready(room):

        if room_state == GameState.LOBBY:
            update_room(room_id, {"state": GameState.COUNTDOWN})
            asyncio.create_task(run_countdown(room_id))

            await manager.broadcast(room_id, {
                            "event": "countdown_started"
                        })

            return {
                "message": "countdown_started",
                "state": GameState.COUNTDOWN.value
            }

    return {
        "message": f"Team {team.get('name', '')} is now {'ready' if value else 'not ready'}",
        "team": team
    }