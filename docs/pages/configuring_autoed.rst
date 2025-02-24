============================
Configuring AutoED
============================

AutoED provides a way to configure some of its main features using a
configuration file. The first step in configuring AutoED is to generate a
default configuration file by running

.. code-block:: console

    autoed_generate_config

This command will create a JSON file called ``autoed_config.json`` with the
list of global configuration parameters. To enable AutoED to find the
configuration file, you need to set an environment variable called
``AUTOED_CONFIG_FILE`` to point to it. If you saved your AutoED config file in
your home directory, add a command

.. code-block:: console

    export AUTOED_CONFIG_FILE=~/autoed_config.json

in your .bashrc. When you set the environment variable, you can edit your 
configuration file using it (e.g. ``vim $AUTOED_CONFIG_FILE``, or use
``nano`` instead of ``vim``).

AutoED will list global configuration variables in its log file. It is
essential to understand how global variables are set. The default values are
those you see when you generate the configuration file. Any variable you
change in your configuration file will overwrite the default one. AutoED will
only log those variables that you changed. Additionally, some variables in
the configuration file can be set via the command line when you call the
AutoED watch command (e.g., ``autoed --inotify watch`` would set the option
``inotify`` to ``True``). In that case, the option from the command line will
overwrite both the default and the one set in the user configuration file.
Again, this change will be recorded in the log file. In case you set the
parameter ``dummy`` to ``true`` (either in the global config file or on the
command line) AutoED will assume you are running tests, and will reset all the
parameters (except ``dummy``) to their default values.


A list of global parameters (their default value) and their description is given below. 

   - ``inotify: false`` 

     If set to ``false``, AutoED will run the watchdog scripts
     with the polling method. If set to ``true``, AutoED will use 
     ``inotify``. For more details, see the 
     :ref:`note <inotify-note>` on ``inotify``.
   - ``sleep_time: 1.0`` 

     When AutoED monitors the filesystem, it checks for the existence of a
     trigger file in fixed time intervals. This parameter sets the time
     between two filesystem checks (in seconds). 

   - ``dummy: false`` 

     To process each dataset, AutoED creates a processing script (with DIALS or
     xia2 commands) and executes them. If this parameter is set to ``true``,
     AutoED will create the processing scripts, but it will not execute them.

   - ``test: false`` 

     Similar to ``dummy``, except if you set it to ``true`` AutoED will 
     assume you are running tests, and will reset all the other global
     parameters to their default values.

   - ``local: false``

     If ``true``, execution of the processing scripts is done locally, on the
     same machine we run AutoED. If ``false``, processing scripts will be
     executed remotely (using a SLURM submission to the Diamond cluster). 

   - ``log_dir: null``
    
     This parameter sets the location where the global ``autoed_watch.log``
     file is put. If not set, the log file is created in the watched
     directory. 

   - ``gain: 1.0``
    
     Sets the gain in xia2/DIALS processing. 

   - ``overwrite_mask: false``
    
     AutoED has a custom mask for the Singla detector at eBIC. The mask was
     not written in the output files during the initial microscope setup. The
     mask had to be overwritten manually before processing. Data masking has
     been fixed on the microscope, so overwriting the mask is now obsolete.
     However, there is still an option to control it.

   - ``trigger_file: .HiMarko``
    
     Name of the file that triggers the dataset processing.
    
   - ``ed_root_dir: ED``

     Name of the root directory where ED data is located. This directory is
     needed because the processed and report directories are created at the
     same level.

   - ``processed_dir: processed``

     Name of the directory where to keep the processed results (xia2 log
     files and reports).

   - ``run_pipelines: {"default": true, "user": true, ...}``

     A dictionary that sets which pipelines to run. Only the pipelines in this
     dictionary set to ``true`` will be executed.
