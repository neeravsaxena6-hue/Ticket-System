from pydantic import BaseModel, ConfigDict, Field


class Signup(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1)


class Login(BaseModel):
    email: str
    password: str


class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)


class TicketReject(BaseModel):
    reason: str = Field(min_length=1)


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)