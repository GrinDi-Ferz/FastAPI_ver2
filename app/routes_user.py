from fastapi import FastAPI, Depends, HTTPException, APIRouter
from typing import List
import datetime
from schema import (
    CreateUserRequest, CreateUserResponse,
    LoginRequest, LoginResponse,
    CreateAdvirtesmentRequest, CreateAdvirtesmentResponse,
    UpdateAdvirtesmentRequest, UpdateAdvirtesmentResponse,
    GetAdvirtesmentResponse, SearchAdvirtesmentResponse,
    IdResponse, SuccessResponse
)
import models
from sqlalchemy.ext.asyncio import AsyncSession
router = APIRouter()


# Заглушки для авторизации и текущего пользователя
async def get_current_user() -> models.User:
    try:
        user = await get_current_user()  # Ваша функция авторизации
        return user
    except HTTPException:
        return None

async def get_user_by_id(user_id: int) -> models.User:
    async with models.Session() as session:
        return await session.get(models.User, user_id)

# Проверка прав
async def verify_admin(user: models.User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Только для админов")
    return user

async def verify_user_or_admin(user_id: int, user: models.User = Depends(get_current_user)):
    if user.role != "admin" and user.id != user_id:
        raise HTTPException(403, "Можно изменять только свои данные")
    return user

# --- Общие публичные маршруты ---

@router.post("/user", response_model=CreateUserResponse)
async def create_user(user_req: CreateUserRequest):
    # Создание пользователя
    async with models.Session() as session:
        new_user = models.User(
            name=user_req.email,
            password=user_req.password,
            role=user_req.role
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return CreateUserResponse(id=new_user.id, email=new_user.name, role=new_user.role)

@router.get("/user/{user_id}", response_model=CreateUserResponse)
async def get_user(user_id: int):
    async with models.Session() as session:
        user = await session.get(models.User, user_id)
        if not user:
            raise HTTPException(404, "Пользователь не найден")
        return CreateUserResponse(id=user.id, email=user.name, role=user.role)

@router.get("/advertisement/{ad_id}", response_model=GetAdvirtesmentResponse)
async def get_advertisement(ad_id: int):
    async with models.Session() as session:
        ad = await session.get(models.Advertisement, ad_id)
        if not ad:
            raise HTTPException(404, "Объявление не найдено")
        return GetAdvirtesmentResponse(
            id=ad.id,
            title=ad.title,
            description=ad.description,
            price=ad.price,
            author=ad.author,
            create_date=ad.create_date
        )

@router.get("/advertisement/search", response_model=SearchAdvirtesmentResponse)
async def search_advertisements():
    async with models.Session() as session:
        ads = await session.execute(
            "SELECT * FROM advertisements"
        )
        ads_list = ads.scalars().all()
        parsed_ads = [
            GetAdvirtesmentResponse(
                id=a.id,
                title=a.title,
                description=a.description,
                price=a.price,
                author=a.author,
                create_date=a.create_date
            ) for a in ads_list
        ]
        return SearchAdvirtesmentResponse(results=parsed_ads)

# --- Защищенные маршруты для пользователей ---

@router.post("/user/{user_id}", response_model=CreateUserResponse)
async def update_user(user_id: int, user_req: CreateUserRequest, user: models.User = Depends(get_current_user)):
    await verify_user_or_admin(user_id, user)
    async with models.Session() as session:
        user_obj = await session.get(models.User, user_id)
        if not user_obj:
            raise HTTPException(404, "Пользователь не найден")
        user_obj.name = user_req.email
        user_obj.role = user_req.role
        await session.commit()
        await session.refresh(user_obj)
        return CreateUserResponse(id=user_obj.id, email=user_obj.name, role=user_obj.role)

@router.delete("/user/{user_id}", response_model=SuccessResponse)
async def delete_user(user_id: int, user: models.User = Depends(get_current_user)):
    await verify_user_or_admin(user_id, user)
    async with models.Session() as session:
        user_obj = await session.get(models.User, user_id)
        if not user_obj:
            raise HTTPException(404, "Пользователь не найден")
        await session.delete(user_obj)
        await session.commit()
        return SuccessResponse(success=True)