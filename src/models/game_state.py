from enum import Enum

class GameState(str, Enum):
    LOBBY = "lobby"
    COUNTDOWN = "countdown"
    PLAYING = "playing"
    FINISHED = "finished"
