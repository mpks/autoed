#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='autoed',
    version='0.2.2.post2',
    entry_points={
        'console_scripts': [
            'autoed_watch = autoed.watch:main',
            'autoed = autoed.autoed:main',
            'autoed_beam_center = autoed.beam_position.beam_center:main',
            'autoed_process = autoed.process.process_static:main',
            'autoed_server = autoed.server:run',
            'autoed_generate_report = autoed.report.report_generator:run'
        ]
    },
    setup_requires=['argcomplete'],
    packages=find_packages(),
    package_data={'autoed': ['data/*', 'report/template/*']},
    install_requires=[
        'argcomplete',
        'watchdog==4.0.0',
        'numpy',
        'nexgen>=0.8.5',
        'h5py',
        'argparse',
        'python-daemon',
        'pathlib',
        'psutil',
        'attr',
        'hdf5plugin',
        'matplotlib',
        'pydantic',
        'uvicorn',
    ],
    extras_require={
        'server': [
            'fastapi[standard]',
            'pyyaml',
            'python-jose',
            ],
    },
)
