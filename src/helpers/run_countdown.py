from .update_room import update_room
from models import GameState
from .get_room_or_404 import get_room_or_404
from .all_ready import all_ready
from .managers import connection_manager
import asyncio


manager = connection_manager

async def run_countdown(room_id: str):
    room = get_room_or_404(room_id)

    countdown_seconds = room.get("countdown_seconds", 5)

    update_room(room_id, {"state": GameState.COUNTDOWN.value})

    await manager.broadcast(room_id, {
        "event": "countdown_started",
        "seconds": countdown_seconds,
        "room": room
    })

    for i in range(countdown_seconds, 0, -1):

        room = get_room_or_404(room_id)

        if(not all_ready(room)):
            update_room(room_id, {"state": GameState.LOBBY.value})

            await manager.broadcast(room_id, {
                "event": "countdown_stopped",
                "room": room
            })
            return

        await manager.broadcast(room_id, {
            "event": "countdown_tick",
            "value": 1,
            "room": room
        })

        await asyncio.sleep(1)

    update_room(room_id, {
        "state": GameState.PLAYING.value
    })

    await manager.broadcast(room_id, {
        "event": "game_started",
        "room": get_room_or_404(room_id)
    })