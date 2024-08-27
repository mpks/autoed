import os
import sys
from autoed.constants import report_dir
import autoed
import shutil
from autoed.utility.filesytem import gather_datasets
from autoed.report.json_database import JsonDatabase
from autoed.report.parser import Xia2OutputParser
import argparse


def run():
    """Generates the HTML report"""
    msg = 'Generates an HTML report for the given directory'
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument('watch_dir', type=str,
                        help='A directory from where to scrap the data.')
    parser.add_argument('report_path', type=str,
                        help='A path where to save the report.')
    args = parser.parse_args()

    watch_dir = os.path.abspath(args.watch_dir)
    report_path = os.path.abspath(args.report_path)
    report_full_path = os.path.join(report_path, report_dir)

    if not os.path.exists(watch_dir):
        print("Error: FileNotFound {watch_dir}.")
        print(" Can not generate HTML report.")
        print(" The directory from which to scrap the data does not exist")
        sys.exit()

    generate_report_files(report_full_path)
    generate_json_database(watch_dir, report_full_path)


def generate_report_files(report_path):

    os.makedirs(report_path, exist_ok=True)
    print("Generating HTML report in")
    print(f" {report_path} ")

    autoed_path = autoed.__path__[0]
    template_path = os.path.join(autoed_path, 'report/template')
    template_files = ['report.html', 'scripts.js', 'styles.css', 'favicon.png']

    for file in template_files:
        source_path = os.path.join(template_path, file)
        destination_path = os.path.join(report_path, file)
        shutil.copy(source_path, destination_path)


def generate_json_database(path_to_watched_dir, report_path):
    """
    Goes through the watched directory recursively gathering all the datasets
    and then parses them into a single json file
    """

    datasets = gather_datasets(path_to_watched_dir)
    database = JsonDatabase(report_path)

    database.load_data()

    for dataset in datasets:
        parser = Xia2OutputParser(dataset, database)
        parser.add_to_database()
