============================
Installation and usage
============================

The AutoED package is available though Python's package manager.
To install it run

.. code-block:: console

   pip install autoed

To see the list of AutoED options and commands, run :code:`autoed -h`.
The main idea behind the auto-processing package is to watch 
directories with diffraction data, register changes 
within those directories, and use those changes to trigger the
data processing.

The first step in running AutoED is to start the daemon process.

.. code-block:: bash

   autoed start

Next, we can start watching a directory.

.. code-block:: bash

   autoed watch /path/to/diffraction/data

This will create a subprocess that runs separately from the AutoED
daemon, with only purpose to watch and process
files within a single directory (recursively). A user can place all
data in a single directory, and watch just that one, or distribute
data in different places and watch those separately. 


.. important::

   AutoED uses :code:`inotify` to watch the filesystem. 
   Note that :code:`inotify` does not work on.
.. Maybe smaller directories require less processing with inotify
