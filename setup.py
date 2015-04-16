"""
BusyBody
--------------

A library for enriching user data using the FullContact API.
"""
from setuptools import setup

with open('README.md', 'r') as inf:
    long_description = inf.read()

setup(
    name='busybody',
    version='0.0.1',
    description='Tools for managing and enriching user data with the FullContact API',
    long_description=long_description,
    url='https://github.com/bmd/busybody',
    author='Brendan Maione-Downing',
    author_email='b.maionedowning@gmail.com',
    license='MIT',
    packages=['busybody'],
    zip_safe=False,
    platforms='any',
    include_package_data=True,
    install_requires=['tortilla', 'peewee', 'unicodecsv', 'pyyaml'],
    tests_require=['nose>=1.0'],
    test_suite='nose.collector',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
