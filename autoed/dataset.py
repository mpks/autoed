#!/usr/bin/env python3
import os
import logging
import re
from .convert import generate_nexus_file, run_slurm_job
from .beam_center import BeamCenterCalculator
from .misc_functions import replace_dir


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
        self.master_file = self.base + '.__master.h5'
        self.log_file = self.base + '._.log'
        self.autoed_log_file = self.base + '.autoed.log'
        self.nexgen_file = self.base + '._.nxs'
        self.mdoc_file = self.base + '._.mrc.mdoc'
        self.patch_file = os.path.join(self.path, 'PatchMaster.sh')

        in_path = os.path.dirname(self.base)
        out_path = replace_dir(in_path, 'ED', 'processed')
        os.makedirs(out_path, exist_ok=True)

        self.output_path = out_path
        self.slurm_file = os.path.join(out_path, 'slurm_config.json')
        self.logger = None
        self.status = 'NEW'
        self.beam_center = None
        self.processed = False
        self.data_files = []

    def search_and_update_data_files(self):

        data_files = []
        pattern = self.base + r'\.__data_\d{6}\.h5'
        for root, dirs, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                if re.match(pattern, file_path):
                    data_files.append(file_path)
        self.data_files = data_files

    def set_logger(self):
        self.logger = logging.getLogger(self.base)
        self.logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(self.autoed_log_file)
        stream_handler = logging.StreamHandler()

        fmt = '%(asctime)s %(levelname)s - %(message)s'
        formatter = logging.Formatter(fmt, datefmt='%d-%m-%Y %H:%M:%S')
        stream_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        stream_handler.setLevel(logging.DEBUG)
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
        return files_exist and data_exists

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
                self._compute_beam_center()
            success = generate_nexus_file(self)
            if success:
                os.makedirs(self.output_path, exist_ok=True)
                run_slurm_job(self)
