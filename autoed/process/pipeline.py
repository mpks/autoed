""" A class which allows for different processing pipelines """
import os
import autoed
import json
from abc import ABC, abstractmethod
from autoed.constants import xia2_pipelines, dials_pipelines, all_pipelines
import subprocess


class Pipeline(ABC):

    @abstractmethod
    def __init__(self, dataset, method=xia2_pipelines[0]):
        """
        A pipeline to process diffraction data

        dataset : SinglaDataset
        method : string
            Method used to process the dataset:
            default - Run xia2 with default params.
            user - Run xia2 with user-provided space group and unit cell.
            ice - Run xia2 with ice parameters.
            max_lattices - Run with DIALS using `max_lattices=5` parameter.
            real_space_indexing - Run xia2 using real space indexing.
            xds - Run with xia2 with XDS pipeline.
        """

        self.dataset = dataset
        self.method = method

        self.out_dir = os.path.join(dataset.output_path, method)
        os.makedirs(self.out_dir, exist_ok=True)

    @abstractmethod
    def run(self):
        pass

    def generate_pipeline_cmd(self):
        """Generate the command to process the pipeline"""

        if self.method in dials_pipelines:
            cmd = self.generate_dials_cmd()
        elif self.method in xia2_pipelines:
            cmd = self.generate_xia2_cmd()
        else:
            cmd = f"echo Unknown method provided: '{self.method}'\n "
            cmd += "echo pipeline empty \n "
        return cmd

    def generate_dials_cmd(self):
        """Generate commands for methods that work with DIALS"""

        import_file = os.path.join(self.out_dir, 'imported.expt')
        refl_file = os.path.join(self.out_dir, 'strong.refl')
        nexus_file = self.dataset.nexgen_file

        cmd = f"dials.import {nexus_file} goniometer.axis=0,-1,0; "
        cmd += f"dials.find_spots {import_file} d_max=9; "
        cmd += f"dials.index {import_file} {refl_file} "
        cmd += "detector.fix=distance "

        if self.method == 'max_lattices':
            options = 'max_lattices=5 '
            cmd += options
            cmd += "\n"
        else:
            cmd = f"echo Unknown method provided: '{self.method}'\n "
            cmd += "echo pipeline empty \n "
        return cmd

    def generate_xia2_cmd(self):
        """Generate commands for methods that work with xia2"""

        cmd = f"xia2 image={self.dataset.nexgen_file} "
        cmd += "goniometer.axis=0,-1,0 dials.fix_distance=True "
        cmd += "dials.masking.d_max=9 "

        if self.method == 'default':
            cmd += "\n"
        elif self.method == 'ice':
            cmd += "xia2.settings.unit_cell=4.5,4.5,7.33,90,90,119.999 "
            cmd += 'xia2.settings.space_group="P63/mmc" '
            cmd += "\n"
        elif self.method == 'user':
            option = ''

            # If the user does not supply either a unit cell or a space group
            # the is no point in processing this pipeline
            process_user = False

            if is_unit_cell_OK(self.dataset.metadata.unit_cell):
                a, b, c, alpha, beta, gamma = self.dataset.metadata.unit_cell
                unit_cell = f"{a},{b},{c},{alpha},{beta},{gamma}"
                option += f"xia2.settings.unit_cell={unit_cell} "
                process_user = True

            if self.dataset.metadata.space_group:
                sg = self.dataset.metadata.space_group
                option += f"xia2.settings.space_group={sg} "
                process_user = True

            cmd += option
            cmd += "\n"

            if not process_user:
                cmd = "echo Wrong unit cell or space group provided\n "
                cmd += f"echo Unit cell: {self.dataset.metadata.unit_cell}\n "
                cmd += f"echo SG: {self.dataset.metadata.space_group}\n "
                cmd += "echo Pipeline with user parameters empty \n "
                return cmd

        elif self.method == 'real_space_indexing':

            option = 'dials.index.method=real_space_grid_search '

            if is_unit_cell_OK(self.dataset.metadata.unit_cell):
                a, b, c, alpha, beta, gamma = self.dataset.metadata.unit_cell
                unit_cell = f"{a},{b},{c},{alpha},{beta},{gamma}"
                option += f"xia2.settings.unit_cell={unit_cell} "
            else:
                cmd = "echo Method real_space_grid_search "
                cmd += "requires the user to provide the unit cell.\n "
                cmd += "echo pipeline empty \n "
                return cmd

            if self.dataset.metadata.space_group:
                sg = self.dataset.metadata.space_group
                option += f"xia2.settings.space_group={sg} "

            option += cmd
            cmd += "\n"

        else:         # Wrong command provided (do nothing)
            cmd = f"echo Unknown method provided: '{self.method}'\n "
            cmd += "echo pipeline empty \n "
        return cmd


class LocalPipeline(Pipeline):
    """Pipeline that runs processes locally using a bash script"""

    def __init__(self, dataset, method=xia2_pipelines[0]):
        super().__init__(dataset, method)
        self.bash_file = os.path.join(self.out_dir, 'run_pipeline.sh')

        script = self.generate_bash_script()

        with open(self.bash_file, 'w') as bash_file:
            bash_file.write(script)

    def generate_bash_script(self):
        start = "#!/bin/bash\n"
        start += "echo \"$(date '+%Y-%m-%d %H:%M:%S.%3N'):\"\n"
        start += "if command -v module &> /dev/null; then\n"
        start += "    module load ccp4 || true\n"
        start += "    module load dials || true\n"
        start += "fi\n"

        command = self.generate_pipeline_cmd()

        end = "echo \"$(date '+%Y-%m-%d %H:%M:%S.%3N'): job finished\""

        return start + command + end

    def run(self):

        if not self.dataset.dummy:

            p = subprocess.run('bash ' + self.bash_file,
                               shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, cwd=self.out_dir,
                               env=os.environ)
            if p.stderr:
                msg = "Failed to process data with local pipeline "
                msg += f"'{self.method}'"
                self.dataset.logger.error(msg)
                self.dataset.logger.error(p.stderr)
                return 0
            else:
                msg = f"Data processed with local pipeline '{self.method}'"
                self.dataset.logger.info(msg)
                return 1
        else:
            self.dataset.logger.info('bash run switched off for testing')
            return 1


class SlurmPipeline(Pipeline):
    """Pipeline that submitts processes using SLURM"""

    def __init__(self, dataset, method='default'):

        super().__init__(dataset, method)
        self.slurm_file = os.path.join(self.out_dir, 'slurm_config.json')

        slurm_template = 'data/relion_slurm_cpu.json'
        slurm_template = os.path.join(autoed.__path__[0], slurm_template)

        with open(slurm_template, 'r') as file:
            data = json.load(file)

        data['job']['current_working_directory'] = self.out_dir
        data['job']['environment']['USER'] = os.getenv('USER')
        data['job']['environment']['HOME'] = os.getenv('HOME')

        script_line = self.generate_json_script()
        data['script'] = script_line

        with open(self.slurm_file, 'w') as file:
            json.dump(data, file, indent=2)

    def generate_json_script(self):

        start = "#!/bin/bash\n"
        start += "echo \"$(date '+%Y-%m-%d %H:%M:%S.%3N'): \"\n"
        start += "echo \"Running on host $(hostname -s) \""
        start += "\"with job ID ${SLURM_JOB_ID:-(SLURM_JOB_ID not set)}\"\n"
        start += "source /etc/profile.d/modules.sh\n"
        start += "module load EM/relion/4.0-slurm 2> /dev/null\n"
        start += "module load ccp4\n"
        start += "module load dials\n"

        command = self.generate_pipeline_cmd()

        end = "\n unset SLURM_JWT\n"
        end += "echo \"$(date '+%Y-%m-%d %H:%M:%S.%3N'):\" job finished\n"

        return start + command + end

    def run(self):

        if 'SLURM_JWT' not in os.environ:
            cmd = 'export `ssh wilson scontrol token lifespan=7776000`;'
        else:
            cmd = ''
        cmd += 'curl -s -H X-SLURM-USER-NAME:${USER} -H '
        cmd += 'X-SLURM-USER-TOKEN:${SLURM_JWT} '
        cmd += '-H "Content-Type: application/json" '
        cmd += '-X POST https://slurm-rest.diamond.ac.uk:'
        cmd += '8443/slurm/v0.0.38/job/submit '
        cmd += '-d@' + self.slurm_file

        if not self.dataset.dummy:

            p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, cwd=self.out_dir)
            if p.stderr:
                msg = f"Failed to process data with pipeline '{self.method}'"
                self.dataset.logger.error(msg)
                self.dataset.logger.error(p.stderr)
                return 0
            else:
                msg = f"Data processed with pipeline '{self.method}'"
                self.dataset.logger.info(msg)
                return 1
        else:
            self.dataset.logger.info('Slurm run switched off for testing')
            self.dataset.logger.info(f"Slurm command: {cmd}")
            return 1


def is_unit_cell_OK(unit_cell):
    """Checks if unit cell parameter is of the proper format and type"""
    if isinstance(unit_cell, (list, tuple)):
        if len(unit_cell) == 6:
            conds = [isinstance(a, (float, int)) for a in unit_cell]
            return all(conds)
        return False
    return False


def run_processing_pipelines(dataset, local):

    methods = all_pipelines
    pipelines = []

    for method in methods:
        if local:
            pipelines.append(LocalPipeline(dataset, method))
        else:
            pipelines.append(SlurmPipeline(dataset, method))

    for pipeline in pipelines:
        pipeline.run()
