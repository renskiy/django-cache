from distutils.core import setup

with open('README.rst') as description:
    long_description = description.read()

setup(
    name='django-cache',
    version='0.2.5',
    author='Rinat Khabibiev',
    author_email='srenskiy@gmail.com',
    py_modules=['djangocache'],
    url='https://github.com/renskiy/django-cache',
    license='MIT',
    description='Extended HTTP-caching for Django',
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Operating System :: OS Independent',
        'Environment :: Web Environment',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
