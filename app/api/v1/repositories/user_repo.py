from app.models.users_models import User
from app.api.v1.dependencies import DBSession
from app.schemas.user_schema import UserCreate
from sqlalchemy import select
from fastapi import HTTPException


async def new_user(db:DBSession, user_data:UserCreate) -> User:
    user = User(
        fullname = user_data.fullname,
        email = user_data.email,
        password = user_data.password
    )
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, 
            detail={'message': 'Error inesperado', 'contexto': str(e)}
        )


async def get_user_by_email(db:DBSession,email:str) -> User | None:
    stmt = select(User).where(
        User.email == email
    )
    exist = await db.execute(stmt)

    return exist.scalar_one_or_none()