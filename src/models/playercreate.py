from pydantic import BaseModel
from .account import Account
from .player import Player

class PlayerCreate(BaseModel):
    player: Player
    account: Account