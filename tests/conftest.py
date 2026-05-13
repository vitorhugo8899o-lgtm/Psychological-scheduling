import os  #noqa

os.environ['TESTING'] = 'true'  #noqa

from app.core.config import settings  #noqa
from app.main import app  # noqa


import asyncio
from datetime import datetime, time, timedelta, timezone
from unittest.mock import AsyncMock, patch

import jwt
import pytest
import pytest_asyncio
from freezegun import freeze_time
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app import models
from app.api.v1.dependencies import get_db, get_redis
from app.api.v1.repositories import auth_repo, payment_repo
from app.db.base import Base
from app.schemas.custom_schema import AppointmentStatus

TEST_DATABASE_URL = 'postgresql+asyncpg://postgres:postgres@localhost:5433/test_db'


test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(autouse=True)
def bypass_lifespan_db_check():
    with patch('app.main.check_database_connection') as mock_check:
        mock_check.return_value = None
        yield mock_check


@pytest_asyncio.fixture(scope='function')
async def init_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope='function')
async def db_session():

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


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

    return user


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

    return user


@pytest_asyncio.fixture(scope='function')
async def user_adm(db_session):
    raw_password = 'Senha12@#'

    user = models.User(
        fullname='Full Name',
        email='useradm@example.com',
        password=auth_repo.hash_password(raw_password),
        role='adm',
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture(scope='function')
async def user_psych(db_session):
    raw_password = 'Senha12@#'

    user = models.User(
        fullname='Full Name',
        email='userpsych@example.com',
        password=auth_repo.hash_password(raw_password),
        role='psychologist',
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    psych = models.Psychologist(user=user, crp='CRP 01/5596')

    db_session.add(psych)
    await db_session.commit()

    return user


@pytest_asyncio.fixture(scope='function')
async def user_psych_payment(db_session):
    raw_password = 'Senha12@#'

    user = models.User(
        fullname='Full Name',
        email='userpsych@example.com',
        password=auth_repo.hash_password(raw_password),
        role='psychologist',
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    psych = models.Psychologist(user=user, crp='CRP 01/5596')

    db_session.add(psych)
    await db_session.commit()

    return psych


@pytest_asyncio.fixture(scope='function')
async def fake_psych(db_session):
    raw_password = 'Senha12@#'

    user = models.User(
        fullname='Full Name',
        email='userfakepsych@example.com',
        password=auth_repo.hash_password(raw_password),
        role='psychologist',
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture(scope='function')
async def token_client(client, user_client):
    data = {'username': 'user@example.com', 'password': 'Senha12@#'}

    response = await client.post('/api/v1/login', data=data)

    status = 200

    assert response.status_code == status

    return client


@pytest_asyncio.fixture(scope='function')
async def token_adm(client, user_adm):
    data = {'username': 'useradm@example.com', 'password': 'Senha12@#'}

    response = await client.post('/api/v1/login', data=data)

    status = 200

    assert response.status_code == status

    return client


@pytest_asyncio.fixture(scope='function')
async def token_psych(client, user_psych):
    data = {'username': 'userpsych@example.com', 'password': 'Senha12@#'}

    response = await client.post('/api/v1/login', data=data)

    status = 200

    assert response.status_code == status

    return client


@pytest_asyncio.fixture(scope='function')
async def token_fakepsych(client, fake_psych):
    data = {'username': 'userfakepsych@example.com', 'password': 'Senha12@#'}

    response = await client.post('/api/v1/login', data=data)

    status = 200

    assert response.status_code == status

    return client


@pytest_asyncio.fixture(scope='function')
async def availability(db_session, user_psych):
    days = [0, 1, 2, 3, 4, 5, 6]
    availability_save = []
    for d in days:
        new_availability = models.Avaliabilite(
            id_psychologist=user_psych.id,
            day_of_the_week=d,
            start_time=time(8, 10),
            end_time=time(12, 30),
        )

        availability_save.append(new_availability)

    db_session.add_all(availability_save)
    await db_session.commit()

    return user_psych


@pytest_asyncio.fixture(scope='function')
async def availability2(db_session, user_psych):
    days = [0, 1, 2, 3, 4, 5, 6]
    availability_save = []
    for d in days:
        new_availability = models.Avaliabilite(
            id_psychologist=user_psych.id,
            day_of_the_week=d,
            start_time=time(9, 10),
            end_time=time(13, 30),
        )

        availability_save.append(new_availability)

    db_session.add_all(availability_save)
    await db_session.commit()

    return user_psych


@pytest_asyncio.fixture(scope='function')
async def availability_paymenttest(db_session, user_psych_payment):
    days = [0, 1, 2, 3, 4, 5, 6]
    availability_save = []
    for d in days:
        new_availability = models.Avaliabilite(
            id_psychologist=user_psych_payment.id,
            day_of_the_week=d,
            start_time=time(9, 10),
            end_time=time(13, 30),
        )

        availability_save.append(new_availability)

    db_session.add_all(availability_save)
    await db_session.commit()

    return user_psych_payment


@pytest_asyncio.fixture(scope='function')
async def service(db_session):
    new_service = models.Service(
        name='Terapia de casal',
        description='Terapia realizada com um casal',
        price=90.00,
        duration_minutes=50,
    )

    db_session.add(new_service)
    await db_session.commit()
    await db_session.refresh(new_service)

    return new_service


@pytest_asyncio.fixture(scope='function')
async def service2(db_session):
    new_service = models.Service(
        name='Terapia Parecida',
        description='Nome parecido para ser pego no filtro',
        price=90.00,
        duration_minutes=50,
    )

    db_session.add(new_service)
    await db_session.commit()


@pytest_asyncio.fixture(scope='function')
async def fake_token(client):
    token = auth_repo.create_token(data={'not_sub': 'invalid'})

    client.cookies.set('Login_info', token)

    return client


@pytest_asyncio.fixture(scope='function')
async def expired_token_client(client):
    expired_payload = {
        'sub': 'user@example.com',
        'exp': datetime.now(timezone.utc) - timedelta(minutes=1),
    }

    token = jwt.encode(
        expired_payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    client.cookies.set('Login_info', token)

    return client


@pytest_asyncio.fixture(scope='function')
async def not_token(client):
    token = 'not token'

    client.cookies.set('Login_info', token)

    return client


@pytest_asyncio.fixture(scope='function')
async def not_exists_user_token(client):
    payload = {'sub': 'user@example.com'}

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    client.cookies.set('Login_info', token)

    return client


@pytest_asyncio.fixture(scope='function')
async def schedule(
    db_session,
    service,
    availability,
    user_client,
):
    appointment = models.Appointment(
        id_client=user_client.id,
        id_psychologist=availability.id,
        id_service=service.id,
        date_time=datetime(2026, 5, 11, 12, 30, tzinfo=timezone.utc),
    )

    db_session.add(appointment)
    await db_session.commit()
    await db_session.refresh(appointment)

    return appointment


@pytest_asyncio.fixture(scope='function')
async def schedule2(
    db_session,
    service,
    availability,
    user_client,
):
    appointment = models.Appointment(
        id_client=user_client.id,
        id_psychologist=availability.id,
        id_service=service.id,
        status=AppointmentStatus.confirmed,
        date_time=datetime(2026, 5, 11, 14, 30, tzinfo=timezone.utc),
    )

    db_session.add(appointment)
    await db_session.commit()
    await db_session.refresh(appointment)

    return appointment


@pytest_asyncio.fixture(scope='function')
async def schedule_psych(
    db_session,
    service,
    availability,
    user_client2,
):
    appointment = models.Appointment(
        id_client=user_client2.id,
        id_psychologist=availability.id,
        id_service=service.id,
        date_time=datetime(2026, 5, 11, 12, 30, tzinfo=timezone.utc),
    )

    db_session.add(appointment)
    await db_session.commit()
    await db_session.refresh(appointment)

    return appointment


@pytest_asyncio.fixture(scope='function')
async def schedule_payment(
    db_session,
    service,
    availability_paymenttest,
    user_client,
):
    appointment = models.Appointment(
        id_client=user_client.id,
        id_psychologist=availability_paymenttest.id,
        id_service=service.id,
        status=AppointmentStatus.confirmed,
        date_time=datetime(2026, 5, 11, 14, 30, tzinfo=timezone.utc),
    )

    db_session.add(appointment)
    await db_session.commit()
    await db_session.refresh(appointment)

    return appointment


@pytest.fixture(autouse=True)
def frozen_time():
    with freeze_time('2026-05-11'):
        yield


@patch('app.api.v1.repositories.sdk.preference.create')
async def test_create_payment(mock_create):
    mock_create.return_value = {
        'response': {'id': '1', 'init_point': 'https://checkout-fake.com'}
    }

    result = await payment_repo.create_preference(...)

    assert result['checkout_url'] == 'https://checkout-fake.com'


@pytest_asyncio.fixture(scope='function')
async def Payment(db_session, schedule_payment):
    new_payment = models.Payment(
        id_mercado_pago=123,
        id_appointment=f'{schedule_payment.id}',
        amount=90.0,
        status='pending',
    )

    db_session.add(new_payment)
    await db_session.commit()
    await db_session.refresh(new_payment)

    return new_payment
