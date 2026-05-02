from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from app.core.config import Settings

settings = Settings()

ph = PasswordHasher()


def hash_password(senha: str) -> str:
    return ph.hash(senha)


def verify_password(password: str, db_password: str) -> bool:
    try:
        ph.verify(hash=db_password, password=password)
        return True

    except VerificationError:
        return False


def create_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACESSES_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({'exp': expire})

    encode_jwt = jwt.encode(to_encode, settings.SECRET_KEY, settings.ALGORITHM)
    return encode_jwt
