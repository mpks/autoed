import time
import autoed
import os
import re
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from autoed.dataset import SinglaDataset
from autoed.process.process_static import gather_master_files
import logging
import argparse

"""
A watchdog script that watches a directory for file changes.
The script checks, converts and processes the electron diffraction
data if present.

Run with:
autoed_watch directory_name
optionaly
autoed_watch -i -s 30 directory_name
"""


def main():

    msg = 'Watchdog script for monitoring filesystem changes'
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument('--inotify', '-i', action='store_true',
                        default=False,
                        help='Run watchdog with inotify.')
    hmsg = "Sleep duration between filesystem checks.\n"
    hmsg += "By default 1 sec for inotify method, "
    hmsg += "or 30 sec for pooling method."
    parser.add_argument('--sleep_time', '-s', type=float,
                        default=None, help=hmsg)

    msg = 'Run watchdog without running xia2 or dials (for testing)'
    parser.add_argument('--dummy', action='store_true', default=False,
                        help=msg)

    msg = 'If used, it runs xia2 and DIALS processing locally with bash, '
    msg += 'instead of submitting the job request to cluster using SLURM.'
    parser.add_argument('--local', action='store_true', default=False,
                        help=msg)
    parser.add_argument('--log-dir', type=str, default=None,
                        help='A directory to store autoed log file.')
    parser.add_argument('dirname', nargs='?', default=None,
                        help='Name of the directory to watch')

    args = parser.parse_args()

    if args.inotify:
        sleep_time = 1.0  # Default for inotify method
    else:
        sleep_time = 30.0  # Default for polling method

    if args.sleep_time:    # Overwrite the default
        sleep_time = args.sleep_time

    if not args.dirname:
        msg = 'autoed_watch requires a single argument'
        msg += ' (watch directory)'
        raise IOError(msg)

    input_dir = args.dirname

    watch_path = os.path.abspath(input_dir)
    if not os.path.exists(watch_path):
        msg = f'Path {watch_path} does not exist.'
        raise FileNotFoundError(msg)

    if args.log_dir:
        if not os.path.exists(args.log_dir):
            msg = f'Path {args.log_dir} does not exist.'
            raise FileNotFoundError(msg)

        log_directory = args.log_dir
    else:
        log_directory = watch_path

    processing_script = os.path.join(autoed.__path__[0], 'process.py')

    watch_logger = set_watch_logger(log_directory,
                                    args.inotify,
                                    sleep_time)

    event_handler = DirectoryHandler(watch_path,
                                     processing_script,
                                     watch_logger,
                                     report_dir=log_directory,
                                     dummy=args.dummy,
                                     local=args.local)

    if args.inotify:
        observer = Observer()
    else:
        observer = PollingObserver(timeout=sleep_time)

    observer.schedule(event_handler, watch_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(sleep_time)

    except KeyboardInterrupt as e:
        watch_logger.exception(str(e))
        observer.stop()
    except Exception as e:
        watch_logger.exception(str(e))
        observer.stop()
    observer.join()


class DirectoryHandler(FileSystemEventHandler):

    def __init__(self, watch_path, script, logger, report_dir,
                 dummy=False, local=False):

        """
        Parameters
        ----------
        watch_path : Path
            The path of the directory to be watched.

        script : Path
            The path to the processing script used to
            convert and process data.
        logger : logger object
        report_dir : Path
            The path where to save the report HTML file.
        dummy: boolean
            If True, the AutoED will not run xia2 or dials. This is used
            for testing.
        local: boolean
            If True, the AutoED will run xia2 and DIALS on the local machine
            using bash, instead of submitting a SLURM request to the cluster.
        """

        self.watch_path = watch_path
        self.status_file = os.path.join(watch_path, '.autoed_status.txt')
        self.dataset_names = set()
        self.datasets = dict()
        self.queue = dict()
        self.logger = logger
        self.dummy = dummy
        self.local = local

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
                                dataset.dummy = self.dummy
                                self.datasets[dataset.base] = dataset
                            else:
                                dataset = self.datasets[basename]

                            dataset.update_processed()
                            msg = 'Found dataset: %s'
                            info(msg % dataset.base)

                            if not dataset.processed:
                                if dataset.all_files_present():
                                    msg = 'All files present: %s'
                                    info(msg % dataset.base)
                                    info('Processing: %s' % dataset.base)
                                    success = dataset.process(self.local)
                                    base = dataset.base
                                    if success:
                                        ms = f"Processed: {base}"
                                        info(ms)
                                    else:
                                        ms = f"Failed to process: {base}"
                                        info(ms)
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


def set_watch_logger(watch_path, inotify, sleep):

    auto_logger = logging.getLogger(__name__)
    auto_logger.setLevel(logging.DEBUG)

    autoed_log_path = os.path.join(watch_path, 'autoed_watch.log')
    file_handler = logging.FileHandler(autoed_log_path, mode='a')
    file_handler.setLevel(logging.DEBUG)
    fmt = '%(asctime)s.%(msecs)03d %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt, datefmt='%d-%m-%Y %H:%M:%S')

    file_handler.setFormatter(formatter)
    file_handler.auto_flush = True

    auto_logger.addHandler(file_handler)

    auto_logger.info(40*'=')
    auto_logger.info('  Starting new logger')
    auto_logger.info('  inotify: %s' % inotify)
    auto_logger.info('  sleep time: %.1f' % sleep)
    auto_logger.info(40*'=')

    return auto_logger


if __name__ == "__main__":
    main()
