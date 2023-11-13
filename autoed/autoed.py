#!/usr/bin/env python3
import sys
import os
import argparse
import daemon
from pathlib import Path
import signal
import time
import subprocess
import psutil
import argcomplete


# PYTHON_ARGCOMPLETE_OK
def main():

    msg = 'Daemon script for automatic processing of ED data'
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument('command',
                        choices=['start', 'watch', 'list', 'stop',
                                 'kill'],
                        help='Commands to execute')
    parser.add_argument('dirname', nargs='?', default=None,
                        help='Name of the directory to watch')
    parser.add_argument('--pid', nargs='?', type=int,
                        default=None,
                        help='PID of the process to kill')

    argcomplete.autocomplete(parser)

    args = parser.parse_args()

    autoed_daemon = AutoedDaemon()

    def signal_handler(signum, frame):
        print('Entering singnal handler')
        autoed_daemon.stop()
        autoed_daemon.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.command == "start":
        autoed_daemon.start()
    elif args.command == "watch" and args.dirname:
        autoed_daemon.watch(args.dirname)
    elif args.command == "list":
        autoed_daemon.list_directories()
    elif args.command == "stop":
        autoed_daemon.stop()
    elif args.command == "kill" and args.pid is not None:
        if not os.path.exists(autoed_daemon.lock_file):
            print("No daemon running")
            sys.exit(0)
        if args.pid in autoed_daemon.pids.values():
            kill_process_and_children(args.pid)
        else:
            print('The provided PID is not being watched.')
    elif args.command == "kill" and args.dirname is not None:
        if not os.path.exists(autoed_daemon.lock_file):
            print("No daemon running")
            sys.exit(0)
        if int(args.dirname) in autoed_daemon.pids.values():
            kill_process_and_children(int(args.dirname))
        else:
            print('The provided PID is not being watched.')
    else:
        parser.print_help()
        sys.exit(1)


class AutoedDaemon:

    def __init__(self):
        self.directories = []   # Directories to watch
        self._running = True
        self.lock_file = str(Path.home() / '.autoed.lock')
        self.pid_file = str(Path.home() / '.autoed.pid')
        self.dirs_file = str(Path.home() / '.autoed_dirs.txt')
        self.pids = {}
        self.pids, self.directories = self.load_directories()

    def load_directories(self):
        pids = {}
        dirs = []
        if os.path.exists(self.dirs_file):
            with open(self.dirs_file, 'r') as f:
                for line in f.readlines():
                    pid, dirname = line.strip().split()
                    pid = int(pid)
                    if psutil.pid_exists(pid):
                        pids[dirname] = pid
                        dirs.append(dirname)
                return pids, dirs
        return pids, dirs

    def save_dirs(self):
        with open(self.dirs_file, 'w') as f:
            for dirname in self.directories:
                f.write(str(self.pids[dirname]) +
                        ' ' + dirname + '\n')

    def start(self):

        if os.path.exists(self.lock_file):
            print("Daemon is already running.")
            sys.exit(1)

        with open(self.lock_file, 'w') as f:
            print('Starting autoed daemon')
            f.write("")

        with daemon.DaemonContext():
            with open(self.pid_file, 'w') as pf:
                pf.write(str(os.getpid()))

            try:
                while self._running:
                    time.sleep(1)
            finally:
                self.cleanup()

    def stop(self):
        self._running = False

        # Kill running processes
        for indir in self.directories:
            pid = self.pids[indir]
            kill_process_and_children(pid)

        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)
        if os.path.exists(self.dirs_file):
            os.remove(self.dirs_file)

        if os.path.exists(self.pid_file):
            with open(self.pid_file, 'r') as pf:
                pid = int(pf.read().strip())
                print('Stopping autoed daemon')
                os.kill(pid, signal.SIGTERM)
            os.remove(self.pid_file)

    def cleanup(self):
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)
        if os.path.exists(self.dirs_file):
            os.remove(self.dirs_file)

        if os.path.exists(self.pid_file):
            with open(self.pid_file, 'r') as pf:
                pid = int(pf.read().strip())
                os.kill(pid, signal.SIGTERM)
            os.remove(self.pid_file)

    def is_process_running(self, command):
        for p in psutil.process_iter(['cmdline']):
            if p.info['cmdline'] == [command]:
                return True
        return False

    def is_subdirectory(self, path_to_check):

        is_sub = False
        p2 = os.path.abspath(path_to_check)
        for p1 in self.directories:

            is_sub = is_sub or p2.startswith(p1 + os.sep)
        return is_sub

    def is_parent_directory(self, path_to_check):

        is_parent = False
        p2 = os.path.abspath(path_to_check)
        for p1 in self.directories:

            is_parent = is_parent or p1.startswith(p2 + os.sep)
        return is_parent

    def watch(self, dirname):

        if not os.path.exists(self.lock_file):
            print("No daemon running")
            sys.exit(0)

        full_path = os.path.abspath(dirname)

        if not os.path.exists(full_path):
            print(f'No path found: {full_path}')
            sys.exit(0)
        if full_path in self.directories:
            print(r'Directory {dirname} already watched.')
            sys.exit(1)
        elif self.is_subdirectory(full_path):
            print(f'Can not watch {dirname}.')
            print(r'Already watching its parent directory.')
            sys.exit(1)
        elif self.is_parent_directory(full_path):
            print(f'Can not watch {dirname}.')
            print(r'Already watching its subdirectories.')
            sys.exit(1)
        else:
            command = 'autoed_watch ' + full_path
            if not self.is_process_running(command):
                print('Watching path:', full_path)
                process = subprocess.Popen(command, shell=True)
                pid = str(process.pid)
                self.pids[full_path] = pid
                self.directories.append(full_path)
                self.save_dirs()

    def list_directories(self):

        if not os.path.exists(self.lock_file):
            print("No daemon running")
            sys.exit(0)
        print('Listing watched directories')
        print("PID    PATH")
        print("------------------------------------------")
        for idx, dirname in enumerate(self.directories):
            print(f"{self.pids[dirname]}  {dirname}")
        print("------------------------------------------")
        print('')
        msg = ("* Please use 'autoed kill PID' to kill a process.\n")
        msg += "  Alternatively you can use 'pkill -P PID'."
        print(msg)


def kill_process_and_children(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.terminate()
        psutil.wait_procs(children, timeout=5)
        parent.terminate()
        parent.wait(5)
    except psutil.NoSuchProcess:
        pass
    except psutil.TimeoutExpired:
        pass




if __name__ == '__main__':
    main()
