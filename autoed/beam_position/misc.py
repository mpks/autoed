"""Helper functions used to determine the beam position of the imported data"""

from __future__ import annotations


import numpy as np


def remove_percentiles(image, percentile=0.999):

    pixels_1d = np.sort(image.flatten())
    ntot = len(pixels_1d)
    ncut = int(ntot * 0.999)
    icut = pixels_1d[ncut]
    clean_image = np.array(image)
    clean_image[image > icut] = 0

    return clean_image


def normalize(array):
    """Normalize a 1D numpy array"""
    array_max = array.max()
    return array / array_max


def smooth(a, half_width=1):
    """Given a 1D array a, do convolution with a rectangle
       function of the width = 2*half_width
    """

    smooth = 0*a
    n = len(a)
    for i in range(n):
        if i < half_width:
            smooth[i] = a[0:i+half_width].mean()
        elif i > n - half_width:
            smooth[i] = a[i-half_width:].mean()
        else:
            smooth[i] = a[i-half_width:i+half_width].mean()
    return smooth
