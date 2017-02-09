from __future__ import print_function

import codecs
import os
import re
from setuptools import setup


def read(filename):
    """Read and return `filename` in root dir of project and return string"""
    here = os.path.abspath(os.path.dirname(__file__))
    return codecs.open(os.path.join(here, filename), 'r').read()

version = "0.0.7"

install_requires = read("requirements.txt").split()
long_description = read('README.rst')

setup(
    name='cloudmesh-piazza',
    version=version,
    url='https://github.com/cloudmesh/piazza',
    license='Apache 2.0',
    author='Gregor von Laszewski, Tim Whitson',
    author_email='laszewski@gmail.com',
    install_requires=install_requires,
    description="Command line client for Piazza",
    long_description=long_description,
    packages=['cloudmesh.piazza'],
    package_data = {
        'cloudmesh.piazza': [
            'includes/*',
            'templates/*'
    ]},    
    platforms='any',
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
    entry_points={
        'console_scripts': [
            'piazza = cloudmesh.piazza.piazza:main',
        ],
    },
    namespace_packages=['cloudmesh']    
)
