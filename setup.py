#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='autoed',
    version='0.0.1',
    entry_points={
        'console_scripts': [
            'autoed_watch = autoed.watch:main',
            'autoed = autoed.autoed:main'
        ]
    },
    setup_requires=['argcomplete'],
    packages=find_packages(),
    install_requires=[
        'watchdog',
        'numpy>=1.26.0',
        'nexgen',
        'h5py>=3.10.0',
        'argparse',
        'python-daemon',
        'pathlib',
        'argcomplete'
    ]
)
