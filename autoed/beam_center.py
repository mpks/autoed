#!/usr/bin/env python3
import h5py
import hdf5plugin
import numpy as np
import matplotlib.pyplot as plt
import os
import autoed
import matplotlib.gridspec as gridspec
from matplotlib.patches import Circle
import argparse

hdf5plugin


def main():

    info = 'A script to determine the beam center'
    parser = argparse.ArgumentParser(description=info)

    parser.add_argument('filename', help='The input file')
    parser.add_argument('-p', '--plot', action='store_true',
                        help='Plot results')
    parser.add_argument('-s', '--stack', action='store_true',
                        help='Compute beam center from stacks')
    parser.add_argument('-a', '--all', action='store_true',
                        help='Compute beam center from all stacks')
    args = parser.parse_args()

    cal = BeamCenterCalculator(args.filename)

    x0, y0 = cal.center_from_average(verbose=True,
                                     plot=args.plot)
    if args.stack or args.all:

        if args.all:
            ns = -1
        else:
            ns = 10

        bx, by = cal.centre_from_max(x0, y0,
                                     plot=args.plot,
                                     number_of_stacks=ns,
                                     verbose=True)
        print('From average: (%.2f, %.2f)' % (x0, y0))
    cal.file.close()


class BeamCenterCalculator:

    def __init__(self, filename):
        mask_path = 'data/singla_mask.npz'
        mask_path = os.path.join(autoed.__path__[0], mask_path)
        mask_data = np.load(mask_path)
        self.mask = mask_data['mask']

        self.file = h5py.File(filename, 'r')
        self.dataset = self.file['/entry/data/data']

    def center_from_average(self, every=100,
                            bad_pixel_treshold=20000,
                            plot=False,
                            verbose=False):
        """ Compute beam center using average electron distribution

            Parameters
            ----------
            every: int
                Take every n-th image from the dataset.
            bad_pixel_treshold : int
                Set any pixel above this value to zero
        """

        average_image = self.dataset[::every, :, :].mean(axis=0)

        average_image[self.mask > 0] = 0
        average_image[average_image > bad_pixel_treshold] = 0
        profile_x, x0 = find_x0_from_avg(average_image)
        profile_y, y0 = find_y0_from_avg(average_image)

        if verbose:
            print('From average: (%.2f, %.2f)' % (x0, y0))
        if plot:
            out_file = 'beam_center.png'
            plot_profile(average_image,
                         profile_x,
                         profile_y,
                         x0, y0,
                         plot_circles=True,
                         filename=out_file)
        return x0, y0

    def centre_from_max(self, x0, y0,
                        pixel_range=10,
                        images_in_stack=20,
                        number_of_stacks=3,
                        bad_pixel_treshold=2000,
                        plot=False,
                        verbose=False):
        """ Compute beam center using peaks of maximal pixels

            Parameters
            ----------
            x0: int
                Initial guess for the beam center.
                Pixel index in the x-direction.
            y0: int
                Initial guess for the beam center.
                Pixel index in the y-direction.
            pixel_range: int
                Beam center is searched in the range
                [x0 - pixel_range, x0 + pixel_range]
                and
                [y0 - pixel_range, y0 + pixel_range]
            images_in_stack: int
                To get maximal pixels, a certain number of
                images are stacked together to compute pixel
                maximums.
            number_of_stacks: int
                Compute the average beam center by averaging
                over different stacks. If number is -1, compute
                the average over all stacks.
            bad_pixel_treshold: int
                Disregard pixels with values above this one
            verbose: boolean
                Print the beam center for each stack
            plot: boolean
                Plot estimated beam position for each stack
        """

        x0_int = int(np.round(x0))
        y0_int = int(np.round(y0))

        average_x = []
        average_y = []

        nimages, ny, nx = self.dataset.shape

        if number_of_stacks == -1:
            nmax = nimages
        elif number_of_stacks > 0:
            nmax = number_of_stacks * images_in_stack
            if nmax > nimages:
                nmax = nimages

        for i in range(0, nmax, images_in_stack):

            max_image = self.dataset[i:i+images_in_stack,
                                     :, :].max(axis=0)
            max_image[self.mask > 0] = 0
            max_image[max_image > bad_pixel_treshold] = 0

            data_x = beam_x_from_max(max_image, x0=x0_int,
                                     width=pixel_range)
            data_y = beam_y_from_max(max_image, y0=y0_int,
                                     width=pixel_range)
            bx = data_x['center']
            by = data_y['center']
            average_x.append(bx)
            average_y.append(by)

            if verbose:
                if i == 0:
                    print('---------------------------')
                print('Image set %04d-%04d: (%d, %d)' %
                      (i, i+images_in_stack, bx, by))

            if plot:
                out_file = ('fig_%04d_%04d.png' %
                            (i, i+images_in_stack))
                plot_profile(max_image,
                             data_x['profile'],
                             data_y['profile'],
                             bx, by,
                             indices_x=data_x['indices'],
                             correlation_x=data_x['correlation'],
                             indices_y=data_y['indices'],
                             correlation_y=data_y['correlation'],
                             plot_circles=True,
                             filename=out_file)
        average_x = np.array(average_x)
        average_y = np.array(average_y)

        if verbose:
            print('---------------------------')
            print('From peaks:   (%.2f, %.2f)' % (average_x.mean(),
                                                  average_y.mean()))

        return average_x.mean(), average_y.mean()


def find_x0_from_avg(avg_image):

    y_start = 203  # choose only rows where mask is
    y_end = 865    # rectangular

    avg_x = avg_image[y_start:y_end:1, :].sum(axis=0)
    avg_x[avg_x > 20000] = 0            # Kill dead pixels
    avg_x = smooth(avg_x, half_width=2)

    # Normalize the distribution
    avg_max = np.max(avg_x)
    avg_x = avg_x / avg_max

    sample = np.arange(0.3, 0.7, 0.01)

    mid_points = []
    for x_point in sample:
        mid_point = middle(avg_x, x_point)
        if mid_point:
            mid_points.append(mid_point)
    center = np.array(mid_points).mean()

    return avg_x, center


def find_y0_from_avg(avg_image):

    x_start = 182  # choose only columns where mask is
    x_end = 845    # rectangular
    mask_start = 512
    mask_end = 551
    avg_y = avg_image[:, x_start:x_end:1].sum(axis=1)
    avg_y[mask_start:mask_end] = 0      # Kill mask
    avg_y[avg_y > 20000] = 0            # Kill dead pixels
    avg_y = smooth(avg_y, half_width=2)
    avg_y[mask_start:mask_end] = 0      # Kill mask

    # Normalize the distribution
    avg_max = np.max(avg_y)
    avg_y = avg_y / avg_max

    # Find value edge values around the mask
    cut1 = np.max(avg_y[mask_start-5:mask_start])
    cut2 = np.max(avg_y[mask_end:mask_end+5])
    cut_min = np.min([cut1, cut2])
    cut_max = np.max([cut1, cut2])

    sample = np.arange(0.3, 0.7, 0.01)
    sample = sample[np.where(np.logical_or(sample <= cut_min,
                                           sample >= cut_max))]
    mid_points = []
    for y_point in sample:
        mid_point = middle(avg_y, y_point)
        if mid_point:
            mid_points.append(mid_point)
    center = np.array(mid_points).mean()

    return avg_y, center


def beam_x_from_max(image, x0=500, width=10):

    y_start = 203  # choose only rows where mask is
    y_end = 865    # rectangular
    x_profile = image[y_start:y_end:1, :].max(axis=0)

    x_profile_max = x_profile.max()
    x_profile = x_profile / x_profile_max

    indices = np.arange(x0-width, x0+width, 1)
    correlations = []
    for index in indices:
        correlations.append(invert_and_correlate(x_profile, index))

    correlations = np.array(correlations)
    index = correlations.argmax()

    data = {}
    data['profile'] = x_profile
    data['indices'] = indices
    data['correlation'] = correlations
    data['center'] = indices[0] + index

    return data


def beam_y_from_max(image, y0=500, width=10):

    x_start = 182  # choose only columns where mask is
    x_end = 845    # rectangular
    mask_start = 512
    mask_end = 551

    y_profile = image[:, x_start:x_end:1].max(axis=1)
    y_profile[mask_start:mask_end] = 0      # Kill the mask

    y_profile_max = y_profile.max()
    y_profile = y_profile / y_profile_max

    indices = np.arange(y0-width, y0+width, 1)
    correlations = []
    for index in indices:
        correlations.append(invert_and_correlate(y_profile, index))

    correlations = np.array(correlations)
    index = correlations.argmax()

    data = {}
    data['profile'] = y_profile
    data['indices'] = indices
    data['correlation'] = correlations
    data['center'] = indices[0] + index

    return data


def invert_and_correlate(x, index):
    """Given an 1D array x, compute inverted array inv_x
       (inversion around an element with index 'index')
       and return a sum of the x * inv_x.
    """

    inv_x = np.zeros(len(x))
    n = len(x)
    half = int(n/2)

    # Computed the inverted 1D array
    if index <= half:
        left = x[0:index]
        right = x[index:2*index]
        inv_x[0:index] = right[::-1]
        inv_x[index:2*index] = left[::-1]
    else:
        right = x[index:]
        width = len(right)
        left = x[index-width:index]
        inv_x[index-width:index] = right[::-1]
        inv_x[index:] = left[::-1]

    return np.sum(x * inv_x)


def middle(a, ymin):
    """Compute a middle pixel of a symmetric distribution a"""
    a = np.where(a >= ymin)[0]
    if len(a) >= 2:
        return 0.5*(a[0] + a[-1])
    else:
        return None


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


def plot_profile(image, profile_x, profile_y, beam_x, beam_y,
                 filename='fig.png', plot_circles=False,
                 correlation_x=None, indices_x=None,
                 correlation_y=None, indices_y=None):

    ny, nx = image.shape

    gs = gridspec.GridSpec(2, 2, top=0.95, bottom=0.07,
                           left=0.15, right=0.95,
                           wspace=0.0, hspace=0.0,
                           width_ratios=[2, 1],
                           height_ratios=[1, 3])
    ax_x = plt.subplot(gs[0, 0])
    ax_y = plt.subplot(gs[1, 1])
    ax = plt.subplot(gs[1, 0])

    nx_half = int(nx/2)
    ny_half = int(ny/2)
    width_xy = 200
    ax_x.set_xlim(nx_half-width_xy, nx_half+width_xy)
    ax_y.set_ylim(ny_half+width_xy, ny_half-width_xy)

    ax.set_xlim(nx_half-width_xy, nx_half+width_xy)
    ax.set_ylim(ny_half+width_xy, ny_half-width_xy)

    if (indices_x is not None) and (correlation_x is not None):
        correlation_x /= correlation_x.max()
        ax_x.plot(indices_x, correlation_x, c='C3')

    if (indices_y is not None) and (correlation_y is not None):
        correlation_y /= correlation_y.max()
        ax_y.plot(correlation_y, indices_y, c='C3')
    ax_x.set_ylim(0, 1.2)
    ax_y.set_xlim(0, 1.2)

    ax.set_xlabel(r'\rm Pixel index X')
    ax.set_ylabel(r'\rm Pixel index Y')

    ax.imshow(image, cmap='jet', aspect='auto',
              origin='upper', vmin=0, vmax=50,
              rasterized=True, interpolation='none')

    ax_x.plot(profile_x, c='C0', mew=0, ms=0.5, lw=1.0)

    yvals = np.arange(0, len(profile_y))
    ax_y.plot(profile_y, yvals, lw=0.5, c='C0')

    ax_x.axvline(beam_x, lw=0.5, c='C2')
    ax.axvline(beam_x, lw=0.5, c='white')

    ax_y.axhline(beam_y, lw=0.5, c='C2')
    ax.axhline(beam_y, lw=0.5, c='white')

    ax.plot([beam_x], [beam_y], marker='o', ms=1., c='white', lw=0)

    if plot_circles:
        radii = np.arange(50, 600, 25)
        for radius in radii:
            c = Circle((beam_x, beam_y), radius, facecolor='none',
                       edgecolor='white', lw=0.5, ls=(1, (2, 2)))
            ax.patches.append(c)

    ax_x.tick_params(labelbottom=False)
    ax_y.tick_params(labelleft=False)

    plt.savefig(filename, dpi=800)


if __name__ == '__main__':
    main()
