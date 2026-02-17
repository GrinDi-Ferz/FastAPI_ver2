import datetime
import uuid
import config
from sqlalchemy import DateTime, Integer, String, func, Float, ForeignKey, UUID
from sqlalchemy.ext.asyncio import (AsyncAttrs, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from custom_tupes import ROLE
engine = create_async_engine(config.PG_DSN)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase, AsyncAttrs):

    @property
    def id_dict(self):
        return {"id": self.id}


class Token(Base):
    __tablename__ = "token"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, server_default=func.gen_random_uuid()
    )
    create_time: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship("User", lazy="joined", back_populates="tokens")

    @property
    def dict(self):
        return {"token": str(self.token)}


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)
    role: Mapped[ROLE] = mapped_column(String, default="user")
    tokens: Mapped[list[Token]] = relationship(
        "Token", lazy="joined", back_populates="user"
    )
    advertisements: Mapped[list["Advertisement"]] = relationship(
        "Advertisement", lazy="joined", back_populates="user"
    )

    @property
    def dict(self):
        return {"id": self.id, "username": self.username}

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class Advertisement(Base):
    __tablename__ = "advertisements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    price: Mapped[float] = mapped_column(Float)
    author: Mapped[str] = mapped_column(String, index=True)
    create_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship("User", lazy="joined", back_populates="advertisements")

    @property
    def dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "author": self.author,
            "create_date": self.create_date.isoformat() if self.create_date else None,
        }


ORM_OBJ = Advertisement | User | Token
ORM_CLS = type[Advertisement] | type[User] | type[Token]

async def init_orm():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_orm():
    await engine.dispose()