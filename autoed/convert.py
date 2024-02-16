import subprocess
import os
import re
import autoed
import json


from .misc_functions import (
    electron_wavelength, scrap, get_detector_distance,
    is_file_fully_written, overwrite_mask
)


def generate_nexus_file(dataset):
    """Generates Nexus file from the dataset files using nexgen"""

    dataset.logger.info('Overwriting mask in : %s'
                        % dataset.master_file)
    overwrite_mask(dataset.master_file)
    dataset.logger.info('Mask overwritten in : %s'
                        % dataset.master_file)

    phil_file = os.path.join(dataset.path, 'ED_Singla.phil')

    if not os.path.exists(phil_file):
        dataset.logger.info('Copying ED_Singl.phil')
        cmd = ['nexgen_phil get ED_Singla.phil -o ' + phil_file]
        subprocess.run(cmd, shell=True, text=True, capture_output=True)
    else:
        dataset.logger.info('ED_Singl.phil detected')

    if os.path.exists(dataset.nexgen_file):
        dataset.logger.info('Found existing nexus file')
        cmd = ['rm ' + dataset.nexgen_file]
        subprocess.run(cmd, shell=True, text=True, capture_output=True)
        dataset.logger.info('Nexus file removed')

    phil_written, _, _ = is_file_fully_written(phil_file)
    if not phil_written:
        dataset.logger.info('Conversion failed. Phil file not written')
        return 0

    mdoc_written, _, _ = is_file_fully_written(dataset.mdoc_file)
    if not mdoc_written:
        dataset.logger.info('Conversion failed. mdoc file not complete')
        return 0

    dataset.logger.info('Scraping voltage from mdoc file')
    voltage_kev = float(scrap(dataset.mdoc_file, 'Voltage'))
    wavelength = electron_wavelength(voltage_kev)

    log_written, _, _ = is_file_fully_written(dataset.log_file)
    if not log_written:
        dataset.logger.info('Conversion failed. log file not complete')
        return 0

    dataset.logger.info('Scraping speed_param from the log file')
    speed_param = float(scrap(dataset.log_file, 'speed parameter'))

    dataset.logger.info('Scraping rotationSpeed from the log file')
    speed_line = scrap(dataset.log_file, 'rotationSpeed')
    pattern = r'^(.*)\*(.*)\+(.*)\*10\^(.*)$'
    params = re.search(pattern, speed_line)

    rotation_speed = float(params.group(1)) * speed_param
    rotation_speed += (float(params.group(3)) *
                       10**(float(params.group(4))))

    start_angle = float(scrap(dataset.log_file, 'start angle'))
    dataset.logger.info('Scraping start angle from the log file: %f'
                        % start_angle)

    frame_rate = float(scrap(dataset.log_file, 'frame rate'))
    dataset.logger.info('Scraping frame rate from the log file: %f'
                        % frame_rate)

    rotation_angle = rotation_speed / frame_rate

    data_file_pattern = dataset.base + r'_data_*.h5'

    patch_written, _, _ = is_file_fully_written(dataset.patch_file)
    if not patch_written:
        dataset.logger.info('Conversion failed. Patch file not complete')
        return 0

    detector_distance = get_detector_distance(dataset.patch_file)

    nex_cmd = 'ED_nexus singla-phil '
    nex_cmd += '%s ' % phil_file
    nex_cmd += r'input.datafiles=%s ' % data_file_pattern
    nex_cmd += 'goniometer.starts=%.0f,0,0,0 ' % start_angle
    nex_cmd += 'goniometer.increments=%.5f,0,0,0 ' % rotation_angle
    nex_cmd += 'goniometer.vectors=0,-1,0,0,0,1,0,1,0,1,0,0 '
    nex_cmd += 'detector.starts=%f ' % detector_distance
    nex_cmd += 'beam.wavelength=%.10f ' % wavelength
    if dataset.beam_center:
        nex_cmd += 'detector.beam_center=%.2f,%.2f ' % dataset.beam_center
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


def run_slurm_job(dataset):

    slurm_config_file = 'data/relion_slurm_cpu.json'
    slurm_config_file = os.path.join(autoed.__path__[0],
                                     slurm_config_file)

    with open(slurm_config_file, 'r') as file:
        data = json.load(file)

    data['job']['current_working_directory'] = dataset.output_path
    data['job']['environment']['USER'] = os.getenv('USER')
    data['job']['environment']['HOME'] = os.getenv('HOME')
    commands = data['script']
    new_cmd = commands.replace('NEXUS_FILE_PATH',
                               dataset.nexgen_file)
    data['script'] = new_cmd

    with open(dataset.slurm_file, 'w') as file:
        json.dump(data, file, indent=2)

    if 'SLURM_JWT' not in os.environ:
        cmd = 'export `ssh wilson scontrol token lifespan=7776000`;'
    else:
        cmd = ''
    cmd += 'curl -s -H X-SLURM-USER-NAME:${USER} -H '
    cmd += 'X-SLURM-USER-TOKEN:${SLURM_JWT} '
    cmd += '-H "Content-Type: application/json" '
    cmd += '-X POST https://slurm-rest.diamond.ac.uk:'
    cmd += '8443/slurm/v0.0.38/job/submit '
    cmd += '-d@' + dataset.slurm_file

    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, cwd=dataset.path)
    if p.stderr:
        msg = 'Failed to process data with xia2'
        dataset.logger.error(msg)
        dataset.logger.error(p.stderr)
        return 0
    else:
        dataset.logger.info('Data processed')
        return 1
