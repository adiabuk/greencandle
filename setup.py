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

for item in REQUIREMENTS:
    # we want to handle package names and also repo urls
    if getattr(item, 'url', None):  # older pip has url
        LINKS.append(str(item.url))
    if getattr(item, 'link', None): # newer pip has link
        LINKS.append(str(item.link))
    if item.req:
        REQUIRES.append(str(item.req))

VER = '0.02'

setup(
    name='greencandle',
    packages=find_packages(),
    version=VER,
    description='a trading bot for binance and coinbase',
    author='Amro Diab',
    author_email='adiab@linuxmail.org',
    url='https://github.com/adiabuk/greencandle',
    install_requires=REQUIRES,
    dependency_links=LINKS,
    entry_points={'console_scripts':['backend=greencandle.backend:main',
                                     'pdfcheck=pdfgrep.pdfcheck:main']},
    classifiers=[],
)
