#!/usr/bin/env python

"""
Setup script for greencandle - a trading bot
"""

import pip
from setuptools import setup, find_packages

REQUIRES = []
LINKS = []

REQUIREMENTS = pip.req.parse_requirements(
    'requirements.txt', session=pip.download.PipSession())

exec(open('greencandle/version.py').read())

for item in REQUIREMENTS:
    # we want to handle package names and also repo urls
    if getattr(item, 'url', None):  # older pip has url
        LINKS.append(str(item.url))
    if getattr(item, 'link', None): # newer pip has link
        LINKS.append(str(item.link))
    if item.req:
        REQUIRES.append(str(item.req))

setup(
    name='greencandle',
    packages=find_packages(),
    version=__version__,
    description='a trading bot for binance and coinbase',
    author='Amro Diab',
    author_email='adiab@linuxmail.org',
    url='https://github.com/adiabuk/greencandle',
    install_requires=REQUIRES,
    dependency_links=LINKS,
    entry_points={'console_scripts':['backend=greencandle.backend:main',
                                     'test_backend=greencandle.test_backend:main',
                                     'average_down=greencandle.scripts.average_down:main',
                                     'balances=greencandle.scripts.balances:main',
                                     'get_details=greencandle.scripts.get_details:main',
                                     'get_file=greencandle.scripts.get_file:main',
                                     'get_mysql_status=greencandle.scripts.get_mysql_status:main',
                                     'get_order_status=greencandle.scripts.get_order_status:main',
                                     'get_recent_profit=greencandle.scripts.get_recent_profit:main',
                                     'get_totals_csv=greencandle.scripts.get_totals_csv:main',
                                     'green_top=greencandle.scripts.green_top:main',
                                     'investment=greencandle.scripts.investment:main',
                                     'pip_value=greencandle.scripts.pip_value:main',
                                     'sell_1p=greencandle.scripts.sell_1p:main',
                                     'sell_now=greencandle.scripts.sell_now:main',
                                     'create_graph=greencandle.scripts.create_graph:main',
                                     'create_test_data=greencandle.scripts.create_test_data:main']},
    classifiers=[],
)
