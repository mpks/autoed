============================
Beam position methods
============================

``dials.search_beam_position`` searches
beam position in a set of diffraction images. There are four 
methods implemented in this function: default, maximum, midpoint, and
inversion. The default method is based on the work of *Sauter et al.*
(please see Ref. [`1 <sauter>`_]) and it is not covered
here. The other three methods are based on projecting diffraction images along
the *x* and the *y* axes, and we will briefly describe them here.


The three projection methods were developed to automate the 
processing of diffraction datasets produced at the DLS electron Bio-Imaging Centre
(eBIC). They are developed primarily for electron diffraction images,
although nothing prevents you from using them for other sources. They work
primarily in cases when the user can quickly determine the beam center just by
looking at a diffraction image, and they do not
rely on some profound mathematical truths. In other words, they are not a 'silver
bullet' to handle every dataset, but an *ad hoc* solution developed to work for
most of the datasets obtained at eBIC. The initial idea was to use the output
of these three methods to train machine learning models (with problematic
datasets labeled by hand in order to catch all the cases).

It is unlikely that any of the three methods presented here will work on your
data out of the box. Depending on the setup of your experiment, detector
resolution, position of the beam stop etc, you will have to tune method 
parameters to fit your experiment. However, once you find the correct
combination of parameters, the methods will work well for most your datasets.
In the first example below (processing with the maximum method) we will just
present the interface of the maximum method. In the second example, beside
explaining the interface of the midpoint method, we will give a step by step
explanation how we tuned the method parameters to work with the Singla data.

*********************************
Maximum pixel intensity method
*********************************
This is the simplest projection method, which is suitable for datasets where 
the beam is visible. Assuming we already imported our dataset with
``dials.import``, we can run the ``search_beam_position`` on the imported
experiment file

.. code-block:: console

   dials.search_beam_position method=maximum image_ranges=0:3 imported.expt


The ``search_beam_position`` command will compute the average diffraction 
image using the first three images in the dataset, and then compute the 
beam position using the maximum pixel intensity method. The 
output should be a single PNG image called ``beam_position.png`` 
(shown below, see Fig. 1).

.. figure:: ../figs/beam_position_maximum.png
   :alt: Beam position computed using maximum method 
   :width: 80%
   :align: center

   Beam position computed using the maximum pixel intensity method.
   Data provided by Peter Ercius from  Lawrence Berkeley National
   Laboratory.

The generated plot shows the average diffraction image in the central part
and two projected profiles along the *x*- and the *y*-direction in the top and
right plots, respectively. The beam position in pixels (rounded to
an integer) is shown in the top right, between the plotted graphs.
The plotted result has additional metadata, such as the image dimensions, the
minimal and maximal pixel intensity, etc. Note that all
projection methods work only for single-panel detectors (for now).

.. note::

   By default, the plotting function will try to adjust the colormap range to 
   show high intensity regions.
   However, in some datasets, the pixel intensities might be unevenly 
   distributed (imagine a dataset where the average pixel has an intensity
   between 0 and 10, but some bad pixels show intensities of several
   millions). In such cases, spotting the beam on the central image would be
   hard. If this is the case with your dataset, you can use the argument
   ``color_cutoff`` (for example, in the previously described case, you would
   ``set color_cutoff=10``) to set the maximum value of the colormap range.
   Setting this parameter will not change the original data; it will only 
   change how it is plotted. Pixels with intensities above the color cutoff 
   would be set to the same color. The ``color_cutoff`` also applies to other
   methods (inversion and midpoint) and is not limited to the maximum method.


When projecting data from a 2D image to 1D profiles, we can
either compute the average pixel intensity along an axis or 
find the maximal pixel along an axis (i.e., computing the maximal projection).
The previous figure shows both maximal and average projections along each axis.

Because the beam is visible, one can  find the pixel with maximum
intensity and declare that to be the beam position without any projecting.
However, this is not always correct. In some cases, bad pixels
will return the maximal intensity from the trusted range by default.
Also, there might be cases where the intensity of a reflection spot is higher
than the intensity at the direct beam. One condition usually
satisfied when the beam is visible is that the direct beam has the most
extensive spread compared to other diffraction spots.
Finding the broadest peak is a good starting point for computing the beam
position. The next step is determining the pixel with the highest intensity 
within that broadest peak. Projecting the diffraction image along the *x* and
the *y* is not necessary. However, it
dramatically simplifies the problem by reducing it to one dimension.
The downside is that there might be cases where strong
reflection spot masks the direct beam in the projected profile. 
Averaging over few images (as in our example above) usually removes this problem.

The first step in the maximum method is to find the broadest peak
in the projected profiles. This is done by scanning the average
projected profile (the green curves in Fig. 1) with an averaging kernel of a
certain width (see Fig. 2, below).

.. figure:: ../figs/max_method.png
   :alt: Explanation of the maximum method
   :width: 80%
   :align: center

   Parameters ``bin_width`` and ``bin_step`` of the maximum pixel intensity
   method.


The averaging kernel (the dark gray rectangle in Figure 2) sweeps over the
projected profile moving in discrete steps (determined by the ``bin_step``
parameter (in pixels)). The kernel size is set with the ``bin_width`` parameter
(again, in pixels). At each position during the sweep, the kernel computes the
integral sum of the average projected profile beneath the kernel (the
green area below the green curve in Figure 2). After sweeping the entire
profile and computing profile integrals, the maximum method determines the
kernel position where this integral has the maximal value. In general, this
will correspond to an area where most of the projected profile intensity is
located (the broadest peak). For a real-world example, see the gray shaded areas
in projected profiles in Fig. 1. These are kernel positions with maximal
integral, and they indeed correspond to the broadest peak. Depending on the
image dimensions, the beam characteristics, etc, the user will have to 
fine-tune the ``bin_step`` and ``bin_width`` parameters to match the expected
spread of the direct beam for the given experimental setup. To ensure the
continuous sweep across the projected profile, DIALS assumes that ``bin_step``
is always smaller than ``bin_width``, otherwise it will throw an error.

Note that most of the narrow reflection spots will disappear because we are
dealing with the average projected profile when determining the broadest peak.
The user can additionally remove narrow reflection peaks by increasing the
``maximum.convolution_width`` parameter, which sets the width of the
convolution smoothing window before the kernel sweep. Additionally, the user
can set all pixels above a certain intensity to zero in the average
diffraction image (that is, before projecting onto the *x* and *y*-axis). 
This is done using ``maximum.bad_pixel_threshold`` parameter.

The next step after locating the broadest peak is to find the
actual beam position. For this, we use the maximum projected profiles 
(the gray curves in Fig. 1). The maximum projected profile will contain peaks
from the reflections and the direct beam. The method will find a pixel with
the highest intensity within the previously determined maximum kernel
(the gray-shaded areas in the projected plots in Fig. 1). The previous
``maximum.bad_pixel_threshold`` argument
is applied to the central image before data is projected so that it will 
affect both projected profiles (average and maximum).


The ``image_ranges=0:3`` argument uses slicing like the Numpy
library, starting at the first image (index 0) up until the third image.
Image ranges are selected using the Numpy
slice notation, that is, ``start:stop:step``, where any of the three numbers 
can be omitted. Multiple image ranges can be separated by commas
(e.g.,  ``image_ranges=0:3,7:20:2,35,48``) which also
allows for the selection of individual images. The averaging procedure in the
current method is not fully optimized, so instead of waiting for thousands of
images to average, it is much faster to select only a subset of those images
(assuming the beam position does not change much throughout the dataset).
Similarly to the previous parameter, one can additionally use 
``imageset_ranges`` to select between different imagesets (if they are present
in the dataset).

Besides computing the average image and then making the projection, 
the user can compute beam position for each image separately
using ``per_image=True`` parameter. This will produce a series of PNG images.

.. code-block:: console

    beam_position_imageset_00000_image_00000.png
    beam_position_imageset_00000_image_00001.png
    beam_position_imageset_00000_image_00002.png
    beam_position_imageset_00000_image_00003.png
    ...

Each image will contain information about beam position. Additionally, if
``per_image=True``, DIALS will produce ``beam_positions.json`` file with
a list of computed beam positions


.. code-block:: console

    [
        [
            0,
            0,
            294.0,
            261.0
        ],
        [
            1,
            0,
            296.0,
            261.0
        ],
        ...
   ]

Here, the first number in the four-element list is the imageset index, 
the second is the image index, and the third and fourth are beam positions
along the *x* and *y* direction (in pixels). 
The JSON file will have beam positions for all
images and imagesets selected using ``image_ranges`` and ``imageset_ranges``.
In contrast to PNG images, the computed positions are not converted to 
integers (which is not that important for the maximum method, but it is for
the other two projection methods).

The user should also distinguish between method-specific parameters 
(such as ``bin_width`` and ``bin_step``) and parameters such as ``per_image``
and ``image_ranges``, which also apply to other projection methods as well
(see ``dials.search_beam_position -h`` for more info on the function
interface. The parameters that apply to all three projection methods
are under the ``projection`` keyword). Additionally, it is important to
emphasize that most parameters specific to the maximum method (and other
projection methods) apply both to projections along the *x* and the *y* axis
(the mini plots on the top and left in Fig. 1). Some parameters
apply separately to *x* and *y* projection, and we will discuss them below.


************************
Midpoint method
************************
This method is suitable for datasets where direct beam is blocked by some
obstacle (and not fully visible in the diffraction images). Fig. 3 presents
one such dataset (obtained at eBIC). A DECTRIS Singla detector consists of two
panels, with a gap between them. It is common for electron beam to be
positioned in this gap. Determining beam position based on the maximum pixel
intensity is not possible in this case (at least not along the *y*-direction)
because the beam peak is blocked.

.. figure:: ../figs/singla_image.png
   :alt: Singla diffraction image
   :width: 50%
   :align: center

   A diffraction image from DECTRIS Singla detector at eBIC.

First, let us run the midpoint method on this dataset without any parameters

.. code-block:: console

   dials.search_beam_position method=midpoint imported.expt

Because we did not provide ``per_image=True`` parameter, DIALS will go through
all the images in the dataset, compute the average image, project that image 
onto *x* and *y* axis, and compute the midpoints. The output of this command
is ``beam_position.png`` file.

.. figure:: ../figs/midpoint_01.png
   :alt: Midpoint method
   :width: 50%
   :align: center

   Beam position determined by the midpoint method.

.. figure:: ../figs/midpoint_method.png
   :alt: Midpoint method
   :width: 50%
   :align: center

   Beam position determined by the midpoint method.



************************
Inversion method
************************

This method is suitable for datasets where one can clearly see Friedel pairs.


.. _sauter:

   `[1] <https://journals.iucr.org/j/issues/2004/03/00/dd5008>`_
   Sauter et al., *J.Appl.Cryst.* **37**, 399-409 (2004).

