
def centre_from_max(x0, y0, pixel_range=10,
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

