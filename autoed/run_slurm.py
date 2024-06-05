import subprocess
import os
import autoed
import json


def run_slurm_job(dataset):

    slurm_config_file = 'data/relion_slurm_cpu.json'
    slurm_config_file = os.path.join(autoed.__path__[0], slurm_config_file)

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

    if dataset.run_slurm:
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

    else:
        dataset.logger.info('Slurm run switched off for this session.')
        dataset.logger.info(f"Slurm command: {cmd}")
        return 1
