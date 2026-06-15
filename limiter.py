from cache import _get_client


def check_rate_limit(ip: str, endpoint: str, limit: int) -> bool:
    """Returns True if the request is allowed, False if the limit is exceeded."""
    try:
        client = _get_client()
        key = f"rl:{ip}:{endpoint}"
        count = client.incr(key)
        if count == 1:
            client.expire(key, 60)
        return count <= limit
    except Exception:
        return True
