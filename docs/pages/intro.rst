============================
Installation
============================

The AutoED package is available through Python's package manager.
To install it, run

.. code-block:: console

   pip install autoed

Use :code:`autoed -h` to see its full options list.
The main idea behind the package is to monitor directories with diffraction 
images, to register and process new files obtained from the eBIC microscope.

Usage
^^^^^^

First, start the daemon process.

.. code-block:: bash

   autoed start

Next, start watching a directory.

.. code-block:: bash

   autoed watch /path/to/diffraction/data

This will create a subprocess that runs separately from the
AutoED daemon. The watchdog process monitors all subdirectories within the
given path (recursively). 

You can list currently watched directories with

.. code-block:: bash

    autoed list

which will give you a list of all the watchdog processes, their process
identifier number (PID), and the path to the directory being watched. 

.. code-block:: bash

    Listing watched directories
    PID    PATH
    ------------------------------------------
    430056  /home/.../.../dir1
    882356  /home/.../.../dir2
    ------------------------------------------

    * Please use 'autoed kill PID' to kill a process.
      Alternatively you can use 'pkill -P PID'.
 
As the output says, you can terminate a watchdog script using its PID. For
example, 

.. code-block:: bash

   autoed kill 430056

to stop watching the first directory. Alternatively, you can run 

.. code-block:: bash

    autoed stop 

to kill all the watchdog processes and terminate the autoed daemon.
    


.. important::

   AutoED uses :code:`inotify` to monitor the filesystem. 
   Unfortunately, :code:`inotify` does not work on Network File Systems (NFSs).
   Because of this, AutoED uses the polling method in :code:`inotify`. The
   disadvantage of the polling method is that it might require more
   computational resources. If you are working on a local filesystem, you can
   run the watch command with an option :code:`--inotify` or :code:`-i` to use
   :code:`inotify` without polling (which is the default).

   To minimize CPU usage, you can set the time interval (in seconds) for 
   filesystem checks. Use :code:`--time_sleep` or :code:`-t`. For example,

    .. code-block:: bash

       autoed --time_sleep 60 watch /path/to/diffraction/data

   would check the filesystem every minute.
