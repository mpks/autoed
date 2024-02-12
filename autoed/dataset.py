#!/usr/bin/env python3
import os
import logging
from .convert import generate_nexus_file
from .beam_center import BeamCenterCalculator


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
        self.output_path = None
        self.logger = None
        self.status = 'NEW'
        self.beam_center = None
        self.processed = False
        self.data_files = []

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
                       os.path.exists(self.mdoc_file))
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
                if self.output_path:
                    os.makedirs(self.output_path, exist_ok=True)
                # print('Can process with xia2')
                pass

    def convert(self):
        """Generates Nexus file from the dataset files using nexgen"""

        return
