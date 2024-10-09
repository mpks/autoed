"""Define Singla dataset class"""
import os
import logging
import time
import re
from autoed.convert import generate_nexus_file
from autoed.process.pipeline import run_processing_pipelines
from autoed.beam_position.beam_center import BeamCenterCalculator
from autoed.utility.misc_functions import replace_dir, is_file_fully_written
from autoed.metadata import Metadata


class SinglaDataset:                    # pylint: disable=R0902
    """A class to keep all data relevant to single experimental dataset"""

    def __init__(self, path, dataset_name, make_out_path=True):
        """
        path : Path
            Path of the dataset.
        dataset_name : str
            Name of the dataset. Usually, if given a master file
            'abc.__master.h5', the dataset will have name 'abc'.
        make_out_path: boolean
            If True, the AutoED will create a path in the processed directory,
            and the log file in the data directory.
        """

        self.path = path
        self.dataset_name = dataset_name
        self.base = os.path.join(path, dataset_name)
        self.master_file = self.base + '_master.h5'
        self.log_file = self.base + '.log'
        self.autoed_log_file = self.base + '.autoed.log'
        self.nexgen_file = self.base + '.nxs'
        self.json_file = self.base + '.json'
        self.mdoc_file = self.base + '.mrc.mdoc'
        self.patch_file = os.path.join(self.path, 'PatchMaster.sh')
        self.beam_figure = os.path.join(self.path, 'beam_position.png')

        in_path = os.path.dirname(self.base)
        out_path = replace_dir(in_path, 'ED', 'processed')

        # We use dataset object in report generator. We do not want
        # to create output paths or write logs when generating reports.
        # Also, the report generation would fail if used by someone without
        # write permissions in out_path.
        if make_out_path:
            os.makedirs(out_path, exist_ok=True)
            self.set_logger()

        self.output_path = out_path
        self.slurm_file = os.path.join(out_path, 'slurm_config.json')
        self.status = 'NEW'
        self.beam_center = None
        self.present_lock = False
        self.processed = False
        self.last_processed_time = 0
        self.dummy = False
        self.data_files = []
        self.metadata = None

    def search_and_update_data_files(self):

        data_files = []
        pattern = self.base + r'\_data_\d{6}\.h5'
        for root, dirs, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                if re.match(pattern, file_path):
                    data_files.append(file_path)
        self.data_files = data_files

    def set_logger(self, clear=True):

        self.logger = logging.getLogger(self.base)
        self.logger.setLevel(logging.DEBUG)

        if clear:          # Clear the log file if it exists
            with open(self.autoed_log_file, 'w'):
                pass

        file_handler = logging.FileHandler(self.autoed_log_file)

        fmt = '%(asctime)s.%(msecs)03d %(levelname)s - %(message)s'
        formatter = logging.Formatter(fmt, datefmt='%d-%m-%Y %H:%M:%S')
        file_handler.setFormatter(formatter)

        file_handler.setLevel(logging.DEBUG)

        self.logger.addHandler(file_handler)

    def all_files_present(self):
        """Checks if all files for the current dataset are present"""

        data_exists = len(self.data_files) > 0
        files_exist = (os.path.exists(self.master_file) and
                       os.path.exists(self.log_file) and
                       os.path.exists(self.mdoc_file) and
                       os.path.exists(self.patch_file))

        new_files_exist = (os.path.exists(self.master_file) and
                           os.path.exists(self.json_file))

        if (files_exist and data_exists):
            self.logger.info('All files present in dataset %s' % self.base)

            con_data = True
            for data_file in self.data_files:

                self.logger.info('Waiting for data to be written: %s'
                                 % data_file)
                con_temp, sd, td = is_file_fully_written(data_file,
                                                         timeout=1200)
                if con_temp:
                    self.logger.info('Data file size stable: %d %s'
                                     % (sd, data_file))
                else:
                    self.logger.info('Data file size test failed %d %s'
                                     % (sd, data_file))
                con_data = con_data and con_temp

            self.logger.info('Waiting for master file: %s'
                             % self.master_file)
            con1, s1, t1 = is_file_fully_written(self.master_file,
                                                 timeout=180)
            if con1:
                self.logger.info('Master file size stable: %d %s'
                                 % (s1, self.master_file))
            else:
                self.logger.info('Master file size test failed: %d %s'
                                 % (s1, self.master_file))

            self.logger.info('Waiting for log file: %s'
                             % self.log_file)
            con2, s2, t2 = is_file_fully_written(self.log_file)
            if con2:
                self.logger.info('Log file size stable: %d %s'
                                 % (s2, self.log_file))
            else:
                self.logger.info('Log file size test failed: %d %s'
                                 % (s2, self.log_file))

            self.logger.info('Waiting for mdoc file: %s'
                             % self.mdoc_file)
            con3, s3, t3 = is_file_fully_written(self.mdoc_file)
            if con3:
                self.logger.info('Mdoc file size stable: %d %s'
                                 % (s3, self.mdoc_file))
            else:
                self.logger.info('Mdoc file size test failed: %d %s'
                                 % (s3, self.mdoc_file))

            self.logger.info('Waiting for Patch file: %s'
                             % self.patch_file)
            con4, s4, t4 = is_file_fully_written(self.patch_file)
            if con4:
                self.logger.info('PatchMaster.sh file size stable: %d %s'
                                 % (s4, self.patch_file))
            else:
                self.logger.info('PatchMaster.sh file size test failed: %d %s'
                                 % (s4, self.patch_file))
            if con1 and con2 and con3 and con4 and con_data:
                self.present_lock = True
            return con1 and con2 and con3 and con4 and con_data
        elif (new_files_exist and data_exists):
            self.logger.info(f"Detected JSON dataset: {self.base}")
            return True
        else:
            self.logger.info('Dataset not complete %s' % self.base)
            return False

    @classmethod
    def from_basename(cls, basename, make_out_path=True):
        path = os.path.dirname(basename)
        dataset_name = os.path.basename(basename)
        return cls(path, dataset_name, make_out_path=make_out_path)

    def update_processed(self):
        """
        AutoED can process a dataset again if we want. If data is sitting
        for say 10 min after being processed, it should be possible to
        reprocess it again.
        """
        time_diff = time.time() - self.last_processed_time
        if time_diff > 300:
            self.processed = False

    def compute_beam_center(self):

        if len(self.data_files) > 0:

            calc = BeamCenterCalculator(self.data_files[0])

            if calc.problem_reading:
                x = 514
                y = 531
                msg = f"Problem reading data file {self.data_files[0]}.\n"
                msg += "Setting beam position to default (514, 531)."
                self.logger.error(msg)
                self.beam_center = (x, y)
                return

            x, y = calc.center_from_mixed(every=50,
                                          plot_file=self.beam_figure)

            if not x:
                msg = 'Beam position along x is None. Setting beam_x to 514'
                self.logger.error(msg)
                x = 514
            if not y:
                msg = 'Beam position along y is None. Setting beam_y to 531'
                self.logger.error(msg)
                y = 531
            self.beam_center = (x, y)
            calc.file.close()

        return

    def fetch_metadata(self):

        metadata = Metadata()
        new_files_exist = (os.path.exists(self.master_file) and
                           os.path.exists(self.json_file))

        # First try to fetch metadata from JSON format
        success_json = False
        if new_files_exist:
            success_json = metadata.from_json(self)

        # If fetching from JSON fails, try with the old (textual) format
        if not success_json:
            self.logger.error('Failed to fetch metadata from JSON')
            self.logger.info('Trying to fetch metadata from txt')
            success_txt = metadata.from_txt(self)
            if not success_txt:
                self.logger.error('Failed to fetch metadata from txt files')
                return False

        self.metadata = metadata
        return True

    def process(self, local=False):

        if not self.processed:
            self.processed = True
            if not self.beam_center:
                msg = f"Computing the beam center for {self.dataset_name}"
                self.logger.info(msg)

                self.compute_beam_center()

                msg = f"Beam center for {self.dataset_name}"
                msg += ' = (%f, %f) ' % self.beam_center
                self.logger.info(msg)

            succes_metadata = self.fetch_metadata()
            if not succes_metadata:
                msg = 'Failed to fetch metadata from JSON and TXT.\n'
                msg += 'No conversion/processing'
                self.logger.error(msg)
                return False
            else:
                success = generate_nexus_file(self)
                if success:
                    msg = 'Nexus file generated'
                    self.logger.info(msg)
                    os.makedirs(self.output_path, exist_ok=True)
                    # run_slurm_job(self)
                    run_processing_pipelines(self, local)
                    self.last_processed_time = time.time()
                    return True
                else:
                    msg = 'Failed to generate nexus file'
                    self.logger.error(msg)
                    self.last_processed_time = time.time()
                    return False
        return False
