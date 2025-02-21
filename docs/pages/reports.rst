==================
AutoED reports
==================

AutoED reports are files that give an overview of the data processing
statistics. These files are generated automatically as the data is being
processed. The reports are saved in the report directory (i.e.,
``autoed_report``). For each watched directory, the report directory appears
at the same level as the data root directory (e.g., the ED directory) and the
directory for the processed results. Currently, reports are available as a
single HTML file or two textual (``txt``) files. If you look inside
``autoed_report``, you might find something like this

.. code-block:: console

    report_data
    report.html
    report_sorted.txt
    report.txt
    server

The ``report_data`` is a directory where we keep all the relevant data 
necessary to generate an HTML report (e.g., beam position figures, xia2
reports, etc). The ``report.html`` is not a static HTML page. Therefore, you
need to start a local HTTP server to view it. Run the ``server`` script

.. code-block:: console

    server

This command will start a server on a local port 8000. You can see the 
generated report in your browser at http://localhost:8000/report.html.
To kill the HTTP server when you finish viewing, run

.. code-block:: console

    server stop

Your browser must run on the same machine where the report is located. So, if
you are on a Diamond filesystem, you must access a
`remote desktop using NoMachine <https://www.diamond.ac.uk/Users/Experiment-at-Diamond/IT-User-Guide/Not-at-DLS/Nomachine.html>`_. 
Another option is downloading the AutoED report directory to your
local machine and running the server there.  

If you want to view multiple reports: 

- You can always start another server at a different port 
  (e.g., port 8001) with

  .. code-block:: console

     server 8001

  and then go to http://localhost:8001/report.html. 

- You can run a server on the default 8000 port, which will overwrite 
  your previous report. You might need to refresh your browser to see 
  the new report (e.g., for Firefox on Ubuntu, the refresh is ``<ctrl-F5>``).  


If viewing the HTML report is too complicated, you can view the textual
report. There are two plain text files with processing statistics.
``report.txt`` will give you a chronological list of datasets as they are
processed (stored in the database). On the other hand, ``report_sorted.txt``
will provide you with a list of only those datasets that were processed
successfully and ordered according to the percentage of indexed points.   

The textual reports are concise because they do not provide the results from
all the pipelines. Instead, they pick a pipeline with the highest percentage
of indexed spots and only list that one.

