"""Helper functions used to determine the beam position of the imported data"""

from __future__ import annotations

from typing import List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass
from matplotlib import gridspec
from matplotlib.patches import Circle


def remove_percentiles(image, percentile=0.999):

    pixels_1d = np.sort(image.flatten())
    ntot = len(pixels_1d)
    ncut = int(ntot * 0.999)
    icut = pixels_1d[ncut]
    image[image > icut] = 0

    return image


def normalize(array):
    """Normalize a 1D numpy array"""
    array_max = array.max()
    return array / array_max


def smooth(a: np.ndarray, width: int = 1):
    """
    Smooth a 1D numpy array `a` with a rectangle convolution.
    The rectangle width is 2*half_width.
    """

    smooth_a = 0 * a
    n = len(a)

    half_width = int(width / 2)

    for i in range(n):

        if i < half_width:
            smooth_a[i] = a[0 : i + half_width].mean()
        elif i > n - half_width:
            smooth_a[i] = a[i - half_width :].mean()
        else:
            smooth_a[i] = a[i - half_width : i + half_width].mean()

    return smooth_a
