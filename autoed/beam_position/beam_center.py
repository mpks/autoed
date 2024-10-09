import h5py
import hdf5plugin
import numpy as np
import os
import autoed
from autoed.beam_position.midpoint_method import (MidpointMethodParams,
                                                  position_from_midpoint)
from autoed.beam_position.maximum_method import MaxMethodParams, find_max
from autoed.beam_position.plot import plot_profile
import argparse
import time


hdf5plugin


def main():

    info = 'A script to determine the beam center'
    parser = argparse.ArgumentParser(description=info)

    parser.add_argument('filename', help='The HDF5 input file.')
    parser.add_argument('-p', '--plot', action='store_true',
                        help='Plot results')
    msg = """
          Method used to determine the beam position.
          Options include: midpoint, maximum, and mixed.

          The mixed method combines midpoint and maximum method. It uses
          maximum for the x, and midpoint or maximum for the y direction.
          It first computes the beam position along the y direction using
          the midpoint method, and if the beam position outside of the
          beam stop (the central stripe in a Singla image) it switches to
          maximum.
          """

    choices = ['maximum', 'midpoint', 'mixed']
    parser.add_argument('--method', choices=choices,
                        default='midpoint', help=msg)

    parser.add_argument('--every', type=int, default=20,
                        help='Use `every` image when computing the average.')

    parser.add_argument('-s', '--stack', action='store_true',
                        help='Compute beam center from stacks')
    parser.add_argument('-a', '--all', action='store_true',
                        help='Compute beam center from all stacks')
    parser.add_argument('--title', type=str, default=None,
                        help='A title to put in the graph')
    args = parser.parse_args()

    cal = BeamCenterCalculator(args.filename)

    if cal.problem_reading:
        print(f"The data file {args.filename}\ncan not be read properly.")
        print("Aborting beam position calculation.")
        return

    if args.method == 'midpoint':

        x0, y0 = cal.center_from_midpoint(verbose=True,
                                          plot_file='beam_from_midpoint.png',
                                          every=args.every)
        print('From midpoint: (%.2f, %.2f)' % (x0, y0))

    elif args.method == 'mixed':

        x0, y0 = cal.center_from_mixed(every=args.every, title=args.title)

        print('From mixed: (%.2f, %.2f)' % (x0, y0))

    elif args.method == 'maximum':

        if args.stack or args.all:

            if args.all:
                ns = -1
            else:
                ns = 10

            bx, by = cal.centre_from_max(x0, y0, plot=args.plot,
                                         number_of_stacks=ns, verbose=True)

        print('From average: (%.2f, %.2f)' % (x0, y0))

    cal.file.close()


class BeamCenterCalculator:

    def __init__(self, filename):
        mask_path = 'data/singla_mask.npz'
        mask_path = os.path.join(autoed.__path__[0], mask_path)
        mask_data = np.load(mask_path)
        self.mask = mask_data['mask']

        index = 0
        self.problem_reading = True

        while index < 3:
            index += 1
            try:
                self.file = h5py.File(filename, 'r')
                self.dataset = self.file['/entry/data/data']
                self.problem_reading = False
                break
            except OSError:
                time.sleep(1)

    def center_from_midpoint(self, every=20, verbose=False, plot_file=None):

        image = self.dataset[::every, :, :].mean(axis=0)
        image[self.mask > 0] = 0

        mid_params = MidpointMethodParams(
            data_slice=(0.35, 0.9, 0.02),
            convolution_width=20,
            exclude_range_x=None,
            exclude_range_y=(510, 550),
            per_image=False)

        x0, y0, plot_params = position_from_midpoint(image, mid_params,
                                                     verbose=False,
                                                     plot_filename=plot_file)
        return x0, y0

    def center_from_mixed(self, every=20, bad_pixel_threshold=20000,
                          convolution_width=3,
                          plot_file=None, title=None):

        image = self.dataset[::every, :, :].mean(axis=0)
        image[self.mask > 0] = 0
        image[image > bad_pixel_threshold] = 0

        # First try midpoint method
        mid_params = MidpointMethodParams(
            data_slice=(0.35, 0.9, 0.02),
            convolution_width=20,
            exclude_range_x=None,
            exclude_range_y=(510, 550),
            per_image=False)

        x_mid, y_mid, plot_params = position_from_midpoint(image, mid_params,
                                                           verbose=False,
                                                           plot_filename=None)
        # Next, try maximum pixel method
        max_params = MaxMethodParams(convolution_width=convolution_width)
        data_x = find_max(image, max_params, axis='x')
        data_y = find_max(image, max_params, axis='y')

        line_max_x, line_smooth_x = data_x['profiles']
        line_max_y, line_smooth_y = data_y['profiles']

        line_max_y = flip_line(line_max_y)
        line_smooth_y = flip_line(line_smooth_y)

        i1_x, i2_x = data_x["bin_position"]
        i1_y, i2_y = data_y["bin_position"]

        x_max = data_x["beam_position"]
        y_max = data_y["beam_position"]

        if plot_file:
            plot_params.filename = plot_file
        else:
            plot_params.filename = 'beam_position.from_mixed.png'

        plot_params.label = title

        edge = 0
        if y_mid > 550 - edge or y_mid < 510 + edge:
            # The beam is visible, switch to maximum
            y = y_max
            x = x_max
            plot_params.profiles_y = [line_max_y, line_smooth_y]
            plot_params.profiles_x = [line_max_x, line_smooth_x]

            plot_params.label_x = 'method: maximum'
            plot_params.label_y = 'method: maximum'
        else:
            y = y_mid
            x = x_mid
            plot_params.label_y = 'method: midpoint'
            plot_params.label_x = 'method: midpoint'

        plot_params.beam_position = x, y

        if plot_file:
            plot_profile(plot_params)

        return x, y


def flip_line(line):

    x = np.array(line.x)
    y = np.array(line.y)

    line.y = x
    line.x = y

    return line


if __name__ == '__main__':
    main()
