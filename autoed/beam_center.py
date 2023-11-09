#!/usr/bin/env python3
import h5py
import hdf5plugin
import numpy as np
import matplotlib.pyplot as plt
import sys
import matplotlib.gridspec as gridspec
from matplotlib.patches import Circle

hdf5plugin


def main():

    mask_data = np.load('../data/mask.npz')
    mask = mask_data['mask']

    file_path = sys.argv[1]
    with h5py.File(file_path, 'r') as h5_file:

        dataset = h5_file['/entry/data/data']
        avg_image = dataset[::100, :, :].mean(axis=0)
        avg_image[mask > 0] = 0
        avg_image[avg_image > 20000] = 0

        print('Computing max pixels')
        max_image = np.max(dataset[0:20, :, :], axis=0)
        max_image[max_image > 2000] = 2000
        print('Computation done')

        ny, nx = avg_image.shape

        profile_y, beam_y, cut_min, cut_max = find_beam_y(avg_image)
        profile_x, beam_x = find_beam_x(avg_image)

        # fig = plt.figure(figsize=(3, 3.0))
        # ax = fig.add_axes([0.13, 0.14, 0.84, 0.82])

        gs = gridspec.GridSpec(2, 2, top=0.95, bottom=0.07,
                               left=0.15, right=0.95,
                               wspace=0.0, hspace=0.0,
                               width_ratios=[2, 1],
                               height_ratios=[1, 3])
        ax_up = plt.subplot(gs[0, 0])
        axm = plt.subplot(gs[1, 0])
        ax_side = plt.subplot(gs[1, 1])
        ax_up.set_xlim(0, nx)
        axm.set_xlim(0, nx)
        ax_side.set_ylim(ny, 0)
        axm.set_ylim(ny, 0)
        ax_up.set_ylim(0, 1.2)
        ax_side.set_xlim(0, 1.2)
        axm.set_xlabel(r'\rm Pixel index X')
        axm.set_ylabel(r'\rm Pixel index Y')

        ax_side.axvspan(xmin=cut_min, xmax=cut_max,
                        ymin=0, ymax=ny,
                        color='#BEBEBE', alpha=0.5, lw=0)

        axm.imshow(max_image, cmap='jet', aspect='auto',
                   origin='upper', vmin=0, vmax=50,
                   rasterized=True, interpolation='none')

        ax_up.plot(profile_x, c='C0', mew=0, ms=0.5, lw=1.0)

        yvals = np.arange(0, len(profile_y))
        ax_side.plot(profile_y, yvals, lw=0.5, c='C0')

        ax_up.axvline(beam_x, lw=0.5, c='C3')
        axm.axvline(beam_x, lw=0.5, c='white')

        ax_side.axhline(beam_y, lw=0.5, c='C3')
        axm.axhline(beam_y, lw=0.5, c='white')
        print("BB", beam_x, beam_y)
        axm.plot([beam_x], [beam_y], marker='o', ms=1., c='white',
                 lw=0)

        radii = np.arange(50, 600, 50)
        for radius in radii:
            c = Circle((beam_x, beam_y), radius, facecolor='none',
                       edgecolor='white', lw=0.5, ls=(1, (2, 2)))
            axm.patches.append(c)

        ax_up.tick_params(labelbottom=False)
        ax_side.tick_params(labelleft=False)

        plt.savefig('fig.png', dpi=800)


def find_beam_x(avg_image):

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
    print('beam center x:', center)

    return avg_x, center


def find_beam_y(avg_image):

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

    sample = np.arange(0.2, 0.8, 0.01)
    sample = sample[np.where(np.logical_or(sample <= cut_min,
                                           sample >= cut_max))]
    mid_points = []
    for y_point in sample:
        mid_point = middle(avg_y, y_point)
        if mid_point:
            mid_points.append(mid_point)
    center = np.array(mid_points).mean()
    print('beam center y:', center)

    return avg_y, center, cut_min, cut_max


def middle(a, ymin):
    a = np.where(a >= ymin)[0]
    if len(a) >= 2:
        return 0.5*(a[0] + a[-1])
    else:
        return None


def smooth(a, half_width=1):

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


if __name__ == '__main__':
    main()
