import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import h5py
import hdf5plugin
import os
import json
import argparse
from matplotlib.colors import LogNorm

description = """
 ===========================================
  AutoED plot the spots in a Singla dataset
 ===========================================

 A command to plot frame stacks (showing diffraction
 spots) from a Singla detector dataset. Run with

 $ autoed_plot_spots DIRECTORY

 Where the DIRECTORY is containing an original Singla HDF5
 data file (e.g. xyz_data_000001.h5) and the corresponding
 metadata file (e.g. xyz.json). To make the spots visible,
 the command will stack several frames together. Each pixel
 on the stacked frame gets the maximum intensity from all
 the intensities of that pixel in the stack.
 The
 number of frames in a single stack (the stack size) is
 determined from the metadata JSON file (if present in the
 DIRECTORY) and it is equal to the number of frames in a
 single degree of rotation. If the metada file is
 incomplete or missing, or the rotation increment is larger
 than a single degree, the stack size is set to be ten
 frames.

 Assuming there are N frames in a dataset, and the stack
 size is S, the command will produce four plots:
  - a stack [0, S-1] around the first frame
  - a stack [int((N-S)/2), int((N+S)/2)-1] around the
    middle frame
  - a stack [N-S, N-1] around the last frame
  - a stack of all images [0, N-1]
 and combine them in a single image ('spots.png'). Here,
 [a, b] stands for a closed interval (indexing starts at
 zero). If the stack size is larger than the total number
 of images in a dataset, all four plots will show stacks of
 all frames.

 The script produces two plots for each dataset:
 spots.png and spots_log10.png with linear and logarithmic
 (base 10) scaling of the pixel intensities.
"""

epilog = """
 ----------------------------------------------------------
 Note: When DIRECTORY contains more than a single dataset,
 the script will write an index for any additional dataset
 ('spots.png', 'spots_01.png', ...). The same applies for
 the logarithmic plots.
 ----------------------------------------------------------
"""

hdf5plugin

CUT_OFF_INTENSITY = 80   # Color cut-off intensity


def main():

    raw_formatter = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=description,
                                     epilog=epilog,
                                     formatter_class=raw_formatter)

    parser.add_argument("directory",
                        help='Name of the directory containing Singla data')

    msg = 'Stack size (number of frames). If provided, it overrides '
    msg += 'the default value (or the one from the metadata file.'
    parser.add_argument("-s", "--stack_size", default=None, type=int, help=msg)

    msg = 'Color cutoff intensity for the linear scale. Overrides the default.'
    parser.add_argument("-c", "--color_cutoff", default=None, type=int,
                        help=msg)
    msg = 'Color cutoff intensity for the log scale. Overrides the default.'
    parser.add_argument("-cl", "--color_cutoff_log", default=None, type=int,
                        help=msg)

    args = parser.parse_args()

    directory = args.directory

    success = True  # A return argument to check if command exited correctely

    hdf5_files = []
    metadata_files = []

    files_in_dir = os.listdir(directory)

    for file in files_in_dir:

        if file.endswith("_data_000001.h5"):

            print(f" Found dataset:  {file}")
            hdf5_full_path = os.path.join(directory, file)
            hdf5_files.append(hdf5_full_path)

            # Check if there is an acompanying metadata file
            metadata_file = file.replace("_data_000001.h5", ".json")
            if metadata_file in files_in_dir:
                print(f" Found metadata: {metadata_file}")
                metadata_full_path = os.path.join(directory, metadata_file)
                metadata_files.append(metadata_full_path)
            else:
                metadata_files.append(None)

    if len(hdf5_files) == 0:
        print(" No Singla datasets found in {directory}")
        print(" By convention, a Singla dataset ends with '_data_000001.h5'")
        return not success

    zip_files = zip(hdf5_files, metadata_files)
    for index, (hdf5_file, metadata_file) in enumerate(zip_files):

        print(50*'-')
        print(f" Loading dataset: {hdf5_file}")

        with h5py.File(hdf5_file, "r") as f:
            dataset = f['/entry/data/data']
            images = dataset[()]

        n_images, ny, nx = images.shape

        print(f' There are {n_images} images in the dataset')
        print(f' Setting cutoff intensity: {CUT_OFF_INTENSITY}')

        # Set the default frame stack size
        stack_size = 10

        # Check if the metadata file overwrites the stack size
        if metadata_file:
            print(' Loading metadata to determine the stack size')
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            if 'rotation_speed' in metadata and 'frame_rate' in metadata:
                rotation_speed = float(metadata["rotation_speed"])  # deg / sec
                print(f' Rotation speed: {rotation_speed} (deg / sec)')
                frame_rate = float(metadata["frame_rate"])    # frames / sec
                print(f' Frame rate: {frame_rate} (frames / sec)')

                # number of frames per degree
                stack_size = int(frame_rate / rotation_speed)
        else:
            print(' No metadata file. Setting the stack size to default value')

        if args.stack_size:
            print(' Overwritting the stack size from the command line')
            stack_size = args.stack_size

        if (stack_size > n_images):
            print(' Stack size larger than total number of frames')
            print(' Resizing stack size to fit the data')
            stack_size = n_images

        print(f' Stack size: {stack_size} (frames / deg)')

        plot_spots(images, hdf5_file, stack_size, n_images, index,
                   args, log_scale=False)

        plot_spots(images, hdf5_file, stack_size, n_images, index,
                   args, log_scale=True)

        print(50*'-')


def plot_spots(images, dataset_name, stack_size, n_images, index, args,
               log_scale=False):

    # Define stack ranges for four images to plot
    stack_ranges = []
    stack_ranges.append([0, stack_size])
    stack_ranges.append([int((n_images-stack_size)/2),
                         int((n_images+stack_size)/2)])
    stack_ranges.append([n_images-stack_size, n_images])
    stack_ranges.append([0, n_images])

    fig = plt.figure(figsize=(6, 6))

    gs = gridspec.GridSpec(2, 2, top=0.85, bottom=0.07,
                           left=0.07, right=0.95,
                           wspace=0.0, hspace=0.0)

    cax = fig.add_axes([0.07, 0.90, 0.88, 0.03])

    ax1 = plt.subplot(gs[0, 0])
    ax2 = plt.subplot(gs[0, 1])
    ax3 = plt.subplot(gs[1, 0])
    ax4 = plt.subplot(gs[1, 1])

    ax1.tick_params(labelbottom=False)
    ax2.tick_params(labelbottom=False)

    ax2.tick_params(labelleft=False)
    ax4.tick_params(labelleft=False)

    epsilon = 1   # Log scale does not work well with zeros

    plt.text(0.07, 0.99, 'dataset: ' + dataset_name, color='black',
             va='top', ha='left', transform=fig.transFigure)
    plt.text(0.07, 0.96, f'stack size: {stack_size}', color='black',
             va='top', ha='left', transform=fig.transFigure)
    plt.text(0.27, 0.96, f'N images: {n_images}', color='black',
             va='top', ha='left', transform=fig.transFigure)

    axes = [ax1, ax2, ax3, ax4]
    for i, (stack_range, ax) in enumerate(zip(stack_ranges, axes)):

        start, stop = stack_range

        image = images[start:stop].max(axis=0)

        cut_intensity = CUT_OFF_INTENSITY

        if log_scale:
            min_int = image.min()
            image = image - min_int + epsilon
            # image = np.log10(image)

            cut_intensity = 4.0*(CUT_OFF_INTENSITY)
            if args.color_cutoff_log:
                cut_intensity = args.color_cutoff_log

            img = ax.imshow(image, cmap="jet", aspect="auto", origin="lower",
                            rasterized=True, interpolation="none",
                            norm=LogNorm(vmin=epsilon, vmax=cut_intensity))
            plt.text(0.50, 0.96, f'color cutoff: {cut_intensity}',
                     color='black', va='top', ha='left',
                     transform=fig.transFigure)
        else:

            if args.color_cutoff:
                cut_intensity = args.color_cutoff

            img = ax.imshow(image, cmap="jet", aspect="auto", origin="lower",
                            rasterized=True, interpolation="none",
                            vmin=0, vmax=cut_intensity)

            plt.text(0.50, 0.96, f'color_cutoff: {cut_intensity}',
                     color='black', va='top', ha='left',
                     transform=fig.transFigure)

        plt.colorbar(img, cax, orientation='horizontal')

        label = f"frames: {start} - {stop-1}"

        imax = int(image.max())
        iavg = int(image.mean())
        if log_scale:
            label_color = 'black'
            imax = imax - 1
            iavg = iavg - 1
        else:
            label_color = 'white'

        ax.text(0.05, 0.97, label, color=label_color,
                va='top', ha='left', transform=ax.transAxes)
        ax.text(0.70, 0.97, f'max: {imax}', color=label_color,
                va='top', ha='left', transform=ax.transAxes)
        ax.text(0.70, 0.91, f'avg: {iavg}', color=label_color,
                va='top', ha='left', transform=ax.transAxes)

    file_name = 'spots'

    for ax in axes:
        ax.set_xlim(250, 750)
        ax.set_ylim(250, 750)

    ax1.set_yticks([300, 400, 500, 600, 700])
    ax3.set_yticks([300, 400, 500, 600, 700])
    ax3.set_xticks([300, 400, 500, 600, 700])
    ax4.set_xticks([300, 400, 500, 600, 700])

    if log_scale:
        file_name += '_log'

    if index > 0:
        file_name += '_{index-1:03d}'
    file_name += '.png'

    print(f' Saving figure: {file_name}')
    plt.savefig(file_name, dpi=400)

    plt.close(fig)


if __name__ == '__main__':
    main()
