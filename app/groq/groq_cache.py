import hashlib
import logging

from redis.exceptions import RedisError

from app.api.v1.dependencies import PROMPT_SYSTEM, rediscon
from app.groq.ai_safety import normalize_message

CACHE_TTL_SECONDS = 1800

PROMPT_VERSION = hashlib.sha256(PROMPT_SYSTEM.encode('utf-8')).hexdigest()[:8]


def generate_cache_key(message: str) -> str:
    normalized = normalize_message(message).lower()
    digest = hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    return f'groq:{PROMPT_VERSION}:{digest}'


async def create_cache_response(ask: str, response: str, r: rediscon):
    try:
        await r.set(generate_cache_key(ask), response, ex=CACHE_TTL_SECONDS)
    except RedisError:
        logging.exception('[IA] Redis indisponível ao gravar o cache')

    return response


async def cache_respost(message: str, r: rediscon):
    try:
        cache_ai = await r.get(generate_cache_key(message))
    except RedisError:
        logging.exception('[IA] Redis indisponível ao ler o cache')
        return None

    if cache_ai:
        if isinstance(cache_ai, bytes):
            return cache_ai.decode('utf-8')
        return cache_ai

    return None
