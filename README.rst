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


    def etag_generator(request):
        return 'ETag!!'


    @cache_page(cache_timeout=600)
    @etag(etag_generator)
    def view(request):
        pass

Installation
------------

.. code-block:: bash

    pip install --upgrade django-cache
