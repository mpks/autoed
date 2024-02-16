#!/usr/bin/env python3
import os
import logging
import re
from .convert import generate_nexus_file, run_slurm_job
from .beam_center import BeamCenterCalculator
from .misc_functions import replace_dir, is_file_fully_written


class SinglaDataset:

    def __init__(self, path, dataset_name):
        """
        path : Path
            Path of the dataset.
        dataset_name : str
            Name of the dataset. Usually, if given a
            master file 'abc.__master.h5', the dataset
            will have name 'abc'
        """

        self.path = path
        self.dataset_name = dataset_name
        self.base = os.path.join(path, dataset_name)
        self.master_file = self.base + '_master.h5'
        self.log_file = self.base + '.log'
        self.autoed_log_file = self.base + '.autoed.log'
        self.nexgen_file = self.base + '.nxs'
        self.mdoc_file = self.base + '.mrc.mdoc'
        self.patch_file = os.path.join(self.path, 'PatchMaster.sh')

        in_path = os.path.dirname(self.base)
        out_path = replace_dir(in_path, 'ED', 'processed')
        os.makedirs(out_path, exist_ok=True)

        self.output_path = out_path
        self.slurm_file = os.path.join(out_path, 'slurm_config.json')
        self.set_logger()
        self.status = 'NEW'
        self.beam_center = None
        self.present_lock = False
        self.processed = False
        self.data_files = []

    def search_and_update_data_files(self):

        data_files = []
        pattern = self.base + r'\_data_\d{6}\.h5'
        for root, dirs, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                if re.match(pattern, file_path):
                    data_files.append(file_path)
        self.data_files = data_files

    def set_logger(self):

        self.logger = logging.getLogger(self.base)
        self.logger.setLevel(logging.DEBUG)

        # Clear the log file if it exists
        with open(self.autoed_log_file, 'w'):
            pass

        file_handler = logging.FileHandler(self.autoed_log_file)
        # stream_handler = logging.StreamHandler()

        fmt = '%(asctime)s.%(msecs)03d %(levelname)s - %(message)s'
        formatter = logging.Formatter(fmt, datefmt='%d-%m-%Y %H:%M:%S')
        # stream_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # stream_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)

        self.logger.addHandler(file_handler)
        # self.logger.addHandler(stream_handler)

    def all_files_present(self):
        """Checks if all files for the current dataset are present"""

        data_exists = len(self.data_files) > 0
        files_exist = (os.path.exists(self.master_file) and
                       os.path.exists(self.log_file) and
                       os.path.exists(self.mdoc_file) and
                       os.path.exists(self.patch_file))

        if files_exist and data_exists:
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
        else:
            self.logger.info('Dataset not complete %s' % self.base)
            return False

    @classmethod
    def from_basename(cls, basename):
        path = os.path.dirname(basename)
        dataset_name = os.path.basename(basename)
        return cls(path, dataset_name)

    def _compute_beam_center(self):

        if len(self.data_files) > 0:
            calculator = BeamCenterCalculator(self.data_files[0])
            x, y = calculator.center_from_average()
            self.beam_center = (x, y)
            calculator.file.close()

        return

    def process(self):
        if not self.processed:
            self.processed = True
            if not self.beam_center:
                msg = 'Computing the beam center for %s'
                self.logger.info(msg % self.dataset_name)

                self._compute_beam_center()

                msg = 'Beam center for %s' % self.dataset_name
                msg += ' = (%f, %f) ' % self.beam_center
                self.logger.info(msg)

            success = generate_nexus_file(self)
            if success:
                os.makedirs(self.output_path, exist_ok=True)
                run_slurm_job(self)
