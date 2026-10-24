from pydantic import BaseModel, Field
from datetime import datetime, UTC

class Account(BaseModel):
    email: str
    password: str