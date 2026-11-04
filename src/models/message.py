from pydantic import BaseModel

class Message(BaseModel):
    player_name: str
    message: str
    avatar_url: str