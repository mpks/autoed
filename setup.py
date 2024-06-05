#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='autoed',
    version='0.1.4',
    entry_points={
        'console_scripts': [
            'autoed_watch = autoed.watch:main',
            'autoed = autoed.autoed:main',
            'autoed_beam_center = autoed.beam_position.beam_center:main',
            'autoed_process = autoed.process.process_static:main'
        ]
    },
    setup_requires=['argcomplete'],
    packages=find_packages(),
    package_data={'autoed': ['data/*']},
    install_requires=[
        'watchdog',
        'numpy>=1.10.0',
        'nexgen>=0.8.5',
        'h5py',
        'argparse',
        'python-daemon',
        'pathlib',
        'argcomplete',
        'psutil'
    ]
)
