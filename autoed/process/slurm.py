"""A module to simplify processing with SLURM using REST API"""
import subprocess
import os
import argparse

from autoed.global_config import global_config

global_config.overwrite_from_local_config()

def main():
    """Defines autoed_slurm command"""

    msg = 'Submit SLURM script to the cluster using REST API'
    parser = argparse.ArgumentParser(description=msg)

    parser.add_argument('json_file', type=str,
                        help='A JSON file with the processing script')
    args = parser.parse_args()

    error = run_slurm_job(args.json_file)
    

    if error:
        print(error)


def run_slurm_job(slurm_file):
    """Submit the slurm script to Diamond cluster"""

    slurm_file = os.path.abspath(slurm_file)
    print('Slurm file', slurm_file)
    slurm_dir = os.path.dirname(slurm_file)
    print('Slurm dir', slurm_dir)
    user = global_config['slurm_user']
    print('Slurm user', user)

    if 'SLURM_JWT' not in os.environ:
        cmd = 'export `ssh wilson scontrol token lifespan=7776000`;'
    else:
        cmd = ''
    cmd += f'curl -s -H X-SLURM-USER-NAME:{user} -H '
    cmd += 'X-SLURM-USER-TOKEN:${SLURM_JWT} '
    cmd += '-H "Content-Type: application/json" '
    cmd += '-X POST https://slurm-rest.diamond.ac.uk:'
    cmd += '8443/slurm/v0.0.38/job/submit '
    cmd += '-d@' + slurm_file

    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, cwd=slurm_dir)
    if p.stderr:
        return p.stderr

    return None
