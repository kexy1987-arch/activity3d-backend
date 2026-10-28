from pydantic import BaseModel, Field
from datetime import datetime, UTC

class Player(BaseModel):
    id: str | None = None
    name: str
    is_guest: bool = True
    auth_id: str | None = None
    avatar_url: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    room_id: str | None = None
    first_login : bool | None = None