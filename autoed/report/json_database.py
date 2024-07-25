import os
from autoed.constants import database_json_file, xia2_report_dir
from autoed.constants import beam_report_dir
import json
import shutil
import hashlib


def overwrite_xia2_report(xia2_report_file, added_line):
    """ This function will just add a line with the dataset
        name to xia2 report
    """
    with open(xia2_report_file, 'r') as file:
        lines = file.readlines()

    with open(xia2_report_file, 'w') as file:
        for line in lines:
            file.write(line)
            if '<h1>xia2 processing report' in line:
                file.write(f"<p>{added_line}</p>\n")


class JsonDatabase:

    def __init__(self, full_path_to_database_dir):
        """
        Creates a json database file if it does not exists already

        full_path_to_database_file : path of string
            The json database is generated in the autoed report directory,
            along with the html report with processing statistics.
        """

        self.json_file = os.path.join(full_path_to_database_dir,
                                      database_json_file)
        self.xia2_report_dir = os.path.join(full_path_to_database_dir,
                                            xia2_report_dir)
        self.beam_report_dir = os.path.join(full_path_to_database_dir,
                                            beam_report_dir)
        os.makedirs(self.xia2_report_dir, exist_ok=True)
        os.makedirs(self.beam_report_dir, exist_ok=True)

        self.data = {}

        if not os.path.exists(self.json_file):
            with open(self.json_file, 'w') as file:
                json.dump({}, file)

    def load_data(self):
        with open(self.json_file, 'r') as file:
            self.data = json.load(file)

    def add_entry(self, dataset_name, value, beam_image=None):
        """
        Add column data (value) for a dataset in the database

        dataset_name : string or path
        value : dict
            Can contain any keys, as long there is a key 'title',
            this key determines what is written at the top of the
            table column.
        beam_image : string or path
            The location of the beam position image for that dataset
        """

        # Copy the xia2 report if it exists
        # and also overwrite the destination of the copied file
        if value['link']:
            md5 = hashlib.md5()
            md5.update(value['link'].encode('utf-8'))
            link_hash = md5.hexdigest()[0:10] + '.html'
            destination = os.path.join(self.xia2_report_dir, link_hash)
            if os.path.exists(value['link']):
                shutil.copy(value['link'], destination)
                # Write the dataset name in the xia2 report
                overwrite_xia2_report(destination, value['link'])
                value['link'] = os.path.join(xia2_report_dir, link_hash)
            else:
                value['link'] = None

        if dataset_name in self.data:         # Overwrite existing data
            self.data[dataset_name][value['title']] = value

        else:
            self.data[dataset_name] = {}
            self.data[dataset_name][value['title']] = value

        # Copy the beam image if it exists
        if beam_image:
            if os.path.exists(beam_image):

                beam_for_report = beam_image.replace('/', '_')
                md5 = hashlib.md5()
                md5.update(beam_for_report.encode('utf-8'))
                beam_file_hash = md5.hexdigest()[0:10] + '.png'

                dest = os.path.join(self.beam_report_dir, beam_file_hash)
                link = os.path.join(beam_report_dir, beam_file_hash)

                shutil.copy(beam_image, dest)

                self.data[dataset_name]['beam_image'] = link
            else:
                self.data[dataset_name]['beam_image'] = None
        else:
          self.data[dataset_name]['beam_image'] = None

    def save_data(self):
        with open(self.json_file, 'w') as file:
            json.dump(self.data, file, indent=4)
