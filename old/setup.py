import io, os

from setuptools import setup

version = '0.0.1'

setup(
    name = 'piazza-miner',
    version = version,
    description='Command Line Data Miner for Piazza',
    author = 'Tim Whitson, Gary Bean',
    author_email = 'tdwhitso@indiana.edu',
    url = 'https://gitlab.com/cloudmesh_fall2016/project-004',
    long_description = io.open('README.rst').read().split(),
    install_requires = io.open('requirements.txt').read().split(),
    packages = ['piazza_miner'],
    package_data = {
        'piazza_miner': [
            'includes/*',
            'static/*',
            'templates/*'
    ]},
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        "License :: OSI Approved :: MIT License",
        'Operating System :: OS Independent',
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points = {
        'console_scripts': [
            'piazza = piazza_miner.piazza:main',
        ],
    }
)
