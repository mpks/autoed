#!/usr/bin/env python3
# import shutil
import subprocess
from autoed.constants import trigger_file
import pytest
# import threading
import time
import os


@pytest.fixture(scope='session')
def autoed_setup():
    """Run autoed and start watching the data directory"""

    test_path = os.getcwd()
    watch_path = os.path.join(test_path, 'data')

    run("autoed start")
    run2(f"autoed -i -t 0.1 watch {watch_path}")
    time.sleep(0.2)

    yield

    run('autoed stop')


def test_new_dataset(autoed_setup):

    print('Running the test for new dataset')
    test_path = os.getcwd()
    trigger = os.path.join(test_path, f"data/ED/sweep_json/{trigger_file}")
    run(f"touch {trigger}")
    time.sleep(5)


def test_old_dataset(autoed_setup):

    print("Testing old setup")


def run2(cmd):
    subprocess.Popen(cmd, shell=True)


def run(cmd):
    subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
