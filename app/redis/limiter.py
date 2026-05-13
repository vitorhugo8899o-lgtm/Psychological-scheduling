from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import Settings

limiter = Limiter(key_func=get_remote_address, storage_uri=f'{Settings().REDIS_URL}')
