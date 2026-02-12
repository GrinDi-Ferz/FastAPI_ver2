import datetime
import uuid
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr

class BaseUserRequest(BaseModel):
    name: str
    password: str


class IdResponse(BaseModel):
    id: int


class SuccessResponse(BaseModel):
    status: Literal["success"]


class CreateAdvirtesmentRequest(BaseModel):
    title: str
    description: str
    price: float
    author: str


class CreateAdvirtesmentResponse(IdResponse):
    pass


class UpdateAdvirtesmentRequest(BaseModel):
    title: str = None
    description: str = None
    price: float = None
    author: str = None

class UpdateAdvirtesmentResponse(SuccessResponse):
    pass


class GetAdvirtesmentResponse(BaseModel):
    id: int
    title: str
    description: str = None
    price: float = None
    author: str
    create_date: datetime.datetime


class SearchAdvirtesmentResponse(BaseModel):
    results: list[GetAdvirtesmentResponse]


class DeleteAdvirtesmentResponse(SuccessResponse):
    pass


class CreateUserRequest(BaseUserRequest):
    email: EmailStr
    password: str
    role: str = 'user'  # по умолчанию 'user'


    class Config:
        orm_mode = True


class CreateUserResponse(IdResponse):
    id: int
    email: str
    role: str
    # Добавьте остальные поля

    class Config:
        orm_mode = True


class LoginRequest(BaseUserRequest):
    pass


class LoginResponse(BaseModel):
    token: uuid.UUID