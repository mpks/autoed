import re
import h5py
import os
import numpy as np

import autoed


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


def overwrite_mask(filename):
    """Given a hdf5 file, overwrite the pixel mask"""

    try:
        with h5py.File(filename, 'r+') as file:

            src = '/entry/instrument/detector/detectorSpecific/'
            src += 'pixel_mask'
            pixel_mask = file[src]

            mask_path = 'data/singla_mask.npz'
            mask_path = os.path.join(autoed.__path__[0], mask_path)
            data = np.load(mask_path)
            mask = data['mask']
            pixel_mask[...] = mask

    except KeyError:
        pass


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
