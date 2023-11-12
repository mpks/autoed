#!/usr/bin/env python3
import time
# import subprocess
import autoed
import os
import sys
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .dataset import SinglaDataset
from .misc_functions import overwrite_mask

"""
A watchdog script that watches a directory for file changes.
The script checks, converts and processes the electron diffraction
data if present.

Run with:
autoed_watch directory_name
"""

WRITE_STATUS_EVERY = 2     # Status will be saved every 2 minutes
queue_time_sec = 1         # Time before all files present and processing


def main():
    if len(sys.argv) == 2:
        input_dir = sys.argv[1]
        watch_path = os.path.abspath(input_dir)
        if not os.path.exists(watch_path):
            msg = f'Path {watch_path} does not exist.'
            raise FileNotFoundError(msg)
    else:
        msg = 'autoed_watch requires a single argument'
        msg += ' (watch directory)'
        raise IOError(msg)

    processing_script = os.path.join(autoed.__path__[0], 'process.py')

    event_handler = DirectoryHandler(watch_path, processing_script)
    observer = Observer()
    observer.schedule(event_handler, watch_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)

            # Process all the queued datasets
            to_process = []
            current_time = time.time()
            for key in event_handler.queue.keys():
                if (current_time - event_handler.queue[key]) >= queue_time_sec:
                    to_process.append(key)
            for key in to_process:
                dataset = event_handler.datasets[key]
                event_handler.queue.pop(key)
                dataset.process()

    except KeyboardInterrupt:
        observer.stop()
    observer.join()


class DirectoryHandler(FileSystemEventHandler):

    def __init__(self, watch_path, script):

        """
        Parameters
        ----------
        watch_path : Path
            The path of the directory to be watched.

        script : Path
            The path to the processing script used to
            convert and process data.
        """

        self.watch_path = watch_path
        self.status_file = os.path.join(watch_path, '.autoed_status.txt')
        self.dataset_names = set()
        self.datasets = dict()
        self.queue = dict()

        self.script = script
        self.last_triggered = 0

    def on_created(self, event):

        if not event.is_directory:
            # print('New file detected: ', event.src_path)
            is_logfile = re.match(r".*\.log$", event.src_path)
            is_autoedlog = re.match(r".*\.autoed\.log$", event.src_path)
            is_nexgenlog = re.match(r".*EDnxs\.log$", event.src_path)
            is_masterfile = re.match(r".*\.__master\.h5$", event.src_path)
            is_datafile = re.match(r".*\.__data_\d{6}\.h5$", event.src_path)
            is_mdocfile = re.match(r".*\.mdoc", event.src_path)

            dataset = None
            basename = None

            if is_logfile and not is_autoedlog and not is_nexgenlog:
                basename = event.src_path[:-4]
            if is_masterfile:
                basename = event.src_path[:-12]
                time.sleep(1)
                overwrite_mask(event.src_path)
            if is_datafile:
                basename = event.src_path[:-17]

            if basename:
                if basename not in self.dataset_names:  # Add a new dataset
                    self.dataset_names.add(basename)
                    dataset = SinglaDataset.from_basename(basename)
                    self.datasets[dataset.base] = dataset

                else:                          # Get an existing dataset
                    dataset = self.datasets[basename]

                if is_datafile:
                    dataset.data_files.append(event.src_path)

            if is_mdocfile:      # Check if there is an existing dataset
                mdoc_filename = os.path.basename(event.src_path)
                mdoc_filename = mdoc_filename[:-11]   # Remove ._.mrc.mdoc
                date_str = mdoc_filename[0:9]
                rest = mdoc_filename[9:]
                base_pattern = r".*" + date_str + r"\d{4}_" + rest
                matched_datasets = [ds for ds in self.dataset_names if
                                    re.match(base_pattern, ds)]
                if matched_datasets:
                    # Currently we assume there is only one mdoc
                    # file for each dataset. This might change in the future
                    dataset = self.datasets[matched_datasets[0]]

            if dataset:
                if dataset.all_files_present():
                    self.queue[dataset.base] = time.time()

    def on_modified(self, event):
        current_time = time.time()
        if (current_time - self.last_triggered) > 1:
            self.last_triggered = current_time
            if not event.is_directory:
                # print('File modified', event.src_path)
                pass


if __name__ == "__main__":
    main()
