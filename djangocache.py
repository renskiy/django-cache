import contextlib
import threading
import time

from django.core import signals
from django.core.cache.backends.dummy import DummyCache
from django.middleware import cache as cache_middleware
from django.utils import http, cache, decorators

__all__ = ['cache_page']

response_handle = threading.local()

dummy_cache = DummyCache('dummy_host', {})


def cache_page(**kwargs):
    """
    This decorator is similar to `django.views.decorators.cache.cache_page`
    """
    cache_timeout = kwargs.get('cache_timeout')
    cache_alias = kwargs.get('cache_alias')
    key_prefix = kwargs.get('key_prefix')
    decorator = decorators.decorator_from_middleware_with_args(CacheMiddleware)(
        cache_timeout=cache_timeout,
        cache_alias=cache_alias,
        key_prefix=key_prefix,
    )
    return decorator


@contextlib.contextmanager
def patch(obj, attr, value, default=None):
    original = getattr(obj, attr, default)
    setattr(obj, attr, value)
    yield
    setattr(obj, attr, original)


class CacheMiddleware(cache_middleware.CacheMiddleware):
    """
    Despite of the original one this middleware supports
    callable 'key_prefix' and 'cache_timeout'
    """

    def __init__(self, *args, **kwargs):
        super(CacheMiddleware, self).__init__(*args, **kwargs)
        if callable(self.key_prefix):
            self.get_key_prefix = self.key_prefix
        if callable(self.cache_timeout):
            self.get_cache_timeout = self.cache_timeout
        signals.request_finished.connect(update_response_cache)

    def get_cache_timeout(self, request, *args, **kwargs):
        return self.cache_timeout

    def get_key_prefix(self, request, *args, **kwargs):
        return self.key_prefix

    def process_request(self, request):
        if request.method in ('GET', 'HEAD'):
            response_handle.key_prefix = key_prefix = self.get_key_prefix(
                request,
                *request.resolver_match.args,
                **request.resolver_match.kwargs
            )
        else:
            key_prefix = None
        with patch(self, 'key_prefix', key_prefix):
            response = super(CacheMiddleware, self).process_request(request)

        if response and 'Expires' in response:
            # Replace 'max-age' value of 'Cache-Control' header by one
            # calculated from the 'Expires' header.
            # This is necessary because of FetchFromCacheMiddleware
            # gets 'Cache-Control' header value from the cache
            # where 'max-age' corresponds to the moment of original
            # response generation and thus should have another value
            # for the current time.
            expires = http.parse_http_date(response['Expires'])
            timeout = expires - int(time.time())
            cache.patch_cache_control(response, max_age=timeout)

        return response

    def process_response(self, request, response):
        if not self._should_update_cache(request, response):
            return super(CacheMiddleware, self).process_response(request, response)

        response_handle.response = response
        response_handle.request = request
        response_handle.middleware = self

        response_handle.cache_timeout = cache_timeout = self.get_cache_timeout(
            request,
            *request.resolver_match.args,
            **request.resolver_match.kwargs
        )

        last_modified = 'Last-Modified' in response
        etag = 'ETag' in response

        with patch(cache_middleware, 'learn_cache_key', lambda *_, **__: ''):
            # replace learn_cache_key with dummy one

            with patch(self, 'cache', dummy_cache):
                # use dummy_cache to postpone cache update till the time
                # when all values of Vary header are ready

                with patch(self, 'cache_timeout', cache_timeout):
                    response = super(CacheMiddleware, self).process_response(request, response)

        if not last_modified:
            # UpdateCacheMiddleware sets Last-Modified, remove it
            del response['Last-Modified']
        if not etag:
            # UpdateCacheMiddleware sets ETag, remove it
            del response['ETag']

        return response

    def update_cache(self, request, response, cache_timeout=None, key_prefix=None):
        with patch(cache_middleware, 'patch_response_headers', lambda *_: None):
            # we do not want patch response again

            with patch(self, 'key_prefix', key_prefix):
                with patch(self, 'cache_timeout', cache_timeout):
                    super(CacheMiddleware, self).process_response(request, response)


def update_response_cache(*args, **kwargs):
    middleware = getattr(response_handle, 'middleware', None)
    request = getattr(response_handle, 'request', None)
    response = getattr(response_handle, 'response', None)
    if middleware and request and response:
        try:
            cache_timeout = getattr(response_handle, 'cache_timeout', None)
            key_prefix = getattr(response_handle, 'key_prefix', None)
            CacheMiddleware.update_cache(
                middleware, request, response,
                cache_timeout=cache_timeout,
                key_prefix=key_prefix,
            )
        finally:
            response_handle.__dict__.clear()
