import time

from datetime import datetime

import mock

from django import test, http
from django.conf import settings, urls
from django.core.cache import caches
from django.core.urlresolvers import reverse
from django.views.decorators.http import last_modified, etag

from djangocache import cache_page

mocked_response = mock.Mock(side_effect=lambda: http.HttpResponse())


@cache_page(cache_timeout=24 * 60 * 60)
def static(request):
    return mocked_response()


@cache_page()
def default(request):
    return mocked_response()


def no_cache(request):
    return mocked_response()


# Mon, 17 Jul 2016 09:55:00 GMT
@last_modified(lambda r: datetime.utcfromtimestamp(1468749300))
@cache_page(cache_timeout=24 * 60 * 60)
def cache_with_last_modified(request):
    return mocked_response()


@cache_page(cache_timeout=24 * 60 * 60)
# Mon, 17 Jul 2016 09:55:00 GMT
@last_modified(lambda r: datetime.utcfromtimestamp(1468749300))
def cache_with_last_modified2(request):
    return mocked_response()


@etag(lambda r: 'etag')
@cache_page(cache_timeout=24 * 60 * 60)
def cache_with_etag(request):
    return mocked_response()


@cache_page(cache_timeout=24 * 60 * 60)
@etag(lambda r: 'etag')
def cache_with_etag2(request):
    return mocked_response()


@cache_page(key_prefix=lambda r: dynamic_key_prefix.key_prefix)
def dynamic_key_prefix(request):
    return mocked_response()


@cache_page(cache_timeout=lambda r: dynamic_cache_timeout.cache_timeout)
def dynamic_cache_timeout(request):
    return mocked_response()
dynamic_cache_timeout.cache_timeout = 24 * 60 * 60


class UpdateVaryMiddleware(object):

    def process_response(self, request, response):
        response['Vary'] = 'Header'
        return response

urlpatterns = [
    urls.url(r'static', static, name='static'),
    urls.url(r'default', default, name='default'),
    urls.url(r'no_cache', no_cache, name='no_cache'),
    urls.url(r'dynamic_key_prefix', dynamic_key_prefix, name='dynamic_key_prefix'),
    urls.url(r'dynamic_cache_timeout', dynamic_cache_timeout, name='dynamic_cache_timeout'),
    urls.url(r'cache_with_last_modified$', cache_with_last_modified, name='cache_with_last_modified'),
    urls.url(r'cache_with_last_modified2', cache_with_last_modified2, name='cache_with_last_modified2'),
    urls.url(r'cache_with_etag$', cache_with_etag, name='cache_with_etag'),
    urls.url(r'cache_with_etag2', cache_with_etag2, name='cache_with_etag2'),
]


@test.utils.override_settings(ROOT_URLCONF=__name__)
class CachePageTestCase(test.SimpleTestCase):

    def setUp(self):
        dynamic_key_prefix.key_prefix = 'key_prefix'

    def tearDown(self):
        mocked_response.reset_mock()
        caches[settings.CACHE_MIDDLEWARE_ALIAS].clear()

    def test_default(self):
        client = test.Client()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(reverse('default'))
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 10:10:00 GMT', response['Expires'])
            self.assertEqual('max-age=600', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.get(reverse('default'))
            mocked_response.assert_not_called()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 10:10:00 GMT', response['Expires'])
            self.assertEqual('max-age=300', response['Cache-Control'])

    def test_method_post(self):
        client = test.Client()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.post(reverse('default'))
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertNotIn('Expires', response)
            self.assertNotIn('Cache-Control', response)
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.post(reverse('default'))
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertNotIn('Expires', response)
            self.assertNotIn('Cache-Control', response)

    def test_method_head(self):
        client = test.Client()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.head(reverse('default'))
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 10:10:00 GMT', response['Expires'])
            self.assertEqual('max-age=600', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.head(reverse('default'))
            mocked_response.assert_not_called()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 10:10:00 GMT', response['Expires'])
            self.assertEqual('max-age=300', response['Cache-Control'])

    def test_dynamic_cache_timeout(self):
        client = test.Client()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(reverse('dynamic_cache_timeout'))
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86400', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.get(reverse('dynamic_cache_timeout'))
            mocked_response.assert_not_called()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86100', response['Cache-Control'])

    def test_dynamic_key_prefix(self):
        client = test.Client()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(reverse('dynamic_key_prefix'))
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 10:10:00 GMT', response['Expires'])
            self.assertEqual('max-age=600', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.get(reverse('dynamic_key_prefix'))
            mocked_response.assert_not_called()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 10:10:00 GMT', response['Expires'])
            self.assertEqual('max-age=300', response['Cache-Control'])
            mocked_response.reset_mock()

        dynamic_key_prefix.key_prefix = 'another_key_prefix'

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.get(reverse('dynamic_key_prefix'))
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 10:15:00 GMT', response['Expires'])
            self.assertEqual('max-age=600', response['Cache-Control'])
            mocked_response.reset_mock()

    @test.utils.override_settings(MIDDLEWARE_CLASSES=[__name__ + '.UpdateVaryMiddleware'])
    def test_with_vary_changed_by_middleware(self):
        client = test.Client()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(
                reverse('default'),
                HTTP_HEADER='header1',
            )
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Vary', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Header', response['Vary'])
            self.assertEqual('Sun, 17 Jul 2016 10:10:00 GMT', response['Expires'])
            self.assertEqual('max-age=600', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.get(
                reverse('default'),
                HTTP_HEADER='header1',
            )
            mocked_response.assert_not_called()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Vary', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Header', response['Vary'])
            self.assertEqual('Sun, 17 Jul 2016 10:10:00 GMT', response['Expires'])
            self.assertEqual('max-age=300', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.get(
                reverse('default'),
                HTTP_HEADER='header2',
            )
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Vary', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Header', response['Vary'])
            self.assertEqual('Sun, 17 Jul 2016 10:15:00 GMT', response['Expires'])
            self.assertEqual('max-age=600', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.get(
                reverse('default'),
            )
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Vary', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Header', response['Vary'])
            self.assertEqual('Sun, 17 Jul 2016 10:15:00 GMT', response['Expires'])
            self.assertEqual('max-age=600', response['Cache-Control'])

    def test_static(self):
        client = test.Client()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(reverse('static'))
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86400', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.get(reverse('static'))
            mocked_response.assert_not_called()
            self.assertNotIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86100', response['Cache-Control'])

    def test_with_last_modified(self):
        client = test.Client()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(
                reverse('cache_with_last_modified'),
                HTTP_IF_MODIFIED_SINCE='Sun, 17 Jul 2016 09:55:00 GMT',
            )
            mocked_response.assert_not_called()
            self.assertEqual(304, response.status_code)
            self.assertNotIn('ETag', response)
            self.assertIn('Last-Modified', response)
            self.assertNotIn('Expires', response)
            self.assertNotIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 09:55:00 GMT', response['Last-Modified'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(
                reverse('cache_with_last_modified'),
                HTTP_IF_MODIFIED_SINCE='Sun, 17 Jul 2016 09:50:00 GMT',
            )
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 09:55:00 GMT', response['Last-Modified'])
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86400', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.get(
                reverse('cache_with_last_modified'),
                HTTP_IF_MODIFIED_SINCE='Sun, 17 Jul 2016 09:50:00 GMT',
            )
            mocked_response.assert_not_called()
            self.assertNotIn('ETag', response)
            self.assertIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 09:55:00 GMT', response['Last-Modified'])
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86100', response['Cache-Control'])

    def test_with_last_modified2(self):
        client = test.Client()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(
                reverse('cache_with_last_modified2'),
                HTTP_IF_MODIFIED_SINCE='Sun, 17 Jul 2016 09:55:00 GMT',
            )
            mocked_response.assert_not_called()
            self.assertEqual(304, response.status_code)
            self.assertNotIn('ETag', response)
            self.assertIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 09:55:00 GMT', response['Last-Modified'])
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86400', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(
                reverse('cache_with_last_modified2'),
                HTTP_IF_MODIFIED_SINCE='Sun, 17 Jul 2016 09:50:00 GMT',
            )
            mocked_response.assert_called_once()
            self.assertNotIn('ETag', response)
            self.assertIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 09:55:00 GMT', response['Last-Modified'])
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86400', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.get(
                reverse('cache_with_last_modified2'),
                HTTP_IF_MODIFIED_SINCE='Sun, 17 Jul 2016 09:50:00 GMT',
            )
            mocked_response.assert_not_called()
            self.assertNotIn('ETag', response)
            self.assertIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('Sun, 17 Jul 2016 09:55:00 GMT', response['Last-Modified'])
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86100', response['Cache-Control'])

    def test_with_etag(self):
        client = test.Client()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(
                reverse('cache_with_etag'),
                HTTP_IF_NONE_MATCH='etag',
            )
            mocked_response.assert_not_called()
            self.assertEqual(304, response.status_code)
            self.assertIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertNotIn('Expires', response)
            self.assertNotIn('Cache-Control', response)
            self.assertEqual('"etag"', response['ETag'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(
                reverse('cache_with_etag'),
                HTTP_IF_NONE_MATCH='another_etag',
            )
            mocked_response.assert_called_once()
            self.assertIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('"etag"', response['ETag'])
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86400', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.get(
                reverse('cache_with_etag'),
                HTTP_IF_NONE_MATCH='another_etag',
            )
            mocked_response.assert_not_called()
            self.assertIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('"etag"', response['ETag'])
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86100', response['Cache-Control'])

    def test_with_etag2(self):
        client = test.Client()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(
                reverse('cache_with_etag2'),
                HTTP_IF_NONE_MATCH='etag',
            )
            mocked_response.assert_not_called()
            self.assertEqual(304, response.status_code)
            self.assertIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('"etag"', response['ETag'])
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86400', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:00:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749600):
            response = client.get(
                reverse('cache_with_etag2'),
                HTTP_IF_NONE_MATCH='another_etag',
            )
            mocked_response.assert_called_once()
            self.assertIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('"etag"', response['ETag'])
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86400', response['Cache-Control'])
            mocked_response.reset_mock()

        # Mon, 17 Jul 2016 10:05:00 GMT
        with mock.patch.object(time, 'time', return_value=1468749900):
            response = client.get(
                reverse('cache_with_etag2'),
                HTTP_IF_NONE_MATCH='another_etag',
            )
            mocked_response.assert_not_called()
            self.assertIn('ETag', response)
            self.assertNotIn('Last-Modified', response)
            self.assertIn('Expires', response)
            self.assertIn('Cache-Control', response)
            self.assertEqual('"etag"', response['ETag'])
            self.assertEqual('Mon, 18 Jul 2016 10:00:00 GMT', response['Expires'])
            self.assertEqual('max-age=86100', response['Cache-Control'])

    def test_no_cache(self):
        client = test.Client()
        response = client.get(reverse('no_cache'))
        mocked_response.assert_called_once()
        self.assertNotIn('ETag', response)
        self.assertNotIn('Last-Modified', response)
        self.assertNotIn('Expires', response)
        self.assertNotIn('Cache-Control', response)
        mocked_response.reset_mock()

        response = client.get(reverse('no_cache'))
        mocked_response.assert_called_once()
        self.assertNotIn('ETag', response)
        self.assertNotIn('Last-Modified', response)
        self.assertNotIn('Expires', response)
        self.assertNotIn('Cache-Control', response)