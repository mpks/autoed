#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='autoed',
    version='0.0.3',
    entry_points={
        'console_scripts': [
            'autoed_watch = autoed.watch:main',
            'autoed = autoed.autoed:main',
            'autoed_beam_center = autoed.beam_center:main'
        ]
    },
    setup_requires=['argcomplete'],
    packages=find_packages(),
    package_data={'autoed': ['data/*']},
    install_requires=[
        'watchdog',
        'numpy>=1.10.0',
        'nexgen',
        'h5py',
        'argparse',
        'python-daemon',
        'pathlib',
        'argcomplete',
        'psutil'
    ]
)
