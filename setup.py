#!/usr/bin/env python
from setuptools import setup

from CanvasSync._version import __version__

readme = open('README.md').read()
requirements = list(filter(None, open("requirements.txt").read().split("\n")))


setup(
    name='CanvasSync',
    version=__version__,
    description='Synchronizes modules, assignments and files from a '
                'Canvas server to a local folder',
    long_description=readme,
    author='Mathias Perslev',
    author_email='mathias@perslev.com',
    url='https://github.com/perslev/CanvasSync',
    license="LICENSE.txt",
    package_dir={'CanvasSync': 'CanvasSync'},
    entry_points={
        'console_scripts': [
            'canvas=CanvasSync.__main__:main',
        ],
    },
    install_requires=requirements,
    classifiers=['Development Status :: 3 - Alpha',
                'Environment :: Console',
                'Operating System :: MacOS :: MacOS X',
                'Operating System :: POSIX',
                'Programming Language :: Python',
                'License :: OSI Approved :: MIT License']
)
