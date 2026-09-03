"""A FastAPI port of the Flask-Caching extension, backed by cachelib."""
import functools
import hashlib
import uuid

import cachelib
from starlette.responses import Response

# Flask-Caching 1.x style names mapped to the cachelib classes.
CACHE_TYPES = {
    'null': 'NullCache',
    'simple': 'SimpleCache',
    'filesystem': 'FileSystemCache',
    'redis': 'RedisCache',
    'memcached': 'MemcachedCache',
    'uwsgi': 'UWSGICache',
}

_RESPONSE = '_cached_response'


def _dump(value):
    """Turn a response into a value that can be stored in the cache."""
    if isinstance(value, Response):
        return (_RESPONSE, value.body, value.status_code, value.media_type)
    return value


def _load(value):
    """Rebuild a response stored with _dump()."""
    if isinstance(value, tuple) and len(value) == 4 and value[0] == _RESPONSE:
        return Response(content=value[1], status_code=value[2], media_type=value[3])
    return value


class Cache:
    """The cache object, providing the ``cached`` and ``memoize`` decorators."""

    def __init__(self, app):
        config = app.state.config
        cache_type = config.get('CACHE_TYPE', 'SimpleCache')
        cache_class = getattr(cachelib, CACHE_TYPES.get(cache_type, cache_type))
        self.cache = cache_class(default_timeout=config.get('CACHE_DEFAULT_TIMEOUT', 300))
        app.state.cache = self

    # cache API
    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value, timeout=None):
        return self.cache.set(key, value, timeout=timeout)

    def delete(self, key):
        return self.cache.delete(key)

    def clear(self):
        return self.cache.clear()

    def make_cache_key(self, request, key_prefix, query_string):
        if query_string:
            args = tuple(sorted(request.query_params.multi_items()))
            digest = hashlib.md5(str(args).encode()).hexdigest()
            return request.url.path + digest
        if '%s' in key_prefix:
            return key_prefix % request.url.path
        return key_prefix

    def cached(self, timeout=None, key_prefix='view/%s', query_string=False):
        """Cache the return value of a view function."""
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                request = kwargs.get('request')
                key = self.make_cache_key(request, key_prefix, query_string)
                cached_value = self.cache.get(key)
                if cached_value is not None:
                    return _load(cached_value)
                rv = f(*args, **kwargs)
                self.cache.set(key, _dump(rv), timeout=timeout)
                return rv

            wrapper.uncached = f
            wrapper.cache_timeout = timeout
            return wrapper
        return decorator

    def _memoize_version(self, name):
        version_key = f'memoize-version/{name}'
        version = self.cache.get(version_key)
        if version is None:
            version = uuid.uuid4().hex
            self.cache.set(version_key, version, timeout=0)
        return version

    def _memoize_key(self, f, args, kwargs):
        name = f'{f.__module__}.{f.__qualname__}'
        version = self._memoize_version(name)
        payload = f'{name}{args}{sorted(kwargs.items())}{version}'
        return hashlib.md5(payload.encode()).hexdigest()

    def memoize(self, timeout=None):
        """Cache the return value of a function, per set of arguments."""
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                key = self._memoize_key(f, args, kwargs)
                rv = self.cache.get(key)
                if rv is None:
                    rv = f(*args, **kwargs)
                    self.cache.set(key, rv, timeout=timeout)
                return rv

            wrapper.uncached = f
            return wrapper
        return decorator

    def delete_memoized(self, f):
        """Drop every cached value of a memoized function."""
        self.cache.delete(f'memoize-version/{f.__module__}.{f.__qualname__}')
