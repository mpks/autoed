#!/usr/bin/env python3
"""Module used to test the entire autoed processing pipeline"""
import shutil
import subprocess
import autoed
from autoed.constants import trigger_file
import pytest
import time
import os


@pytest.fixture(scope='session')
def autoed_setup():
    """Run autoed and start watching the data directory"""

    test_path = os.path.dirname(autoed.__path__[0])
    test_path = os.path.join(test_path, 'test/')
    watch_path = os.path.join(test_path, 'data')

    run("autoed start")
    print('Running autoed')
    run2(f"autoed --inotify -t 0.1 --dummy watch {watch_path}")
    time.sleep(0.5)

    yield

    run('autoed stop')


def test_text_01_dataset(autoed_setup):
    d = get_files('text_01')
    run_for_dataset(d, 'TEXT 01')


def test_text_02_dataset(autoed_setup: None):
    d = get_files('text_02')
    run_for_dataset(d, 'TEXT 02')


def test_json_01_dataset(autoed_setup: None):
    d = get_files('json_01')
    run_for_dataset(d, 'JSON 01')


def run_for_dataset(dataset, name):

    print()
    print(f"Running test for the {name} dataset")
    print('------------------------------------')

    d = dataset

    remove_generated_files(d)

    shutil.copy2(d.data_origin, d.data_dest)
    shutil.copy2(d.master_origin,  d.master_dest)

    run(f"touch {d.trigger_file}")
    time.sleep(5)

    print("Nexus file exists:")
    assert os.path.exists(d.nxs_file)
    print("OK")
    print("Autoed log exists:")
    assert os.path.exists(d.autoed_log)
    print("OK")
    print("Slurm files exist: ")
    print("  'default': ", end='')
    assert os.path.exists(d.slurm_file['default'])
    print('OK')
    print("  'user': ", end='')
    assert os.path.exists(d.slurm_file['user'])
    print('OK')
    print("  'ice': ", end='')
    assert os.path.exists(d.slurm_file['ice'])
    print('OK')
    print("  'max_lattices': ", end='')
    assert os.path.exists(d.slurm_file['max_lattices'])
    print('OK')
    print("  'real_space_indexing': ", end='')
    assert os.path.exists(d.slurm_file['real_space_indexing'])
    print('OK')

#    assert check_for_slurm_command(d.autoed_log)
#    print("Slurm run: OK")

    remove_generated_files(d)


def run2(cmd):
    subprocess.Popen(cmd, shell=True)


def run(cmd):
    subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)


def remove_generated_files(dataset):

    d = dataset
    for file in [d.nxs_file, d.autoed_log, d.data_dest, d.master_dest,
                 d.nexus_log, d.phil_file, d.trigger_file,
                 *d.slurm_file.values()]:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass


def get_files(dir_name):
    """
    Return a simple class containing all the filenames in the test data
    directory `dir_name`
    """

    class Simple:
        pass

    a = Simple()
    path = os.path.dirname(autoed.__path__[0])
    path = os.path.join(path, 'test/')
    join = os.path.join
    dest_path = join(path, f"data/ED/{dir_name}")
    processed_path = join(path, f"data/processed/{dir_name}")

    a.data_origin = join(path, 'data/ED/data/sample_data_000001.h5')
    a.master_origin = join(path, 'data/ED/data/sample_master.h5')

    a.data_dest = join(dest_path, 'sample_data_000001.h5')
    a.master_dest = join(dest_path, 'sample_master.h5')
    a.nxs_file = join(dest_path, 'sample.nxs')
    a.autoed_log = join(dest_path, 'sample.autoed.log')
    a.patch_file = join(dest_path, 'PatchMaster.sh')
    a.trigger_file = join(dest_path, f"{trigger_file}")
    a.nexus_log = join(dest_path, 'EDnxs.log')
    a.phil_file = join(dest_path, 'ED_Singla.phil')
    a.log_file = join(dest_path, 'sample.log')
    a.mdoc_file = join(dest_path, 'sample.mrc.mdoc')
    a.slurm_file = {}

    pp = processed_path
    a.slurm_file['default'] = join(pp, "default/slurm_config.json")
    a.slurm_file['user'] = join(pp, "user/slurm_config.json")
    a.slurm_file['ice'] = join(pp, "ice/slurm_config.json")
    rs_path = "real_space_indexing/slurm_config.json"
    a.slurm_file['real_space_indexing'] = join(pp, rs_path)
    a.slurm_file['max_lattices'] = join(pp, "max_lattices/slurm_config.json")

    return a


def check_for_slurm_command(file_path):
    """Check if log file has no errors and it ends with slurm submission"""
    with open(file_path, 'r') as file:
        for line in file:
            if 'Slurm command:' in line:
                return True
    return False
