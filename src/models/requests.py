from pydantic import BaseModel
from src.models.player import Player
from src.models.team import Team

class RoomCreateRequest(BaseModel):
    name: str
    creator: Player
    teams: list[Team] = []
    lobby: list[Player] = []