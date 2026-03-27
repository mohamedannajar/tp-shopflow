import os
import logging
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def _create_redis_client():
    try:
        import redis
        client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2
        )
        client.ping()
        logger.info(f"Redis connecté : {REDIS_URL}")
        return client
    except Exception as e:
        logger.warning(f"Redis indisponible ({e}) — MagicMock activé")
        return MagicMock()


redis_client = _create_redis_client()


def get_cached(key: str):
    value = redis_client.get(key)

    if isinstance(value, MagicMock):
        return None

    if value is None:
        return None

    if not isinstance(value, (str, bytes, bytearray)):
        return None

    return value


def set_cached(key: str, value: str, ttl: int = 300):
    try:
        return redis_client.set(key, value, ex=ttl)
    except Exception:
        return None


def delete_cached(key: str):
    try:
        return redis_client.delete(key)
    except Exception:
        return None