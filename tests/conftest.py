import asyncio
from unittest.mock import AsyncMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app import models
from app.api.v1.dependencies import get_db, get_redis
from app.api.v1.repositories import auth_repo
from app.db.base import Base
from app.main import app

TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'


test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope='function')
async def init_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope='function')
async def db_session(init_test_db):
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope='session')
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='function')
async def client(db_session):
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        mock_redis = AsyncMock()

        mock_redis.exists.return_value = 0

        mock_redis.get.return_value = None

        yield mock_redis

    app.dependency_overrides[get_db] = override_get_db

    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope='function')
async def user_client(db_session):
    raw_password = 'Senha12@#'

    user = models.User(
        fullname='Full Name',
        email='user@example.com',
        password=auth_repo.hash_password(raw_password),
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user, raw_password


@pytest_asyncio.fixture(scope='function')
async def user_client2(db_session):
    raw_password = 'Senha12@#'

    user = models.User(
        fullname='Full Name',
        email='user2@example.com',
        password=auth_repo.hash_password(raw_password),
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user, raw_password


@pytest_asyncio.fixture(scope='function')
async def token_client(client, user_client):
    data = {'username': 'user@example.com', 'password': 'Senha12@#'}

    response = await client.post('/api/v1/login', data=data)

    status = 200

    assert response.status_code == status

    return client


@pytest_asyncio.fixture(scope='function')
async def token_user_does_not_exist(client):
    cookie = auth_repo.create_token(data={'sub': 'email@não.existe'})

    client.cookies.set('Login_info', cookie)

    return client
