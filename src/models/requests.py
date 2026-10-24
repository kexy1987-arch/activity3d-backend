from pydantic import BaseModel
from models.player import Player
from models.team import Team

class RoomCreateRequest(BaseModel):
    name: str
    creator: Player
    teams: list[Team] = []
    lobby: list[Player] = []