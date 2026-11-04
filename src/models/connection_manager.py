from fastapi import WebSocket

# -----------------------------
# Room connection manager
# -----------------------------

class ConnectionManager:
    def __init__(self):
        self.rooms: dict[str, list[dict]] = {}
        self.active_players: list[str] = []

    async def connect(self, room_id: str, websocket: WebSocket, player_id: str):
        await websocket.accept()
        self.active_players.append(player_id)
        self.rooms.setdefault(room_id, []).append({
            "ws": websocket,
            "player_id": player_id,
            })
        
        await self.broadcast(room_id, {
            "event": "player_joined",
            "connected_player_id": player_id,
            "active_player_ids": self.active_players
        })
        

    async def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id not in self.rooms:
            return

        disconnected_player = None
        for conn in self.rooms[room_id]:
            if conn["ws"] is websocket:
                disconnected_player = conn["player_id"]
                break

        if disconnected_player in self.active_players:
            self.active_players.remove(disconnected_player)
    
        await self.broadcast(room_id, {
            "event": "player_disconnected",
            "disconnected_player_id": disconnected_player,
            "active_player_ids": self.active_players
        })
        
        self.rooms[room_id] = [
            conn for conn in self.rooms[room_id]
            if conn["ws"] is not websocket
        ]

        

    async def broadcast(self, room_id: str, message: dict):
        conns = self.rooms.get(room_id, [])
        alive_conns = []
        for conn in conns:
            try:
                await conn["ws"].send_json(message)
                alive_conns.append(conn)
            except Exception:
                pass
        self.rooms[room_id] = alive_conns

        return len(alive_conns)

# -----------------------------
# Room list connection manager
# -----------------------------

class RoomListConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: str):
        for ws in self.active:
            await ws.send_json(message)

