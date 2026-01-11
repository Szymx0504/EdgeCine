from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    name: str
    password: str

class UserUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)

class UserResponse(BaseModel):
    id: int
    name: str

class InteractionCreate(BaseModel):
    user_id: int
    film_id: int
    interaction_type: str = Field(..., pattern="^(like|rate_[1-5])$")

class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = Field(None, pattern="^(like|rate_[1-5])$")

class InteractionResponse(BaseModel):
    id: int
    user_id: int
    film_id: int
    interaction_type: str
    interaction_timestamp: datetime
