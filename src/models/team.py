from pydantic import BaseModel, field_validator
from .player import Player

class Team(BaseModel):
    id: str
    name: str
    players: list[Player]
    ready: bool = False

    @field_validator("players")
    def validate_players(cls, players):
        if len(players) > 2:
            raise ValueError("Maximum 2 players in a team.")
        return players

    def add_player(self, player: Player):
        if len(self.players) >= 2:
            raise ValueError("Maximum 2 players in a team")
        self.players.append(player)

    def set_ready(self, value: bool):
            self.ready = value
