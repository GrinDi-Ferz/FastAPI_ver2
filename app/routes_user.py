from fastapi import  Depends, HTTPException, APIRouter
from typing import List, Annotated

from sqlalchemy.future import select
from schema import (
    CreateUserRequest, CreateUserResponse,
    GetAdvertisementResponse, SearchAdvertisementResponse,
    SuccessResponse
)
import models
from models import Token, User
from dependancy import get_token, SessionDependency
from sqlalchemy.ext.asyncio import AsyncSession
router = APIRouter()

async def get_user_by_id(session: AsyncSession, user_id: int) -> models.User | None:
    return await session.get(models.User, user_id)


# Заглушки для авторизации и текущего пользователя
async def get_current_user(
    token: Annotated[Token, Depends(get_token)],
    session: AsyncSession = Depends(SessionDependency),
) -> User:
    user = await get_user_by_id(session, token.user_id)  # предполагается, что Token содержит user_id
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# Проверка прав
async def verify_admin(user: models.User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Только для админов")
    return user

# Проверка — пользователь или админ
async def verify_user_or_admin(user_id: int, user: models.User = Depends(get_current_user)):
    if user.role != "admin" and user.id != user_id:
        raise HTTPException(403, "Можно изменять только свои данные")
    return user

# --- Общие публичные маршруты ---

@router.post("/user", response_model=CreateUserResponse)
async def create_user(user_req: CreateUserRequest, session: AsyncSession = Depends(SessionDependency)):
    new_user = models.User(
        username=user_req.username,
        password=user_req.password,
        role=user_req.role
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return CreateUserResponse(id=new_user.id, username=new_user.username, role=new_user.role)


@router.get("/user/", response_model=List[CreateUserResponse])
async def get_users(
        current_user: models.User = Depends(get_current_user),
        session: AsyncSession = Depends(SessionDependency)
):
    # Проверка роли
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только для админов")

    result = await session.execute(select(models.User))
    users = result.scalars().all()
    return [
        CreateUserResponse(id=user.id, username=user.username, role=user.role)
        for user in users
    ]


@router.get("/user/{user_id}", response_model=CreateUserResponse)
async def get_user(user_id: int, session: AsyncSession = Depends(SessionDependency)):
    user = await session.get(models.User, user_id)
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    return CreateUserResponse(id=user.id, username=user.username, role=user.role)


@router.get("/advertisement/{ad_id}", response_model=GetAdvertisementResponse)
async def get_advertisement(ad_id: int, session: AsyncSession = Depends(SessionDependency)):
    ad = await session.get(models.Advertisement, ad_id)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    return GetAdvertisementResponse(
        id=ad.id,
        title=ad.title,
        description=ad.description,
        price=ad.price,
        author=ad.author,
        create_date=ad.create_date
    )

@router.get("/advertisement/search", response_model=SearchAdvertisementResponse)
async def search_advertisements(session: AsyncSession = Depends(SessionDependency)):
    ads_result = await session.execute(select(models.Advertisement))
    ads_list = ads_result.scalars().all()
    parsed_ads = [
        GetAdvertisementResponse(
            id=a.id,
            title=a.title,
            description=a.description,
            price=a.price,
            author=a.author,
            create_date=a.create_date
        ) for a in ads_list
    ]
    return SearchAdvertisementResponse(results=parsed_ads)

# --- Защищенные маршруты для пользователей ---

@router.patch("/user/{user_id}", response_model=CreateUserResponse)
async def update_user(
    user_id: int,
    user_req: CreateUserRequest,
    user: models.User = Depends(get_current_user),
    session: AsyncSession = Depends(SessionDependency)
):
    await verify_user_or_admin(user_id, user)
    user_obj = await session.get(models.User, user_id)
    if not user_obj:
        raise HTTPException(404, "Пользователь не найден")
    user_obj.username = user_req.username
    user_obj.role = user_req.role
    # user_obj.password = user_req.password
    await session.commit()
    await session.refresh(user_obj)
    return CreateUserResponse(id=user_obj.id, username=user_obj.username, role=user_obj.role)

@router.delete("/user/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: int,
    user: models.User = Depends(get_current_user),
    session: AsyncSession = Depends(SessionDependency)
):
    await verify_user_or_admin(user_id, user)
    user_obj = await session.get(models.User, user_id)
    if not user_obj:
        raise HTTPException(404, "Пользователь не найден")
    await session.delete(user_obj)
    await session.commit()
    return SuccessResponse(success=True)