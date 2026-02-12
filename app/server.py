import datetime
import auth
import crud
import models
from dependancy import SessionDependency, TokenDependency
from fastapi import FastAPI, HTTPException
from lifespan import lifespan
from models import Session
from schema import (CreateAdvirtesmentRequest, CreateAdvirtesmentResponse, DeleteAdvirtesmentResponse,
                    GetAdvirtesmentResponse, SearchAdvirtesmentResponse, UpdateAdvirtesmentRequest,
                    UpdateAdvirtesmentResponse, CreateUserRequest, CreateUserResponse, LoginResponse, LoginRequest)
from sqlalchemy import select
from routes_user import router

app = FastAPI(
    Description="Advertisements API",
    terms_of_service="",
    description="list of Advertisements",
    lifespan=lifespan,
)

app.include_router(router)

@app.post("/advertisement", tags=['advertisment_post'], response_model=CreateAdvirtesmentResponse)
async def create_advertisement(advertisment: CreateAdvirtesmentRequest, session: SessionDependency, token: TokenDependency):
    advertisment_dict = advertisment.model_dump(exclude_unset=True)
    advertisment_orm_obj = models.Advertisment(**advertisment_dict, user_id=token.user_id)
    await crud.add_item(session, advertisment_orm_obj)
    return advertisment_orm_obj.id_dict


@app.get("/advertisement/{advertisment_id}", tags=['advertisment_get'], response_model=GetAdvirtesmentResponse)
async def get_advertisement(advertisment_id: int, session: SessionDependency, token: TokenDependency):
    advertisment_orm_obj = await crud.get_item_by_id(session, models.Advertisment, advertisment_id)
    if token.user.role == 'admin' or token.user_id == advertisment_orm_obj.user_id:
        return advertisment_orm_obj.dict
    raise HTTPException(403, "influent privileges")


@app.patch("/advertisement/{advertisment_id}", tags=["advertisement_patch"], response_model=UpdateAdvirtesmentResponse)
async def update_advertisement(
    advertisment_id: int,
    updated_data: UpdateAdvirtesmentRequest,
    session: SessionDependency
):
    updated_data_dict = updated_data.model_dump(exclude_unset=True)
    advertisment_orm_obj = await crud.get_item_by_id(session, models.Advertisment, advertisment_id)
    await crud.update_existing_item(session, advertisment_orm_obj, updated_data_dict)
    return {"status": "success"}

@app.delete("/advertisement/{advertisment_id}", tags=["advertisement_delete"], response_model=DeleteAdvirtesmentResponse)
async def delete_advertisement(advertisment_id: int, session: SessionDependency):
    advertisment_orm_obj = await crud.get_item_by_id(session, models.Advertisment, advertisment_id)
    await crud.delete_item(session, advertisment_orm_obj)
    return {"status": "success"}

@app.get("/advertisement", response_model=SearchAdvirtesmentResponse)
async def search_advirtesment(
        session: SessionDependency,
        title: str = None,
        description: str = None,
        author: str = None,
        price: int = None
):
    query = select(models.Advertisment)
    if title:
        query = query.where(models.Advertisment.title.ilike(f"%{title}%"))
    if description:
        query = query.where(models.Advertisment.description.ilike(f"%{description}%"))
    if author:
        query = query.where(models.Advertisment.author.ilike(f"%{author}%"))
    if price:
        query = query.where(models.Advertisment.price == price)

    advertisments = await session.scalars(query.limit(100))
    return {"results": [advertisment.dict for advertisment in advertisments]}


@app.post("/login", tags=["login"], response_model=LoginResponse)
async def login(login_data: LoginRequest, session: SessionDependency):
    query = select(models.User).where(models.User.name == login_data.name)
    user = await session.scalar(query)
    if user is None:
        raise HTTPException(401, "Invalid credentials")
    if not auth.check_password(login_data.password, user.password):
        raise HTTPException(401, "Invalid credentials")
    token = models.Token(user_id=user.id)
    await crud.add_item(session, token)
    return token.dict


@app.post("/user", tags=["user"], response_model=CreateUserResponse)
async def create_user(user_data: CreateUserRequest, session: SessionDependency):
    user_dict = user_data.model_dump(exclude_unset=True)
    user_dict["password"] = auth.hash_password(user_dict["password"])
    user_orm_obj = models.User(**user_dict)
    await crud.add_item(session, user_orm_obj)
    return user_orm_obj.id_dict