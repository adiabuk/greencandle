#!/usr/bin/env python
#pylint: disable=exec-used,undefined-variable

"""
Setup script for greencandle - a trading bot
"""

import glob
from collections import defaultdict
import pip
from setuptools import setup, find_packages

exec(open('greencandle/version.py').read())

def get_entrypoints():
    """
    get python entrypoints
    """

    entrypoints = []
    files = glob.glob('greencandle/scripts/[!_]*.py')
    for filename in files:
        path = filename.rstrip('.py').replace('/', '.')
        name = path.split('.')[-1]
        string = "{0}={1}:main".format(name, path)
        entrypoints.append(string)
    return entrypoints

def get_shell_scripts():
    """get list of shell scripts in module"""
    return glob.glob('greencandle/scripts/[!_]*[!.py]')

def get_reqs(req):
    """get requirements and links from requirements.txt"""
    results = defaultdict(list)
    requirements = pip.req.parse_requirements(
        'requirements.txt', session=pip.download.PipSession())

    for item in requirements:
        # we want to handle package names and also repo urls
        if getattr(item, 'url', None):  # older pip has url
            results['link'].append(str(item.url))
        if getattr(item, 'link', None): # newer pip has link
            results['link'].append(str(item.link))
        if item.req:
            results['requires'].append(str(item.req))
    return results[req]

setup(
    name='greencandle',
    packages=find_packages(),
    version=__version__,
    description='a trading bot for binance and coinbase',
    author='Amro Diab',
    author_email='adiab@linuxmail.org',
    url='https://github.com/adiabuk/greencandle',
    install_requires=get_reqs('requires'),
    dependency_links=get_reqs('link'),
    scripts=get_shell_scripts(),
    entry_points={'console_scripts': get_entrypoints()},
    classifiers=[],
)
