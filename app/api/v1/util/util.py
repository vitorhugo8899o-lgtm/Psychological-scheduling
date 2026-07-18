import asyncio
import logging
from datetime import UTC, datetime, timedelta, timezone
from functools import wraps
from time import perf_counter
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Generic, TypeVar
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from redis.exceptions import RedisError

if TYPE_CHECKING:
    from app.api.v1.dependencies import rediscon

T = TypeVar('T', bound=BaseModel)


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def format_hour_br(date: datetime):
    br_tmz = ZoneInfo('America/Sao_Paulo')

    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)

    date_format = date.astimezone(br_tmz)

    return date_format.strftime('%d/%m/%Y às %H:%M')


def time_passed(date_compare: datetime) -> bool:
    return datetime.now(UTC) >= date_compare + timedelta(hours=24)


def cauculation_rate(total_appointments: int, total_compared: int):
    if total_appointments == 0 or total_compared == 0:
        return None

    rate = (total_compared / total_appointments) * 100
    return f'{rate:.2f}'.replace('.', ',')


def measure_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        init = perf_counter()

        result = await func(*args, **kwargs)

        end = perf_counter()
        print(f'{func.__name__} executou em {(end - init):.6f}s')

        return result

    return wrapper


class CacheManager(Generic[T]):
    def __init__(self, model_class: type[T], prefix: str, ttl: int = 600):
        self.model_class = model_class
        self.prefix = prefix
        self.ttl = ttl
        self._lock = asyncio.Lock()

    def _get_key(self, identifier: Any) -> str:
        return f'{self.prefix}:{identifier}'

    async def get_or_set(
        self, r: rediscon, identifier: Any, db_fallback: Callable[[], Awaitable[Any]]
    ) -> T | None:
        """
        Busca no Redis. Se não achar, usa a função db_fallback para buscar no banco,
        salva no Redis e retorna o objeto tipado.
        """
        cache_key = self._get_key(identifier)

        try:
            cached_data = await r.get(cache_key)
            if cached_data:
                return self.model_class.model_validate_json(cached_data)
        except RedisError as e:
            logging.error(f'[Cache] Erro de leitura no Redis ({cache_key}): {e}')
            cached_data = None

        async with self._lock:
            if not cached_data:
                try:
                    cached_data = await r.get(cache_key)
                    if cached_data:
                        return self.model_class.model_validate_json(cached_data)
                except RedisError:
                    pass

            db_obj = await db_fallback()

            if db_obj:
                schema_obj = self.model_class.model_validate(db_obj)

                try:
                    await r.set(cache_key, schema_obj.model_dump_json(), ex=self.ttl)
                except RedisError as e:
                    logging.error(
                        f'[Cache] Erro de escrita no Redis ({cache_key}): {e}'
                    )

                return schema_obj

        return None

    async def delete_cache(self, r: rediscon, identifier: Any):
        cache_key = self._get_key(identifier)
        try:
            user_cached = await r.exists(cache_key)
            if not user_cached:
                return None

            await r.delete(cache_key)
            return 'Cache deletado!'
        except RedisError as e:
            logging.error(f'[Cache] Erro ao deletar cache no Redis ({cache_key}): {e}')
