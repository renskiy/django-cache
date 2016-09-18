import contextlib
import time

from django.core.cache.backends.dummy import DummyCache
from django.middleware import cache as cache_middleware
from django.utils import http, cache, decorators

__all__ = ['cache_page']

dummy_cache = DummyCache('dummy_host', {})

# https://tools.ietf.org/html/rfc7232#section-4.1
rfc7232_headers = ['ETag', 'Vary', 'Cache-Control', 'Expires', 'Content-Location']


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


def get_cache_max_age(cache_control):
    if not cache_control:
        return
    cache_control_kwargs = dict(
        cache._to_tuple(attr)
        for attr in
        cache.cc_delim_re.split(cache_control)
    )
    if 'max-age' in cache_control_kwargs:
        try:
            return int(cache_control_kwargs['max-age'])
        except (ValueError, TypeError):
            pass


def get_conditional_response(request, response=None):
    if not (response and hasattr(cache, 'get_conditional_response')):
        return response
    last_modified = response.get('Last-Modified')
    conditional_response = cache.get_conditional_response(
        request,
        last_modified=http.parse_http_date_safe(last_modified),
        response=response,
    )
    if conditional_response is response:
        return response
    headers = {
        header: response[header]
        for header in rfc7232_headers
        if header in response
    }
    for header, value in headers.items():
        conditional_response[header] = value
    if last_modified:
        conditional_response['Last-Modified'] = last_modified
    return conditional_response


class ResponseCacheUpdater(object):

    def __init__(self, middleware, request, response):
        self.middleware = middleware
        self.request = request
        self.response = response

    def close(self):
        middleware = self.middleware
        request = self.request
        response = self.response
        self.request = self.response = self.middleware = None
        with patch(response, '_closable_objects', []):
            # do not save _closable_objects to cache

            self.update_cache(middleware, request, response)

    @staticmethod
    def update_cache(middleware, request, response):
        cache_timeout = getattr(request, '_cache_timeout', None)
        key_prefix = getattr(request, '_cache_key_prefix', None)
        with patch(cache_middleware, 'patch_response_headers', lambda *_: None):
            # we do not want patch response again

            with patch(middleware, 'key_prefix', key_prefix):
                with patch(middleware, 'cache_timeout', cache_timeout):
                    super(CacheMiddleware, middleware).process_response(
                        request, response,
                    )


class CacheMiddleware(cache_middleware.CacheMiddleware):
    """
    Despite of the original one this middleware supports
    callable 'key_prefix' and 'cache_timeout'
    """

    CONDITIONAL_VARY_HEADERS = {
        'HTTP_IF_NONE_MATCH': 'If-None-Match',
        'HTTP_IF_MATCH': 'If-Match',
    }

    def __init__(self, *args, **kwargs):
        super(CacheMiddleware, self).__init__(*args, **kwargs)
        if callable(self.key_prefix):
            self.get_key_prefix = self.key_prefix
        if callable(self.cache_timeout):
            self.get_cache_timeout = self.cache_timeout

    def get_cache_timeout(self, request, *args, **kwargs):
        return self.cache_timeout

    def get_key_prefix(self, request, *args, **kwargs):
        return self.key_prefix

    def process_request(self, request):
        if request.method not in ('GET', 'HEAD'):
            return None

        cache_max_age = get_cache_max_age(request.META.get('HTTP_CACHE_CONTROL'))
        if cache_max_age == 0:
            request._cache_update_cache = True
            return None

        request._cache_key_prefix = key_prefix = self.get_key_prefix(
            request,
            *request.resolver_match.args,
            **request.resolver_match.kwargs
        )

        with patch(self, 'key_prefix', key_prefix):
            response = super(CacheMiddleware, self).process_request(request)

        # check if we should return "304 Not Modified"
        response = response and get_conditional_response(request, response)

        # setting cache age
        if response and 'Expires' in response:
            max_age = get_cache_max_age(response.get('Cache-Control'))
            if max_age:
                expires = http.parse_http_date(response['Expires'])
                timeout = expires - int(time.time())
                response['Age'] = max_age - timeout

        return response

    def process_response(self, request, response):
        if not self._should_update_cache(request, response):
            return super(CacheMiddleware, self).process_response(request, response)

        last_modified = 'Last-Modified' in response
        etag = 'ETag' in response

        request._cache_timeout = cache_timeout = self.get_cache_timeout(
            request,
            *request.resolver_match.args,
            **request.resolver_match.kwargs
        )

        conditional_vary_headers = [
            http_header
            for wsgi_header, http_header in self.CONDITIONAL_VARY_HEADERS.items()
            if wsgi_header in request.META
        ]
        if conditional_vary_headers:
            cache.patch_vary_headers(response, conditional_vary_headers)

        if response.status_code == 304:  # Not Modified
            cache.patch_response_headers(response, cache_timeout)
        else:
            update_response_cache = ResponseCacheUpdater(
                middleware=self,
                request=request,
                response=response,
            )
            response._closable_objects.append(update_response_cache)

            with patch(cache_middleware, 'learn_cache_key', lambda *_, **__: ''):
                # replace learn_cache_key with dummy one

                with patch(self, 'cache', dummy_cache):
                    # use dummy_cache to postpone cache update till the time
                    # when all values of Vary header are ready,
                    # see https://code.djangoproject.com/ticket/15855

                    with patch(self, 'cache_timeout', cache_timeout):
                        response = super(CacheMiddleware, self).process_response(request, response)

        if not last_modified:
            # patch_response_headers sets its own Last-Modified, remove it
            del response['Last-Modified']
        if not etag:
            # patch_response_headers sets its own ETag, remove it
            del response['ETag']

        return response
