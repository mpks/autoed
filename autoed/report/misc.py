from autoed.report.json_database import JsonDatabase
from autoed.report.parser import Xia2OutputParser
from autoed.constants import report_data_dir
import os
import shutil
import autoed


def generate_report_files(report_path, verbose=True):

    os.makedirs(report_path, exist_ok=True)
    if verbose:
        print("Generating report in")
        print(f" {report_path} ")

    data_path = os.path.join(report_path, report_data_dir)
    os.makedirs(data_path, exist_ok=True)

    autoed_path = autoed.__path__[0]
    template_path = os.path.join(autoed_path, 'report/template')
    template_files = ['report.html', 'scripts.js', 'styles.css',
                      'server', 'favicon.png']

    for file in template_files:
        source_path = os.path.join(template_path, file)

        if file == 'report.html' or file == 'server':
            destination_path = os.path.join(report_path, file)
        else:
            destination_path = os.path.join(data_path, file)

        shutil.copy(source_path, destination_path)

        if file == 'server':
            os.chmod(destination_path,
                     os.stat(destination_path).st_mode | 0o111)


def update_database_for_dataset(dataset, report_path):
    """ Add dataset to database """

    database = JsonDatabase(report_path)
    database.load_data()

    parser = Xia2OutputParser(dataset, database)
    parser.add_to_database()
