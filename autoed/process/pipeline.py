""" A class which allows for different processing pipelines """
import os
import json
from abc import ABC, abstractmethod
import subprocess
import traceback

import autoed
from autoed.global_config import global_config
from autoed.utility.filesystem import clear_dir
from autoed.constants import PROCESS_DONE_TRIGGER
from autoed.process.slurm import run_slurm_job


class Pipeline(ABC):
    """An abstract processing pipeline class"""

    @abstractmethod
    def __init__(self, dataset, pipeline_dict):
        """
        A pipeline to process diffraction data

        dataset : SinglaDataset
        pipeline_dict : dictionary
            A dictionary that defines all the pipeline details
        """

        self.dataset = dataset
        self.info = pipeline_dict
        self.method = pipeline_dict['pipeline_name']
        self.run_condition = False     # By default, pipeline will not run

        self.out_dir = os.path.join(dataset.output_path, self.method)
        os.makedirs(self.out_dir, exist_ok=True)
        if not dataset.dummy:
            clear_dir(self.out_dir)    # Clear any previous output

    @abstractmethod
    def run(self):
        """Run processing pipeline"""

    def generate_pipeline_cmd(self):
        """Generate the command to process the pipeline"""

        g = global_config
        m = self.dataset.metadata

        unit_cell = 'None'
        if is_unit_cell_ok(m.unit_cell):
            a, b, c, alpha, beta, gamma = m.unit_cell
            unit_cell = f"{a},{b},{c},{alpha},{beta},{gamma}"

        imported_file = os.path.join(self.out_dir, 'imported.expt')
        refl_file = os.path.join(self.out_dir, 'strong.refl')
        nexus_file = self.dataset.nexgen_file

        variables_dict = {'m': m, 'g': g, 'imported_file': imported_file,
                          'nexus_file': nexus_file,
                          'refl_file': refl_file,
                          'processed_dir': self.out_dir,
                          'unit_cell': unit_cell}

        script = self.info['script']

        run_condition = self.info['run_condition']

        if isinstance(run_condition, bool):
            self.run_condition = run_condition
        else:
            try:
                eval_out = eval(run_condition)
                if isinstance(eval_out, bool):
                    self.run_condition = eval_out
            except Exception:
                full_traceback = traceback.format_exc()
                msg = "Failed to parse the run condition in the pipeline"
                msg += f" '{self.method}'"
                self.dataset.logger.error(msg)
                self.run_condition = False

        if self.run_condition:
            cmd = ''
            for line in script:
                if line[-2:] == '%%':  # Concatenate without space
                    cmd += line[:-2]
                else:
                    line += " "
                    cmd += line
            try:
                new_cmd = cmd.format(**variables_dict)
            except Exception:
                full_traceback = traceback.format_exc()
                msg = f"Failed to parse the pipeline '{self.method}' script\n"
                msg += f"{full_traceback}\n"
                self.dataset.logger.error(msg)
                new_cmd = 'echo Failed to parse the pipeline script string;\n'
            return new_cmd

        msg = f"Run conditions for the pipeline '{self.method}'"
        msg += " not satisfied. Ignoring this pipeline for this dataset."
        self.dataset.logger.error(msg)

        cmd = 'echo Run condition for this pipeline is not satisfied;\n '
        return cmd

    def submit_report_watch(self):
        """Submit a subprocess to wait for finished processing"""

        done_file = os.path.join(self.out_dir, self.method)
        done_file = os.path.join(done_file, PROCESS_DONE_TRIGGER)

        # Remove .done file if it exists from previous runs
        if os.path.exists(done_file):
            os.remove(done_file)

        cmds = []
        cmds.append('autoed_add_to_database')
        cmds.append(f'{self.dataset.master_file}')
        cmds.append(f'{self.method}')

        if global_config['run_multiplex']:
            cmds.append('--multiplex')

        if global_config['local']:
            cmds.append('--local')

        # Note that beside adding result to report database, the submitted
        # script starts the multiplex processing
        subprocess.Popen(cmds, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)


class LocalPipeline(Pipeline):
    """Pipeline that runs processes locally using a bash script"""

    def __init__(self, dataset, pipeline_dict):

        super().__init__(dataset, pipeline_dict)
        self.bash_file = os.path.join(self.out_dir, 'run_pipeline.sh')

        script = self.generate_bash_script()

        with open(self.bash_file, 'w', encoding='utf-8') as bash_file:
            bash_file.write(script)

    def generate_bash_script(self):
        """Write the bash script for local processing"""

        start = "#!/bin/bash\n"
        start += "echo \"$(date '+%Y-%m-%d %H:%M:%S.%3N'):\"\n"
        start += "if command -v module &> /dev/null; then\n"
        start += "    module load ccp4 || true\n"
        start += "    module load dials || true\n"
        start += "fi\n"

        command = self.generate_pipeline_cmd()

        end = "echo \"$(date '+%Y-%m-%d %H:%M:%S.%3N'): job finished\";\n"
        end += f"touch {PROCESS_DONE_TRIGGER};\n"

        return start + command + end

    def run(self):

        if not self.dataset.dummy:

            msg = f"Processing with local pipeline '{self.method}'"
            self.dataset.logger.info(msg)

            self.submit_report_watch()

            p = subprocess.run('bash ' + self.bash_file,
                               shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, cwd=self.out_dir,
                               env=os.environ, check=False)
            if p.stderr:
                msg = f"Pipeline '{self.method}' status: FAILED"
                self.dataset.logger.error(msg)
                self.dataset.logger.error(p.stderr)
                return 0

            msg = f"Pipeline '{self.method}' status: PROCESSED"
            self.dataset.logger.info(msg)
            return 1

        msg = f"Pipeline '{self.method}' status: DUMMY PROCESSED"
        self.dataset.logger.info(msg)
        return 1


class SlurmPipeline(Pipeline):
    """Pipeline that submitts processes using SLURM"""

    def __init__(self, dataset, pipeline_dict):

        super().__init__(dataset, pipeline_dict)
        self.slurm_file = os.path.join(self.out_dir, 'slurm_config.json')

        slurm_template = 'data/relion_slurm_cpu.json'
        slurm_template = os.path.join(autoed.__path__[0], slurm_template)

        with open(slurm_template, 'r', encoding='utf-8') as file:
            data = json.load(file)

        data['job']['current_working_directory'] = self.out_dir
        data['job']['environment'].append(f"USER={os.getenv('USER')}")
        data['job']['environment'].append(f"HOME={os.getenv('HOME')}")

        script_line = self.generate_json_script()
        data['script'] = script_line

        with open(self.slurm_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)

    def generate_json_script(self):
        """Write slurm processing script into the JSON file"""

        start = "#!/bin/bash\n"
        start += "echo \"$(date '+%Y-%m-%d %H:%M:%S.%3N'): \"\n"
        start += "echo \"Running on host $(hostname -s) \""
        start += "\"with job ID ${SLURM_JOB_ID:-(SLURM_JOB_ID not set)}\"\n"
        start += "source /etc/profile.d/modules.sh\n"
        start += "module load ccp4\n"
        start += "module load dials\n"

        command = self.generate_pipeline_cmd()

        end = "\n unset SLURM_JWT\n"
        end += "echo \"$(date '+%Y-%m-%d %H:%M:%S.%3N'):\" job finished;\n"
        end += f"touch {PROCESS_DONE_TRIGGER};\n"

        return start + command + end

    def run(self):

        if not self.dataset.dummy:

            error, _ = run_slurm_job(self.slurm_file)

            if error:
                msg = f"Failed to process data with pipeline '{self.method}'"
                self.dataset.logger.error(msg)
                self.dataset.logger.error(error)
                return 0

            self.submit_report_watch()
            msg = f"Data processed with pipeline '{self.method}'"
            self.dataset.logger.info(msg)
            return 1

        self.dataset.logger.info('Slurm run switched off for testing')
        return 1


def is_unit_cell_ok(unit_cell):
    """Checks if unit cell parameter is of the proper format and type"""
    if isinstance(unit_cell, (list, tuple)):
        if len(unit_cell) == 6:
            conds = [isinstance(a, (float, int)) for a in unit_cell]
            return all(conds)
        return False
    return False


def run_processing_pipelines(dataset, local):
    """Run only pipelines set in the global config file"""

    pipelines = []
    running_pipelines = global_config.run_pipelines

    # Only run those pipelines that apear in the global config file
    for name, run_pipeline in running_pipelines.items():
        if run_pipeline:

            # Search if the pipeline is defined in the global parameters
            for pipeline in global_config.defined_pipelines:

                if pipeline['pipeline_name'] == name:

                    if local:
                        pipelines.append(LocalPipeline(dataset, pipeline))
                    else:
                        pipelines.append(SlurmPipeline(dataset, pipeline))

    for pipeline in pipelines:
        if pipeline.run_condition:
            pipeline.run()
