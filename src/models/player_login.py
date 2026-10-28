from pydantic import BaseModel, Field

class LoginReq(BaseModel):
    email: str
    password: str