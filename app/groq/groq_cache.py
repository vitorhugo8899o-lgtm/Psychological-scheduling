import hashlib

from app.api.v1.dependencies import rediscon


def generate_cache_key(message: str) -> str:
    return hashlib.md5(message.strip().encode('utf-8')).hexdigest()


async def create_cache_response(ask: str, response: str, r: rediscon):
    cache_key = generate_cache_key(ask)
    await r.set(cache_key, response, ex=1800)
    return response


async def cache_respost(message: str, r: rediscon):
    cache_key = generate_cache_key(message)
    cache_ai = await r.get(cache_key)

    if cache_ai:
        if isinstance(cache_ai, bytes):
            return cache_ai.decode('utf-8')
        return cache_ai

    return None
