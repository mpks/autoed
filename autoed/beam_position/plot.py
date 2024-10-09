"""Helper functions used to determine the beam position of the imported data"""

from __future__ import annotations

from typing import List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass
from matplotlib import gridspec
from matplotlib.patches import Circle

matplotlib.use('Agg')


@dataclass
class Line2D:
    """ "Object used to hold matplotlib lines"""

    x: np.ndarray                     # x values
    y: np.ndarray                     # y values
    c: str = "C0"                     # Color
    lw: float = 0.5                   # Line width (pt)
    marker: str = None                # Marker
    ms: float = 1.0                   # Marker size


@dataclass
class PlotParams:
    """
    Object used to hold plot parameters

    Note
    ----
    span_xy: (xmin, xmax, ymin, ymax) highlighted regions in x and y directions
    """

    image: np.ndarray
    profiles_x: List[Line2D]  # Lines to plot on x-projected graph
    profiles_y: List[Line2D]  # Lines to plot on y-projected graph
    beam_position: Tuple[float, float]
    span_xy: Optional[Tuple[float, float, float, float]]  # Highlighted region
    filename: str = "fig.png"
    label: str = None
    label_x: str = None
    label_y: str = None
    mask: Optional[np.ndarray] = None


def decorate_plot(image: np.ndarray,
                  ax: matplotlib.axes.Axes,
                  ax_x: matplotlib.axes.Axes,
                  ax_y: matplotlib.axes.Axes,
                  beam_position: Tuple[float, float]) -> None:
    """Decorate a plot"""

    ny, nx = image.shape
    nx_half = int(nx / 2)
    ny_half = int(ny / 2)
    width_x = int(nx / 2)
    width_y = int(ny / 2)

    ax.set_xlim(nx_half - width_x, nx_half + width_x)
    ax.set_ylim(ny_half - width_y, ny_half + width_y)

    ax_x.set_xlim(nx_half - width_x, nx_half + width_x)
    ax_y.set_ylim(ny_half - width_y, ny_half + width_y)

    beam_x, beam_y = beam_position
    ax_x.set_ylim(-0.15, 1.2)
    ax_y.set_xlim(-0.15, 1.2)
    ax.set_xticks([0, 200, 400, 600, 800])

    ax.set_xlabel(r"Pixel index X")
    ax.set_ylabel(r"Pixel index Y", labelpad=5)

    # Mark the beam position with a dot
    ax.plot([beam_x], [beam_y], marker="o", ms=1.0, c="white", lw=0)

    # Plot circles around the beam center
    for radius in np.arange(50, 1000, 100):
        c = Circle(
            (beam_x, beam_y),
            radius,
            facecolor="none",
            edgecolor="white",
            lw=0.5,
            ls=(1, (2, 2)),
        )
        ax.add_patch(c)

    ax_x.tick_params(labelbottom=False)
    ax_y.tick_params(labelleft=False)

    ax_x.axvline(beam_x, lw=0.5, c="C2")
    ax.axvline(beam_x, lw=0.5, c="white")

    ax_y.axhline(beam_y, lw=0.5, c="C2")
    ax.axhline(beam_y, lw=0.5, c="white")


def plot_profile(params: PlotParams):
    """
    Plots the given profiles along with an image and saves the plot
    as a PNG file.
    """

    fig = plt.figure(figsize=(6, 6))
    gs = gridspec.GridSpec(2, 2, top=0.92, bottom=0.07, left=0.11, right=0.98,
                           wspace=0, hspace=0, width_ratios=[3, 1],
                           height_ratios=[1, 3])
    ax_x = plt.subplot(gs[0, 0])
    ax_y = plt.subplot(gs[1, 1])
    ax = plt.subplot(gs[1, 0])

    if params.span_xy is not None:
        if len(params.span_xy) != 4:
            raise ValueError("span_xy should be a tuple of four numbers")
        i1, i2, j1, j2 = params.span_xy
        ax_x.axvspan(i1, i2, color="#BEBEBE", alpha=0.5)
        ax_y.axhspan(j1, j2, color="#BEBEBE", alpha=0.5)

    ax.imshow(params.image, cmap="jet", aspect="auto", origin="lower",
              rasterized=True, interpolation="none")

    bx, by = params.beam_position
    ax_x.text(0.0, 1.05, f"beam position xy = ({bx:.0f}, {by:.0f})",
              transform=ax_x.transAxes, fontfamily='serif',
              fontsize=10)
    if params.label:
        ax_x.text(0.11, 0.99, f"dataset: {params.label}", va='top', ha='left',
                  transform=fig.transFigure, fontsize=8,
                  fontfamily='sans-serif')

#    ax_x.text(0.4, 1.05, f"max: {params.image.max():.2f}",
#              transform=ax_x.transAxes)
#    ax_x.text(0.9, 1.05, f"avg: {params.image.mean():.2f}",
#              transform=ax_x.transAxes)

    # Plot projected profiles
    for px in params.profiles_x:
        ax_x.plot(px.x, px.y, c=px.c, lw=px.lw, ms=px.ms, marker=px.marker)
    for py in params.profiles_y:
        ax_y.plot(py.x, py.y, c=py.c, lw=py.lw, ms=py.ms, marker=py.marker)

    decorate_plot(params.image, ax, ax_x, ax_y, params.beam_position)

    if params.label_x:
        ax_x.text(0.01, 0.97, params.label_x, va='top', ha='left',
                  transform=ax_x.transAxes)

    if params.label_y:
        ax_y.text(0.97, 0.97, params.label_y, va='top', ha='right',
                  transform=ax_y.transAxes, rotation=-90)

    plt.savefig(params.filename, dpi=400)
    plt.close(fig)
