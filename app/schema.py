import datetime
import uuid
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr

class BaseUserRequest(BaseModel):
    username: str
    password: str


class IdResponse(BaseModel):
    id: int


class SuccessResponse(BaseModel):
    status: Literal["success"] = "success"


class CreateAdvertisementRequest(BaseModel):
    title: str
    description: str
    price: float
    author: str

    class Config:
        orm_mode = True


class CreateAdvertisementResponse(IdResponse):
    pass


class UpdateAdvertisementRequest(BaseModel):
    title: str = None
    description: str = None
    price: float = None
    author: str = None

class UpdateAdvertisementResponse(SuccessResponse):
    pass


class GetAdvertisementResponse(BaseModel):
    id: int
    title: str
    description: str = None
    price: float = None
    author: str
    create_date: datetime.datetime


class SearchAdvertisementResponse(BaseModel):
    results: list[GetAdvertisementResponse]


class DeleteAdvertisementResponse(SuccessResponse):
    pass


class CreateUserRequest(BaseUserRequest):
    role: Literal['user', 'admin'] = 'user'

    class Config:
        orm_mode = True


class CreateUserResponse(IdResponse):
    username: str
    role: Literal['user', 'admin']

    class Config:
        orm_mode = True


class LoginRequest(BaseUserRequest):
    pass


class LoginResponse(BaseModel):
    token: uuid.UUID