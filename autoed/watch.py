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
import logging

"""
A watchdog script that watches a directory for file changes.
The script checks, converts and processes the electron diffraction
data if present.

Run with:
autoed_watch directory_name
"""

# There is a minimal requirement for conversion:
# all files (mdoc, log, data and master) must be present in a directory.
# However, this is a minimal set. Imagine there are two data files.
# The apearance of the first might trigger the processing. That is
# why there is a queue where we wait for other data files to appear.
# If they do not appear after some period, the data is processed.
queue_time_sec = 2


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

    watch_logger = set_watch_logger(watch_path)

    event_handler = DirectoryHandler(watch_path,
                                     processing_script,
                                     watch_logger)
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
                watch_logger.info('Processing dataset: %s' % dataset.base)
                dataset.process()
                watch_logger.info('Finished processing %s' % dataset.base)

    except KeyboardInterrupt as e:
        watch_logger.exception(str(e))
        observer.stop()
    except Exception as e:
        watch_logger.exception(str(e))
        observer.stop()
    observer.join()


class DirectoryHandler(FileSystemEventHandler):

    def __init__(self, watch_path, script, logger):

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
        self.logger = logger

        self.script = script
        self.last_triggered = 0
        self.last_detected = dict()

    def on_created(self, event):

        if not event.is_directory:

            # Prevent the same file to trigger the processing
            # if event.src_path not in self.last_triggered:

            is_logfile = re.match(r".*\.log$", event.src_path)
            is_autoedlog = re.match(r".*\.autoed\.log$", event.src_path)
            is_nexgenlog = re.match(r".*EDnxs\.log$", event.src_path)
            is_masterfile = re.match(r".*_master\.h5$", event.src_path)
            is_datafile = re.match(r".*_data_\d{6}\.h5$", event.src_path)
            is_mdocfile = re.match(r".*\.mdoc", event.src_path)
            is_patchfile = re.match(r".*PatchMaster.sh$", event.src_path)
            filename = os.path.basename(event.src_path)
            is_dosfile = filename.startswith('dos_')

            dataset = None
            basename = None

            # Process only events that happened in ED directory
            if 'ED' in event.src_path.split(os.path.sep):

                if is_logfile and not is_autoedlog and not is_nexgenlog:
                    basename = event.src_path[:-4]    # .log
                    self.logger.info('Detected log file: %s' % event.src_path)
                if is_masterfile:
                    basename = event.src_path[:-10]   # Remove _master.h5
                    time.sleep(1)
                    self.logger.info('Detected master file: %s'
                                     % event.src_path)
                if is_datafile:
                    self.logger.info('Detected data file: %s'
                                     % event.src_path)
                    basename = event.src_path[:-15]  # rm _data_######.h5
                if is_mdocfile:
                    self.logger.info('Detected mdoc file: %s'
                                     % event.src_path)
                    basename = event.src_path[:-9]   # Remove .mrc.mdoc

                if basename and not is_dosfile:
                    if (basename not in self.dataset_names
                       and not is_logfile):  # Add a new dataset
                        self.dataset_names.add(basename)
                        dataset = SinglaDataset.from_basename(basename)
                        self.datasets[dataset.base] = dataset
                    else:                          # Get an existing dataset
                        if basename in self.dataset_names:
                            dataset = self.datasets[basename]

                    if is_datafile:
                        if event.src_path not in dataset.data_files:
                            dataset.data_files.append(event.src_path)

                # The patchfile has a generic name PatchMaster.sh, so we can
                # not get a specific name of the dataset. However, if there
                # is an existing dataset in a given directory, we can take that
                # one. Note that this will take only the first dataset and
                # it won't work if there are several datasets in a directory
                # Also, if there is not dataset in the directory, then we
                # don't care (the patch file is probably copied first).
                if is_patchfile:
                    self.logger.info('Detected PatchMaster file: %s'
                                     % event.src_path)
                    patch_dir = os.path.dirname(event.src_path)
                    for key in self.datasets:
                        td = self.datasets[key]
                        if td.path == patch_dir:
                            dataset = td
                            self.logger.info('Patch file triggered dataset %s'
                                             % dataset.base)
                            break

                if dataset:
                    present_lock = bool(dataset.present_lock)
                    if not present_lock:
                        self.logger.info('Checking if all files present: %s'
                                         % dataset.base)
                        if dataset.all_files_present():
                            self.logger.info('All files present: %s'
                                             % dataset.base)
                            self.queue[dataset.base] = time.time()
                        else:
                            self.logger.info('Not all files present: %s'
                                             % dataset.base)
                    else:
                        msg = 'Ignoring file, data already in queue: %s'
                        self.logger.info(msg % dataset.base)

    def on_modified(self, event):
        current_time = time.time()
        if (current_time - self.last_triggered) > 1:
            self.last_triggered = current_time
            if not event.is_directory:
                # print('File modified', event.src_path)
                pass


def set_watch_logger(watch_path):

    auto_logger = logging.getLogger(__name__)
    auto_logger.setLevel(logging.DEBUG)
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.DEBUG)

    autoed_log_path = os.path.join(watch_path, 'autoed_watch.log')
    # Clean log file
    with open(autoed_log_path, 'w'):
        pass
    file_handler = logging.FileHandler(autoed_log_path)
    file_handler.setLevel(logging.DEBUG)
    fmt = '%(asctime)s.%(msecs)03d %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt, datefmt='%d-%m-%Y %H:%M:%S')
    # console_handler.setFormatter(formatter)
    # console_handler.auto_flush = True
    file_handler.setFormatter(formatter)
    file_handler.auto_flush = True
    # auto_logger.addHandler(console_handler)
    auto_logger.addHandler(file_handler)

    return auto_logger


if __name__ == "__main__":
    main()
