import subprocess
import os
import re
import time
import logging

from .misc_functions import electron_wavelength, scrap


def generate_nexus_file(dataset):
    """Generates Nexus file from the dataset files using nexgen"""

    phil_file = os.path.join(dataset.path, 'ED_Singla.phil')

    if not os.path.exists(phil_file):
        cmd = ['nexgen_phil get ED_Singla.phil -o ' + phil_file]
        subprocess.run(cmd, shell=True, text=True, capture_output=True)
    # We have to wait for the ED_Singla.phil to be created
    # Oterwise the nexgen processing will fail
    time.sleep(1)     # do not delete

    voltage_kev = float(scrap(dataset.mdoc_file, 'Voltage'))
    wavelength = electron_wavelength(voltage_kev)

    speed_param = float(scrap(dataset.log_file, 'speed parameter'))
    speed_line = scrap(dataset.log_file, 'rotationSpeed')
    pattern = r'^(.*)\*(.*)\+(.*)\*10\^(.*)$'
    params = re.search(pattern, speed_line)
    rotation_speed = float(params.group(1)) * speed_param
    rotation_speed += (float(params.group(3)) *
                       10**(float(params.group(4))))

    start_angle = float(scrap(dataset.log_file, 'start angle'))
    frame_rate = float(scrap(dataset.log_file, 'frame rate'))
    rotation_angle = rotation_speed / frame_rate

    data_file_pattern = dataset.base + r'.__data_*.h5'

    nex_cmd = 'ED_nexus singla '
    nex_cmd += '%s ' % phil_file
    nex_cmd += r'input.datafiles=%s ' % data_file_pattern
    nex_cmd += 'goniometer.starts=%.0f,0,0,0 ' % start_angle
    nex_cmd += 'goniometer.increments=%.5f,0,0,0 ' % rotation_angle
    nex_cmd += 'goniometer.vectors=0,-1,0,0,0,1,0,1,0,1,0,0 '
    nex_cmd += 'detector.starts=809 '
    nex_cmd += 'beam.wavelength=%.10f ' % wavelength
    nex_cmd += '-m %s ' % dataset.master_file

    # Remove EDnxs.log if it exists
    EDnxs_file = os.path.join(dataset.path, 'EDnxs.log')
    if os.path.exists(EDnxs_file):
        os.remove(EDnxs_file)

    dataset.logger.info('Running nexgen with: ' + nex_cmd)
    p = subprocess.run(nex_cmd, shell=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, cwd=dataset.path)
    if p.stderr:
        msg = 'Failed to process data with nexgen'
        dataset.logger.error(msg)
        dataset.logger.error(p.stderr)
        dataset.status = 'CONVERSION_FAILED'
        return 0
    else:
        dataset.logger.info('Created Nexus file ' + dataset.nexgen_file)
        dataset.status = 'CONVERTED'
        return 1
