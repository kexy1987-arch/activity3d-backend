from pydantic import BaseModel

class PlayerUpdate(BaseModel):
    id: str | None = None
    name: str
    avatar_url: str | None = None