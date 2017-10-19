============
Django-cache
============

Enhanced :code:`cache_page` decorator for `Django`_ views.

.. _Django: https://www.djangoproject.com

.. image:: https://travis-ci.org/renskiy/django-cache.svg?branch=master
    :target: https://travis-ci.org/renskiy/django-cache
.. image:: https://coveralls.io/repos/github/renskiy/django-cache/badge.svg?branch=master
    :target: https://coveralls.io/github/renskiy/django-cache?branch=master

Compatibility
-------------

Django-cache properly works with Django 1.8, 1.9, 1.10 and 1.11 on Python 2.7, 3.4, 3.5 and 3.6.

Advantages
----------

* fixed certain amount of bugs (including `#15855`_)
* support of callable :code:`cache_timeout` and :code:`key_prefix` parameters
* cache age can be limited by client (min cache age is manageable, default is 0)

.. _#15855: https://code.djangoproject.com/ticket/15855

Usage
-----

.. code-block:: python

    from djangocache import cache_page

    @cache_page(cache_timeout=600)
    def view(request):
        pass

Combination with :code:`last_modified` and/or :code:`etag` view decorators
--------------------------------------------------------------------------

If you planning to use :code:`cache_page` among with :code:`last_modified` and/or :code:`etag` the latter must be placed after :code:`cache_page`:

.. code-block:: python

    from djangocache import cache_page
    from django.views.decorators.http import last_modified, etag

    def etag_generator(request, *args, **kwargs):
        return 'ETag!!'

    @cache_page(cache_timeout=600)
    @etag(etag_generator)
    def view(request, *args, **kwargs):
        pass

Django Settings
---------------

``DJANGOCACHE_MIN_AGE`` - used to set minimal age of cache. Default is 0, meaning that client can ask server to skip cache by providing header ``Cache-Control: max-age=0``.

``@cache_page`` params
----------------------

* ``cache_timeout``. Default is ``settings.CACHE_MIDDLEWARE_SECONDS``.
* ``key_prefix``. Default is ``settings.CACHE_MIDDLEWARE_KEY_PREFIX``.
* ``cache_alias``. Default is ``settings.CACHE_MIDDLEWARE_ALIAS``, or ``settings.DEFAULT_CACHE_ALIAS`` if set to ``None``.
* ``cache_min_age``. Default is ``settings.DJANGOCACHE_MIN_AGE``.

Installation
------------

.. code-block:: bash

    pip install --upgrade django-cache
