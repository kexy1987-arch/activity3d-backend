from pydantic import BaseModel
import datetime

class Player(BaseModel):
    id: str | None = None
    name: str
    is_guest: bool = True
    auth_id: str | None = None
    avatar_url: str | None = None
    created_at: datetime = datetime.utcnow()
    last_seen: datetime = datetime.utcnow()
    room_id: str | None = None
