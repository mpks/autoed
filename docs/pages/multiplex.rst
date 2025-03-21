AutoED multiplex
================

The xia2 multiplex command combines several successful integrated
results into one. The AutoED multiplex uses only the results of a
single pipeline (usually the ``default`` pipeline). 

- The multiplex processing is triggered every time the dedicated
  pipeline (e.g., the ``default``) updates the AutoED automatic
  report.  Triggering the multiplex does not necessarily mean the
  xia2 multiplex command will run.

- The AutoED will first determine to which sample the triggering
  dataset belongs (for more on samples, see below) and check if the
  percentage of indexed spots is above a certain threshold (see
  ``multiplex_indexing_percent_threshold`` parameter in the global
  configuration file). 

- If the dataset is high quality (above the indexing threshold), 
  the AutoED will add it to its list of samples to process with 
  multiplex. The multiplex command runs on every fifth dataset added 
  (this can be modified with the ``multiplex_run_on_every_nth``
  parameter in the configuration file). Note that this does not mean
  multiplex will run on every fifth measured dataset but on every
  fifth high-quality dataset for a given sample.

Multiplex samples
.................

Based on datasets processed so far, AutoED makes few assumptions
about how diffraction files are structured. A typical path of a
single dataset looks like this.

.. code-block:: console

    /../ED/SAMPLE_DIRS/CRYSTAL_DIR/SWEEP_DIR/DATA_master.h5

Here, ``ED`` is the data root directory (a directory where AutoED 
looks for diffraction images). The assumption is that there is only one 
data root directory in a dataset path (a complete path of a master
file). ``CRYSTAL_DIR`` is a directory where we keep diffraction 
data obtained from individual crystals. These directories usually 
start with a date (e.g., ``20240521_nav22_...``). A 
``CRYSTAL_DIR`` can contain one or more ``SWEEP_DIR``-s 
(e.g. ``sweep0``, ``sweep1``, ``sweep2``, etc). 
The assumption is that everything between the ``ED`` directory and 
the ``CRYSTAL_DIR`` is a grouping of different samples.

For example, if we have the following structure

.. code-block:: console

    ../ED/sample_01/20250215_nav15_124.543.22/sweep0/...master.h5
    ../ED/sample_02/20250215_nav11_172.255.33/sweep0/...master.h5

AutoED assumes we are dealing with two different samples. You can 
have as many directories for sample grouping as you like, so
something like this.

.. code-block:: console

    ED/abc/123/sample_02/20250215_nav11_.../sweep0/...master.h5

is treated as a sample.

The structure of the sample directories is copied into the multiplex
directory. In the case when crystal directories are placed directly
in the ED data root

.. code-block:: console

    ../ED/20250215_nav7.../sweep0/...master.h5
    ../ED/20250216_nav5.../sweep0/...master.h5

These crystals would be assigned to the default sample, and
the output of their processing would be in 
``multiplex/default_sample``.
