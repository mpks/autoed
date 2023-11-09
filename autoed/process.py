#!/usr/bin/env python3
import subprocess
import os
import re
import sys
from time import time
import time as tme
import logging


def main():

    in_dir = sys.argv[1]    # Directory to be processed
    print('Running process')

    converter = SinglaConverter(in_dir)

    converter.check_files()
    converter.convert()
    converter.process()

    logger = converter.logging.getLogger()
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)


class SinglaConverter:

    def __init__(self, path):
        self._path = path
        log_file = os.path.join(path, 'auto_processing.log')
        fmt = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(filename=log_file,
                            level=logging.INFO,
                            format=fmt)
        self.logging = logging

    def check_files(self, wait_time=5):
        """Checks if there exists a master and other files.
        This action is activated on a directory creation,
        so there is a wait time for the directory to
        get populated.
        """

        start_time = time()
        current_time = time()
        all_files_present = False

        while (current_time - start_time) < wait_time:

            files = os.listdir(self._path)
            master_files = [file for file in files if
                            re.match(r".*\.__master.h5$", file)]

            if master_files:

                master_file = master_files[0]
                master_path = os.path.join(self._path, master_file)
                filename = master_file[:-12]

                log_file = filename + '.log'
                log_path = os.path.join(self._path, log_file)

                df_pattern = filename + r".__data_\d{6}.h5"
                data_files = [file for file in files if
                              re.match(df_pattern, file)]
                if data_files:
                    data_file = data_files[0]
                    data_path = os.path.join(self._path, data_file)

                else:
                    data_file = None
                    data_path = None

                mdoc_file = filename[0:9] + filename[14:] + '._.mrc.mdoc'
                mdoc_path = os.path.join(self._path, mdoc_file)

                all_files_present = (os.path.exists(log_path) and
                                     os.path.exists(data_path) and
                                     os.path.exists(mdoc_path))
            if all_files_present:
                break
            current_time = time()

        if all_files_present:
            self.logging.info('Input files checked. All files present.')
            self._master_file = master_path
            self._log_file = log_path
            self._data_file = data_path
            self._mdoc_file = mdoc_path
            self._filename = filename

            nexgen_file = self._filename + '._.nxs'
            nexgen_path = os.path.join(self._path, nexgen_file)
            self._nexgen_file = nexgen_path

            phil_file = 'ED_Singla.phil'
            phil_path = os.path.join(self._path, phil_file)
            self._phil_file = phil_path
            if os.path.exists(phil_path):
                self.logging.info('Removing file ' + phil_path)
                os.remove(phil_path)

        else:
            msg = 'Could not find all the required input files.'
            self.logging.info(msg)
            # raise IOError(msg)

    def convert(self):

        self.logging.info('Starting conversion with nexgen.')
        run = subprocess.run

        if not os.path.exists(self._phil_file):
            cmd = ['nexgen_phil get ED_Singla.phil -o ' + self._path]
            run(cmd, shell=True, text=True, capture_output=True)
        # We get into troubles running Nexgen later if we do not
        # wait for the ED_Singla.phil to be created
        tme.sleep(1)   # Please do not delete

        # Remove nexgen file if it exists
        if os.path.exists(self._nexgen_file):
            self.logging.info('Found existing nexgen file. Removing')
            os.remove(self._nexgen_file)

        voltage_kev = float(scrap(self._mdoc_file, 'Voltage'))
        wavelength = electron_wavelength(voltage_kev)

        speed_param = float(scrap(self._log_file, 'speed parameter'))
        speed_line = scrap(self._log_file, 'rotationSpeed')
        pattern = r'^(.*)\*(.*)\+(.*)\*10\^(.*)$'
        params = re.search(pattern, speed_line)
        rotation_speed = float(params.group(1)) * speed_param
        rotation_speed += (float(params.group(3)) *
                           10**(float(params.group(4))))

        start_angle = float(scrap(self._log_file, 'start angle'))
        frame_rate = float(scrap(self._log_file, 'frame rate'))
        rotation_angle = rotation_speed / frame_rate

        nex_cmd = 'ED_nexus singla '
        nex_cmd += '%s ' % self._phil_file
        nex_cmd += 'input.datafiles=%s ' % self._data_file
        nex_cmd += 'goniometer.starts=%.0f,0,0,0 ' % start_angle
        nex_cmd += 'goniometer.increments=%.5f,0,0,0 ' % rotation_angle
        nex_cmd += 'goniometer.vectors=0,-1,0,0,0,1,0,1,0,1,0,0 '
        nex_cmd += 'detector.starts=809 '
        nex_cmd += 'beam.wavelength=%.10f ' % wavelength
        nex_cmd += '-m %s ' % self._master_file

        # Remove EDnxs.log if it exists
        EDnxs_file = os.path.join(self._path, 'EDnxs.log')
        if os.path.exists(EDnxs_file):
            self.logging.info('Removing old EDnxs.log file')
            os.remove(EDnxs_file)
        self.logging.info('Running nexgen conversion:' + nex_cmd)

        p = subprocess.run(nex_cmd, shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           cwd=self._path)
        if p.stderr:
            self.logging.error(p.stderr)
            msg = 'Failed to process data with nexgen'
            self.logging.error(msg)
            # raise IOError(msg)
        else:
            self.logging.error(p.stderr)
            self.logging.info('Created nexgen file ' +
                              self._nexgen_file)

    def process(self):

        cmd = 'xia2 pipeline=dials '
        cmd += 'image=%s ' % self._nexgen_file
        cmd += 'dials.fix_distance=True '
        cmd += 'dials.masking.d_max=9'
        self.logging.info('Running xia2 with command ' + cmd)
        try:
            p = subprocess.run(cmd, shell=True, text=True,
                               capture_output=True,
                               cwd=self._path,
                               check=True)
        except subprocess.CalledProcessError:
            logging.info('xia2 processing failed')
        else:
            logging.info('xia2 processing completed')


def scrap(filename, var_name):
    """Reads the filename and returns a 'value' of the first line that matches a 
    pattern 'var_name = value' """

    pattern = var_name + r'\s*=\s*(.*)'
    match_line = None

    with open(filename, 'r') as file:
        for line in file:
            if re.match(pattern, line):
                match_line = line.strip()
                break
    pattern = r'.*\s*=\s*(.*)$'
    value = re.search(pattern, match_line).group(1)
    return value


def electron_wavelength(energy_kev):
    """Converts electron energy in keV into wavelength in Angstroms"""

    from math import sqrt
    mass_e = 510998.9461  # in eV
    h = 4.135667696e-15   # Planck's constant eV*s
    c = 299792458         # Speed of light m/s

    energy = energy_kev * 1000
    wavelength_m = h*c/sqrt(energy**2 + 2*mass_e*energy)
    wavelength_angs = wavelength_m * 1e10

    return wavelength_angs


if __name__ == main():
    main()
