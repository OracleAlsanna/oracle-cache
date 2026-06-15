import redis

_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    return _client


def is_redis_available() -> bool:
    try:
        _get_client().ping()
        return True
    except Exception:
        return False


def get_cached_url(code: str) -> str | None:
    try:
        return _get_client().get(f"url:{code}")
    except Exception:
        return None


def set_cached_url(code: str, url: str, ttl: int = 3600) -> None:
    try:
        _get_client().setex(f"url:{code}", ttl, url)
    except Exception:
        pass


def delete_cached_url(code: str) -> None:
    try:
        _get_client().delete(f"url:{code}")
    except Exception:
        pass
