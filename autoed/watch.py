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
from .process_static import gather_master_files
import logging

"""
A watchdog script that watches a directory for file changes.
The script checks, converts and processes the electron diffraction
data if present.

Run with:
autoed_watch directory_name
"""

# Sometimes the same file will trigger the watchdog
# Here, we have a wait time of 5 seconds between two
# triggers to be detected.
TRIGGER_TIME_SEC = 5


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
        logger : logger object
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

        try:
            info = self.logger.info

            if not event.is_directory:

                if re.match(r".*\.HiMarko$", event.src_path):

                    info('Detected trigger file: %s' % event.src_path)

                    dataset = None
                    basename = None

                    # Process only events that happened in ED directory
                    if 'ED' in event.src_path.split(os.path.sep):

                        dir_name = os.path.dirname(event.src_path)

                        master_files = gather_master_files(dir_name)

                        for master_file in master_files:
                            basename = master_file[:-10]

                            if (basename not in self.dataset_names):
                                self.dataset_names.add(basename)
                                dataset = SinglaDataset.from_basename(basename)
                                dataset.search_and_update_data_files()
                                self.datasets[dataset.base] = dataset
                            else:
                                dataset = self.datasets[basename]

                            dataset.update_processed()
                            msg = 'Found dataset: %s'
                            info(msg % dataset.base)

                            if not dataset.processed:
                                msg = 'Checking if all files present: %s'
                                info(msg % dataset.base)
                                if dataset.all_files_present():
                                    info('Processing: %s' % dataset.base)
                                    dataset.process()
                                    info('Finished processing: %s'
                                         % dataset.base)
                                else:
                                    msg = 'Not all files present, ignoring: %s'
                                    info(msg % dataset.base)
                            else:
                                msg = 'Ignoring trigger. '
                                msg += 'Data processed recently: %s %s '
                                t1 = dataset.last_processed_time
                                st = time.strftime('%Y-%m-%d %H:%M:%S',
                                                   time.localtime(t1))
                                info(msg % (st, dataset.base))
                    else:
                        msg = 'Ignoring trigger, no ED directory: %s'
                        self.logger.info(msg % event.src_path)
        except Exception as e:
            self.logger.exception(str(e))

    def on_modified(self, event):
        self.on_created(event)


def set_watch_logger(watch_path):

    auto_logger = logging.getLogger(__name__)
    auto_logger.setLevel(logging.DEBUG)
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.DEBUG)

    autoed_log_path = os.path.join(watch_path, 'autoed_watch.log')
    file_handler = logging.FileHandler(autoed_log_path, mode='a')
    file_handler.setLevel(logging.DEBUG)
    fmt = '%(asctime)s.%(msecs)03d %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt, datefmt='%d-%m-%Y %H:%M:%S')
    # console_handler.setFormatter(formatter)
    # console_handler.auto_flush = True
    file_handler.setFormatter(formatter)
    file_handler.auto_flush = True
    # auto_logger.addHandler(console_handler)
    auto_logger.addHandler(file_handler)

    auto_logger.info(40*'=')
    auto_logger.info('  Starting new logger')
    auto_logger.info(40*'=')

    return auto_logger


if __name__ == "__main__":
    main()
