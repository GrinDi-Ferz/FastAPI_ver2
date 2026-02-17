import auth
import crud
import models
from models import User
from dependancy import SessionDependency, TokenDependency
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from lifespan import lifespan
from schema import (CreateAdvertisementRequest, CreateAdvertisementResponse, DeleteAdvertisementResponse,
                    GetAdvertisementResponse, SearchAdvertisementResponse, UpdateAdvertisementRequest,
                    UpdateAdvertisementResponse, CreateUserRequest, CreateUserResponse, LoginResponse, LoginRequest)
from sqlalchemy import select
from routes_user import router, get_current_user

app = FastAPI(
    title="Advertisements API",
    terms_of_service="",
    description="list of Advertisements",
    lifespan=lifespan,
)

app.include_router(router)

@app.post("/advertisement", tags=['advertisement_post'], response_model=CreateAdvertisementResponse)
async def create_advertisement(advertisement: CreateAdvertisementRequest, session: SessionDependency, token: TokenDependency):
    advertisement_dict = advertisement.model_dump(exclude_unset=True)
    advertisement_orm_obj = models.Advertisement(**advertisement_dict, user_id=token.user_id)
    await crud.add_item(session, advertisement_orm_obj)
    return advertisement_orm_obj.id_dict


@app.get("/advertisement/{advertisement_id}", tags=['advertisement_get'], response_model=GetAdvertisementResponse)
async def get_advertisement(advertisement_id: int, session: AsyncSession = Depends(SessionDependency)):
    advertisement_orm_obj = await crud.get_item_by_id(session, models.Advertisement, advertisement_id)
    if advertisement_orm_obj is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return advertisement_orm_obj.dict()


@app.patch("/advertisement/{advertisement_id}", tags=["advertisement_patch"], response_model=UpdateAdvertisementResponse)
async def update_advertisement(
    advertisement_id: int,
    updated_data: UpdateAdvertisementRequest,
    session: AsyncSession = Depends(SessionDependency),
    current_user: User = Depends(get_current_user)  # получаем текущего пользователя
):
    advertisement_orm_obj = await crud.get_item_by_id(session, models.Advertisement, advertisement_id)
    if advertisement_orm_obj is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    # Проверяем, что текущий пользователь — владелец объявления или админ
    if advertisement_orm_obj.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    updated_data_dict = updated_data.model_dump(exclude_unset=True)
    await crud.update_existing_item(session, advertisement_orm_obj, updated_data_dict)
    return {"status": "success"}

@app.delete("/advertisement/{advertisement_id}", tags=["advertisement_delete"], response_model=DeleteAdvertisementResponse)
async def delete_advertisement(
    advertisement_id: int,
    session: AsyncSession = Depends(SessionDependency),
    current_user: User = Depends(get_current_user)
):
    advertisement_orm_obj = await crud.get_item_by_id(session, models.Advertisement, advertisement_id)
    if advertisement_orm_obj is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    if advertisement_orm_obj.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    await crud.delete_item(session, advertisement_orm_obj)
    return {"status": "success"}

@app.get("/advertisement", response_model=SearchAdvertisementResponse)
async def search_advertisement(
        session: AsyncSession = Depends(SessionDependency),
        title: str = None,
        description: str = None,
        author: str = None,
        min_price: int = None,
        max_price: int = None,
        limit: int = 100,  # максимальное число результатов
        offset: int = 0  # сдвиг для пагинации
):
    query = select(models.Advertisement)
    if title:
        query = query.where(models.Advertisement.title.ilike(f"%{title}%"))
    if description:
        query = query.where(models.Advertisement.description.ilike(f"%{description}%"))
    if author:
        query = query.where(models.Advertisement.author.ilike(f"%{author}%"))
    if min_price is not None:
        query = query.where(models.Advertisement.price >= min_price)
    if max_price is not None:
        query = query.where(models.Advertisement.price <= max_price)

    query = query.offset(offset).limit(limit)

    advertisements = await session.scalars(query)
    return {"results": [advertisement.dict() for advertisement in advertisements]}


@app.post("/login", tags=["login"], response_model=LoginResponse)
async def login(login_data: LoginRequest, session: SessionDependency):
    query = select(models.User).where(models.User.username == login_data.username)
    user = await session.scalar(query)
    if user is None:
        raise HTTPException(401, "Invalid credentials")
    if not auth.check_password(login_data.password, user.password):
        raise HTTPException(401, "Invalid credentials")
    token = models.Token(user_id=user.id)
    await crud.add_item(session, token)
    return token.dict()


@app.post("/user", tags=["user"], response_model=CreateUserResponse)
async def create_user(user_data: CreateUserRequest, session: SessionDependency):
    user_dict = user_data.model_dump(exclude_unset=True)
    user_dict["password"] = auth.hash_password(user_dict["password"])
    user_orm_obj = models.User(**user_dict)
    await crud.add_item(session, user_orm_obj)
    return user_orm_obj.id_dict