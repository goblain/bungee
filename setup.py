from setuptools import setup

setup(
    name     = 'bungee',
    packages = ['bungee',],
    version  = '0.1',
    description = 'templating and environment management for kubernetes',
    license  = 'MIT',
    scripts  = ['bin/bungee',],
    author   = 'Radek Goblin Pieczonka',
    author_email = 'goblin@pentex.pl',
    url = 'https://github.com/goblain/bungee',
    download_url = 'https://github.com/goblain/bungee/tarball/0.1',
    keywords = ['kubernetes', 'templates', 'environment'],
    classifiers = []
)
