"""
Shared HTTP session with retry logic and TTL cache for SerpAPI calls.
All agents use cached_get() instead of raw requests.get().
"""
import hashlib
import json
import logging
import time
from threading import Lock

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

_session: requests.Session | None = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
    return _session


class TTLCache:
    """Thread-safe in-memory cache with time-to-live expiry."""

    def __init__(self, ttl_seconds: int = 1800, maxsize: int = 100):
        self._cache: dict = {}
        self._timestamps: dict = {}
        self._ttl = ttl_seconds
        self._maxsize = maxsize
        self._lock = Lock()

    def get(self, key: str):
        with self._lock:
            if key in self._cache:
                if time.time() - self._timestamps[key] < self._ttl:
                    return self._cache[key]
                del self._cache[key]
                del self._timestamps[key]
            return None

    def set(self, key: str, value) -> None:
        with self._lock:
            if len(self._cache) >= self._maxsize:
                oldest = min(self._timestamps, key=self._timestamps.get)
                self._cache.pop(oldest, None)
                self._timestamps.pop(oldest, None)
            self._cache[key] = value
            self._timestamps[key] = time.time()


_cache = TTLCache(ttl_seconds=1800, maxsize=100)


def cached_get(url: str, params: dict, timeout: int = 10) -> dict:
    """
    GET request with:
    - Automatic retry (3x) on 429/5xx with exponential backoff
    - 30-minute TTL cache keyed on URL + params
    """
    cache_key = hashlib.md5(
        json.dumps({"url": url, "params": params}, sort_keys=True).encode()
    ).hexdigest()

    cached = _cache.get(cache_key)
    if cached is not None:
        logger.info("Cache hit for query: %s", params.get("q", ""))
        return cached

    response = get_session().get(url, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    _cache.set(cache_key, data)
    return data
