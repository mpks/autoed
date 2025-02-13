"""Keeps some useful functions that operate on the filesystem"""
import os
import fnmatch


def find_files_in_directory(directory, pattern):
    """Returns a list of all files in a directory matching a pattern"""
    files = [f for f in os.listdir(directory) if fnmatch.fnmatch(f, pattern)]
    return files


def gather_master_files(directory):
    """
    Given a directory path return all the paths of all files ending with
    '_master.h5'
    """

    master_files = []

    if not os.path.exists(directory):
        return []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path.endswith('_master.h5'):
                master_files.append(file_path)

    return master_files
