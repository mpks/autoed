def x_from_midpoint(avg_image):

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


def y_from_midpoint(avg_image):

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
